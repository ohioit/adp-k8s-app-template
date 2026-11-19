"""Compare every scenario's generated project to its committed fixture.

A fixture is the full expected output tree, stored as
test/fixtures/<scenario>/<project slug>/... so a change to the slug is caught too.
"""

import difflib
import shutil
from pathlib import Path

import pytest

from conftest import FIXTURES_DIR
from scenarios import SCENARIOS


def read_tree(root):
    """Map each file's path relative to root to its text content."""
    return {
        path.relative_to(root).as_posix(): path.read_text()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def write_fixture(fixture_dir, project_path):
    if fixture_dir.exists():
        shutil.rmtree(fixture_dir)
    shutil.copytree(project_path, fixture_dir / project_path.name)


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_matches_fixture(scenario, baked_scenario, request):
    project_path = baked_scenario(scenario)
    fixture_dir = FIXTURES_DIR / scenario

    if not fixture_dir.exists():
        if request.config.getoption("--generate-fixtures"):
            write_fixture(fixture_dir, project_path)
            return
        pytest.fail(
            f"No fixture for scenario {scenario!r}. Run `pytest --generate-fixtures` "
            f"and review the new files in {fixture_dir}."
        )

    expected = read_tree(fixture_dir)
    actual = read_tree(project_path.parent)
    actual = {name: text for name, text in actual.items() if name.startswith(project_path.name + "/")}

    problems = []
    for name in sorted(expected.keys() - actual.keys()):
        problems.append(f"missing from generated output: {name}")
    for name in sorted(actual.keys() - expected.keys()):
        problems.append(f"not in fixture: {name}")
    for name in sorted(expected.keys() & actual.keys()):
        if expected[name] != actual[name]:
            diff = difflib.unified_diff(
                expected[name].splitlines(keepends=True),
                actual[name].splitlines(keepends=True),
                fromfile=f"fixture/{name}",
                tofile=f"generated/{name}",
            )
            problems.append("".join(diff))

    if problems:
        if request.config.getoption("--overwrite-fixtures"):
            write_fixture(fixture_dir, project_path)
            return
        pytest.fail(
            f"Generated output for scenario {scenario!r} doesn't match its fixture.\n"
            "If the change is intended, run `pytest --overwrite-fixtures` and commit the fixture diff.\n\n"
            + "\n".join(problems),
            pytrace=False,
        )


def test_no_orphaned_fixtures():
    """Every fixture directory must belong to a scenario in scenarios.py."""
    if not FIXTURES_DIR.exists():
        return
    orphans = sorted(p.name for p in FIXTURES_DIR.iterdir() if p.is_dir() and p.name not in SCENARIOS)
    assert not orphans, f"fixtures without a scenario in scenarios.py (delete them): {orphans}"
