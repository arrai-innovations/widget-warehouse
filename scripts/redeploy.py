#!/usr/bin/env python3
"""Trigger a production redeploy of an existing tag through the CircleCI API.

A tag pipeline tests, builds, releases, and deploys in one pass, so a deploy step
that fails on its own leaves the tag tested, released, and undeployed. Cutting a
new tag to retry records a version that carries no change, and rerunning the tag's
pipeline reruns the config stored at that tag, which for a broken deploy step is
the config that failed.

This posts to the CircleCI v2 pipeline endpoint from main with `redeploy-server`
or `redeploy-client` set and the tag to send as `redeploy-tag`. The setup config
routes that to a deploy-only workflow in .circleci/server.yml or
.circleci/client.yml: no tests, no build, no release, only the signed POST to the
deployer.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_SLUG = "gh/arrai-innovations/widget-warehouse"
PIPELINE_ENDPOINT = f"https://circleci.com/api/v2/project/{PROJECT_SLUG}/pipeline"
PIPELINE_VIEW = "https://app.circleci.com/pipelines/github/arrai-innovations/widget-warehouse"

DEFAULT_BRANCH = "main"

# The client deployer fetches this asset from the tag's GitHub release, so a client
# redeploy of a tag whose release lacks it would deploy nothing.
RELEASE_ASSET = "dist.zip"

# Tag prefix to the pipeline parameter that selects that half's redeploy workflow.
TARGETS = {
    "server-v": "redeploy-server",
    "client-v": "redeploy-client",
}

CLI_CONFIG = Path.home() / ".circleci" / "cli.yml"
TOKEN_LINE = re.compile(r"^token:\s*(?:\"([^\"]*)\"|'([^']*)'|(\S+))\s*$", re.MULTILINE)


def read_token() -> str | None:
    """Return a CircleCI API token from the environment or the CircleCI CLI config."""
    for variable in ("CIRCLECI_TOKEN", "CIRCLECI_CLI_TOKEN"):
        token = os.environ.get(variable)
        if token:
            return token

    if not CLI_CONFIG.is_file():
        return None

    match = TOKEN_LINE.search(CLI_CONFIG.read_text(encoding="utf-8"))
    if match is None:
        return None
    return match.group(1) or match.group(2) or match.group(3)


def parameter_for_tag(tag: str) -> str | None:
    """Return the pipeline parameter that redeploys the half the tag names."""
    for prefix, parameter in TARGETS.items():
        if tag.startswith(prefix):
            return parameter
    return None


def run(command: list[str]) -> subprocess.CompletedProcess[str] | None:
    """Run a command, or return None when it is not installed."""
    try:
        return subprocess.run(command, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return None


def check_tag_exists(tag: str) -> str | None:
    """Return a message describing why the tag cannot be redeployed, or None."""
    result = run(["git", "ls-remote", "--tags", "origin", f"refs/tags/{tag}"])
    if result is None:
        return "git is not installed, so the tag could not be checked."
    if result.returncode != 0:
        return f"git could not reach origin: {result.stderr.strip()}"
    if not result.stdout.strip():
        return f"origin has no tag named '{tag}'."
    return None


def check_release_asset(tag: str) -> str | None:
    """Return a message describing why the tag's release cannot be deployed, or None."""
    result = run(["gh", "release", "view", tag, "--json", "assets", "--jq", ".assets[].name"])
    if result is None:
        return "gh is not installed, so the release assets could not be checked."
    if result.returncode != 0:
        return f"gh could not read the release for '{tag}': {result.stderr.strip()}"
    if RELEASE_ASSET not in result.stdout.split():
        return f"the release for '{tag}' has no {RELEASE_ASSET} asset."
    return None


def trigger_pipeline(branch: str, parameter: str, tag: str, token: str) -> dict:
    """Ask CircleCI to run a redeploy pipeline for the given tag."""
    request = urllib.request.Request(
        PIPELINE_ENDPOINT,
        method="POST",
        data=json.dumps({"branch": branch, "parameters": {parameter: True, "redeploy-tag": tag}}).encode("utf-8"),
        headers={
            "Accept": "application/json",
            "Circle-Token": token,
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Redeploy an existing tag to production through the CircleCI API.")
    parser.add_argument("tag", help="Tag to redeploy, such as server-v0.1.1 or client-v0.1.1.")
    parser.add_argument(
        "--branch",
        default=DEFAULT_BRANCH,
        help=f"Branch supplying the pipeline configuration. Defaults to {DEFAULT_BRANCH}.",
    )
    parser.add_argument(
        "--allow-branch",
        action="store_true",
        help=f"Confirm deploying with configuration from a branch other than {DEFAULT_BRANCH}.",
    )
    parser.add_argument(
        "--skip-checks",
        action="store_true",
        help="Trigger without confirming the tag is on origin and its release carries the client bundle.",
    )
    args = parser.parse_args()

    parameter = parameter_for_tag(args.tag)
    if parameter is None:
        prefixes = " or ".join(f"{prefix}*" for prefix in sorted(TARGETS))
        sys.stderr.write(f"'{args.tag}' names neither half. Redeploy a {prefixes} tag.\n")
        return 1

    if args.branch != DEFAULT_BRANCH and not args.allow_branch:
        sys.stderr.write(
            f"Refusing to deploy with configuration from '{args.branch}'.\n"
            f"This deploys to production, and this branch is not {DEFAULT_BRANCH}.\n"
            f"Confirm with:\n"
            f"  just redeploy {args.tag} --branch {args.branch} --allow-branch\n"
        )
        return 1

    if not args.skip_checks:
        problems = [check_tag_exists(args.tag)]
        if parameter == "redeploy-client":
            problems.append(check_release_asset(args.tag))
        problems = [problem for problem in problems if problem is not None]
        if problems:
            sys.stderr.write(f"Refusing to redeploy '{args.tag}'.\n")
            for problem in problems:
                sys.stderr.write(f"  {problem}\n")
            sys.stderr.write("Override with --skip-checks.\n")
            return 1

    token = read_token()
    if token is None:
        sys.stderr.write("No CircleCI API token found. Run `circleci setup`, or set CIRCLECI_TOKEN.\n")
        return 1

    try:
        result = trigger_pipeline(args.branch, parameter, args.tag, token)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace").strip()
        sys.stderr.write(f"CircleCI returned {error.code}: {detail}\n")
        return 1
    except urllib.error.URLError as error:
        sys.stderr.write(f"Could not reach CircleCI: {error.reason}\n")
        return 1

    number = result.get("number")
    print(f"Triggered a redeploy of '{args.tag}' as pipeline {number}.")
    print(f"{PIPELINE_VIEW}/{number}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
