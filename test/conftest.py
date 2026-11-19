"""Shared pytest configuration for the cookiecutter template tests.

See test/README.md for how to run the suite.
"""

import os
import shutil
import sys
from pathlib import Path

import pytest

from scenarios import SCENARIOS

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def pytest_addoption(parser):
    group = parser.getgroup("fixtures", "template fixture handling")
    group.addoption(
        "--generate-fixtures",
        action="store_true",
        default=False,
        help="Write fixtures for scenarios that don't have one yet.",
    )
    group.addoption(
        "--overwrite-fixtures",
        action="store_true",
        default=False,
        help="Overwrite fixtures that don't match the generated output. "
        "Review the resulting git diff before committing it.",
    )


@pytest.fixture(scope="session")
def bake(cookies_session):
    """Return a function that renders the template with extra_context.

    Results are cached per scenario name so each scenario is only rendered once
    per session, no matter how many tests use it.
    """
    cache = {}

    def _bake(context, name=None):
        if name is not None and name in cache:
            return cache[name]
        result = cookies_session.bake(extra_context=dict(context), template=str(REPO_ROOT))
        if name is not None:
            cache[name] = result
        return result

    return _bake


@pytest.fixture(scope="session")
def baked_scenario(bake):
    """Return a function that renders a named scenario and asserts it succeeded."""

    def _baked(name):
        result = bake(SCENARIOS[name], name=name)
        assert result.exception is None, f"scenario {name!r} failed to generate: {result.exception}"
        assert result.exit_code == 0
        return Path(result.project_path)

    return _baked


def require_tool(name):
    """Return the path to an external tool, or skip the test if it isn't installed.

    Set REQUIRE_TOOLS=1 (as CI does) to fail instead of skipping, so a missing
    tool can't silently disable tests.
    """
    # Also look next to the running Python, so tools installed by pip into a
    # virtualenv (like actionlint-py) are found without activating it.
    path = shutil.which(name) or shutil.which(name, path=os.path.dirname(sys.executable))
    if path is None:
        message = f"{name} is not installed or not on PATH"
        if os.environ.get("REQUIRE_TOOLS") == "1":
            pytest.fail(f"{message} (REQUIRE_TOOLS=1)")
        pytest.skip(message)
    return path
