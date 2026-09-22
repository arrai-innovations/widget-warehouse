import { beforeEach, describe, expect, it, vi } from "vitest";
import { createSSRApp, h } from "vue";
import { renderToString } from "vue/server-renderer";

import DefaultViewList from "@/views/DefaultViewList.vue";

const mocks = vi.hoisted(() => ({ actions: [], rows: [], listProps: null }));
vi.mock("@vueda/use/useModelConfig.js", () => ({
    useModelConfig: () => ({ config: { displayFields: ["reference"], fetchFields: ["reference"] } }),
}));
vi.mock("@vueda/use/useFilteredActions.js", () => ({ useFilteredActions: () => mocks }));
vi.mock("@vueda/navigation/link-model-view/LinkModelView.vue", async () => {
    const { h } = await import("vue");
    return {
        default: {
            props: ["pk", "view", "label"],
            setup: (props) => () => h("a", { "data-target": `${props.pk}:${props.view}` }, props.label),
        },
    };
});
vi.mock("@vueda/views/ViewList.vue", async () => {
    const { h } = await import("vue");
    return {
        default: {
            props: ["displayFields", "listFields"],
            setup(props, { slots }) {
                mocks.listProps = props;
                return () =>
                    h(
                        "div",
                        mocks.rows.map((obj) =>
                            h(
                                "div",
                                Object.keys(props.displayFields).map((field) =>
                                    slots[`field(${field})`]?.({
                                        pk: obj.id,
                                        obj,
                                    }),
                                ),
                            ),
                        ),
                    );
            },
        },
    };
});

const render = (props = {}) =>
    renderToString(
        createSSRApp({ render: () => h(DefaultViewList, { app: "catalog", model: "purchaseorder", ...props }) }),
    );

describe("DefaultViewList", () => {
    beforeEach(() => {
        mocks.actions = ["list", "retrieve", "update"];
        mocks.rows = [];
        mocks.listProps = null;
    });

    it("links editable rows to update, readable rows to read, and neither when unavailable", async () => {
        mocks.rows = [
            { id: 1, available_actions: ["update", "retrieve"] },
            { id: 2, available_actions: ["retrieve"] },
            { id: 3, available_actions: [] },
            { id: 4 },
        ];
        const html = await render();
        expect(html).toContain('data-target="1:update"');
        expect(html).toContain('data-target="2:read"');
        expect(html.match(/data-target=/g)).toHaveLength(2);
        expect(mocks.listProps.listFields).toEqual(["reference", "available_actions"]);
        expect(mocks.listProps.displayFields.update.label).toBe("Actions");
    });

    it("shows the column for read-only users and respects model action filtering", async () => {
        mocks.actions = ["list", "retrieve"];
        mocks.rows = [{ id: 1, available_actions: ["update", "retrieve"] }];
        const html = await render();
        expect(html).toContain('data-target="1:read"');
        expect(html).not.toContain('data-target="1:update"');
    });

    it("omits the automatic column for list-only users", async () => {
        mocks.actions = ["list"];
        await render();
        expect(mocks.listProps.displayFields).not.toHaveProperty("update");
    });

    it("preserves explicit fetch fields and requests available_actions only once", async () => {
        await render({ listFields: ["id", "workflow_state_name", "available_actions"] });
        expect(mocks.listProps.listFields).toEqual(["id", "workflow_state_name", "available_actions"]);
    });
});
