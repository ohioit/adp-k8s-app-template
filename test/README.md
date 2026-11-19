# Template Tests

A [pytest](https://docs.pytest.org/) suite that renders the cookiecutter template
with a set of answers ("scenarios") and checks the generated projects. It needs no
Kubernetes cluster and no access to Artifactory, and it runs on every push via
[`.github/workflows/test.yaml`](../.github/workflows/test.yaml).

## Running the tests

### In the devcontainer

Everything is preinstalled: cookiecutter, pytest, actionlint and skaffold. From the
repository root, run:

```bash
pytest
```

### Anywhere else

You need Python 3.14 or newer. [skaffold](https://skaffold.dev/docs/install/) is
optional: without it, the skaffold tests are skipped. Install the Python
dependencies into a virtualenv once:

```bash
python3 -m venv .venv
.venv/bin/pip install -r test/requirements.txt
```

Then, from the repository root:

```bash
.venv/bin/pytest            # or `source .venv/bin/activate` and run `pytest`
```

### Useful options

| Command | What it does |
| --- | --- |
| `pytest -k generic-bare` | Run only the tests for one scenario, or any name match |
| `pytest test/test_options.py` | Run one test file |
| `pytest --generate-fixtures` | Write fixtures for scenarios that don't have one yet |
| `pytest --overwrite-fixtures` | Rewrite fixtures that don't match the generated output |
| `REQUIRE_TOOLS=1 pytest` | Fail instead of skip when `skaffold` or `actionlint` is missing (CI does this) |

## What is tested

| File | Checks |
| --- | --- |
| [`test_fixtures.py`](test_fixtures.py) | Each scenario's generated project matches its fixture exactly: same files, same content, and the same project directory name |
| [`test_options.py`](test_options.py) | Individual options and hooks: the project type suffix, which files are removed or added, upstream fields required in 3rd-party mode, environments (which workflows exist, clusters, namespaces, ArgoCD settings, and validation errors for bad answers) |
| [`test_files.py`](test_files.py) | Generated files are well-formed: YAML and JSON parse, `helm/Chart.yaml` metadata and dependencies, `actionlint` on the generated workflows (and on this repo's own CI workflow), and `skaffold diagnose --yaml-only -p <env>` for every profile |

The Helm chart itself is **not** rendered:

- the `common` library chart lives in the on-prem Artifactory and is tested in
  `ais-helm-commons`;
- upstream charts are tested by their own projects.

## Fixtures

`fixtures/<scenario>/<project slug>/` holds the exact expected output for each
scenario in [`scenarios.py`](scenarios.py), like the fixtures in `ais-helm-commons`.
A failing fixture test prints a unified diff between the fixture and the generated
output.

When the output changes on purpose:

1. Run `pytest --overwrite-fixtures`.
2. Review the changes with `git diff test/fixtures`. Make sure every difference,
   including blank lines, is one you meant.
3. Commit the fixture changes with the template change.

Don't overwrite fixtures to make a failure you don't understand go away.

### Adding a scenario

1. Add an entry to `SCENARIOS` in `scenarios.py`. Build it from `THIRD_PARTY` or
   `GENERIC` so the required answers are already filled in. If its environments differ
   from the default (`dev` on `k8s-sand`, `prod` on `k8s-prod`), add its expected
   `(name, kind, cluster, namespace)` list to `ENVIRONMENTS`.
2. Run `pytest --generate-fixtures`.
3. Review the new `fixtures/<scenario>/` directory and commit it.

Fixtures for scenarios that no longer exist make `test_no_orphaned_fixtures` fail.
Delete those directories.

## Known bugs

There are none right now. Known bugs in the template are tests marked
`@pytest.mark.xfail(strict=True, reason=...)`. They are reported as `XFAIL` and
don't fail the run. Once a bug is fixed, its test "unexpectedly passes" (`XPASS`),
which **does** fail the run. That's your reminder to remove the marker, so the test
becomes a regression test.

Bugs that make actionlint fail for a scenario are listed in
`KNOWN_ACTIONLINT_FAILURES` in `scenarios.py`.

## Requirements

[`requirements.txt`](requirements.txt) pins every dependency. `cookiecutter` in
particular is pinned exactly, because whitespace in the generated output, and so
the fixtures, can change between versions. When you upgrade it, run
`pytest --overwrite-fixtures` and review the diff.

The skaffold version used in CI is set in `.github/workflows/test.yaml`. Keep it in
line with the version in `ghcr.io/ohioit/vscode-devcontainer-base`.
