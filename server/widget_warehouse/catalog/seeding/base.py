"""The shape every step of ``seed_demo`` shares."""

from io import StringIO

from django.core.management.base import OutputWrapper
from django.core.management.color import no_style


class SeedStep:
    """
    One step of the demo seed.

    A step writes through ``stdout`` and ``style`` the way a management command does, so
    ``seed_demo`` hands it its own and the step's progress lands in the command's output.
    Called without them, as tests do, a step writes nowhere.
    """

    def __init__(self, stdout=None, style=None):
        self.stdout = stdout or OutputWrapper(StringIO())
        self.style = style or no_style()

    def run(self):
        raise NotImplementedError
