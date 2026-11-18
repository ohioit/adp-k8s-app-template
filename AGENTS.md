# Agent Instructions

## What this repo is

A [cookiecutter](https://cookiecutter.readthedocs.io/) template. It generates a new Ohio
application repo: a Helm chart (optionally using the `common` library chart from
`ais-helm-commons`), skaffold profiles, and GitHub Actions that deploy through ArgoCD.

`project_type` (`app`, `ui`, `api` or `integration`) currently only sets the suffix, through the
computed `__project_suffix` used in `project_slug` and `container_image`. The suffix is
`-<type>`, with `-3rdparty` added before it in 3rd-party mode (e.g. `-3rdparty-app`). To make a
type affect generated files later, test `cookiecutter.project_type` in the templates or hooks.

The `deploy_3rdparty_chart` question picks between two modes:

- **true (the default):** a "3rd party app". The chart wraps an upstream chart as a dependency and
  adds Ohio config on top. The slug ends in `-3rdparty-<type>` and the version is
  `<upstream>-OHIO-<n>`. `hooks/pre_gen_project.py` requires `upstream_project_name`,
  `upstream_project_helm_repo` and `upstream_project_version`.
- **false:** a generic app. There's no upstream dependency, the slug ends in `-<type>`, the version
  is plain semver (`chart_version`, default `0.1.0`), and the upstream answers are ignored.

Docs and comments in the generated project should read as generic. Put 3rd-party wording inside
`{% if cookiecutter.deploy_3rdparty_chart %}` blocks.

The repo is not a project itself. Nothing at the top level gets deployed. Real repos generated from
it, such as `adp-cert-manager-3rdparty-app`, `ais-minio-3rdparty-app` and `erp-ords-3rdparty-app`,
sit next to it under `~/Documents/OHIO/Code` and show what the output looks like after people have
worked on it.

This is a sanitized copy. Hostnames are placeholders (`registry.example.com`,
`docker.registry.example.com`, `*.k8s.example.com`). Leave them as placeholders unless asked to
change them.

## Layout

| Path | Purpose |
| --- | --- |
| `cookiecutter.json` | Prompts, defaults and private lookup tables (`_k8s_cluster_details`, `_k8s_environment_spec`) |
| `hooks/pre_gen_project.py` | Fails generation if 3rd-party mode is on but the upstream fields are empty |
| `local_extensions.py` | Jinja filters `k8s_environments` and `k8s_environment_errors`: all environment/cluster/namespace logic (loaded via `_extensions`) |
| `hooks/post_gen_project.py` | Deletes optional files and expands `helm/values/environment.yaml` into one `helm/values/<env>.yaml` per environment |
| `{{cookiecutter.project_slug}}/` | The generated project, all Jinja-rendered |
| `.devcontainer/` | Devcontainer for working on the template: base image (which has skaffold) plus a uv-built Python 3.14 virtualenv with `test/requirements.txt` |
| `test/` | pytest suite, scenarios and fixtures (see `test/README.md`) |
| `.github/workflows/test.yaml` | CI that runs the suite on every push |

Generated project (`{{cookiecutter.project_slug}}/`):

- `helm/Chart.yaml`: in 3rd-party mode, the upstream chart as a dependency (`~<version>`). Also
  `common` from the Artifactory helm repo when `ohio_helm_common_version` is set. If neither
  applies, `dependencies:` is left as a commented example. The version comes from
  `chart_version`.
- `helm/values.yaml`: commented conventions (`secrets.<name>.<KEY>: <sealed value>`, ingress,
  resources, and persistence with `helm.sh/resource-policy: keep`).
- `helm/templates/common.yaml.tpl`: `{{- include "common.all" . -}}`. It is listed in
  `_copy_without_render`, so cookiecutter does not render it.
- `skaffold.yaml`: one helm release, plus one profile per environment. Each profile adds
  `helm/values/<env>.yaml` and sets `kubeContext` (the environment's cluster) and the namespace.
- `.github/workflows/{build,deploy,release}.yaml`: thin callers of
  `OIT/ais-reusable-workflows/.github/workflows/*.yaml@main`. `deploy` takes a manual env input
  for the test environments. `release` deploys the production environment when a GitHub
  release is published.

## Environments

Environments come from these answers. All of the logic is in `local_extensions.py`, and
templates and hooks only call its filters, so change environment behavior there.

- `test_cluster` + `test_environment` (default `dev`): one test environment, unless
  `test_cluster` is `none`.
- `additional_environments`: optional comma-separated `name:cluster` pairs. These are more test
  environments.
- `prod_cluster` + `prod_environment` (default `prod`): the production environment, unless
  `prod_cluster` is `none`.

Rules:

- Any environment can use any cluster in `_k8s_cluster_details`.
- Profile order is test, then additional, then production.
- Namespaces are `<team>-<env>`. With `use_app_specific_namespace`, the namespace is the project
  slug, or `<slug>-<env>` when another environment shares the cluster.
- ArgoCD settings come from `_k8s_environment_spec[<env name>]`. Names that aren't there use
  `argo_project: <env>` and `ARGOCD_SERVER`.
- `hooks/pre_gen_project.py` fails generation, listing every problem, when there are no
  environments, a name isn't lowercase letters, numbers and hyphens, a name is duplicated, or a
  cluster is unknown. A name for an environment whose cluster is `none` is ignored.
- `Dockerfile` and `.dockerignore`: an intentionally broken placeholder, used only when
  `create_container` is true.

## Options that remove files

These are handled in `hooks/post_gen_project.py`, which is the place to add new ones:

- `create_container: false` removes `Dockerfile`, `.dockerignore` and `build.yaml`.
- No test environments (`test_cluster: none` and no `additional_environments`) removes
  `deploy.yaml`.
- No production environment (`prod_cluster: none`) removes `release.yaml`.
- Empty `ohio_helm_common_version` removes `helm/templates/common.yaml.tpl`.
- No chart dependencies (`deploy_3rdparty_chart: false` and empty `ohio_helm_common_version`)
  removes `helm/.gitignore`, which only ignores downloaded `charts/`.

## Testing changes

Run the test suite after every change (details in `test/README.md`):

```bash
python3 -m venv .venv && .venv/bin/pip install -r test/requirements.txt   # once
.venv/bin/pytest
```

- In the devcontainer everything is preinstalled, so just run `pytest`.
- `test/fixtures/<scenario>/` holds the exact expected output for each scenario in
  `test/scenarios.py`. If you change the output on purpose, run `pytest --overwrite-fixtures`,
  read the fixture diff with `git diff test/fixtures`, and commit it with the template change.
  Never overwrite fixtures to silence a failure you don't understand.
- When you add an option or a combination worth covering, add a scenario, run
  `pytest --generate-fixtures`, and review the new fixture. Add behavior checks to
  `test/test_options.py`.
- Known bugs are recorded as strict `xfail` tests (there are none right now). When you fix
  one, the test "unexpectedly passes" and fails the run. Remove its marker, and its
  `KNOWN_ACTIONLINT_FAILURES` entry if it has one.
- Each scenario's expected environments, as `(name, kind, cluster, namespace)`, are in
  `ENVIRONMENTS` in `test/scenarios.py`. Tests check workflows, skaffold profiles, the README and
  the values files against them.
- The suite never renders the Helm chart: no cluster, no Artifactory. Skaffold is only checked
  with `skaffold diagnose --yaml-only`.
- CI (`.github/workflows/test.yaml`) runs the suite on every push with `REQUIRE_TOOLS=1`.

## Jinja gotchas

- GitHub Actions expressions and Helm templates use `{{ }}` too. Wrap literal ones in
  `{% raw %}...{% endraw %}` or emit them as `{{ "{{" }}`. The workflows and `helm/README.md` show
  both patterns.
- `test_cluster` and `prod_cluster` are choice lists, so the first entry is the default
  (`k8s-sand` and `k8s-prod`). Each must list every key of `_k8s_cluster_details` plus `none`.
  `test_cluster_choices_match_cluster_details` enforces this, so add a new cluster in all three
  places.
- Loop over environments with `{% for env in cookiecutter|k8s_environments if env.kind == "prod" %}`,
  even where there is at most one. A loop renders nothing when there is none; `|first` would
  be undefined, and the strict environment would fail.
- `{%-` and `-%}` strip whitespace, including blank lines. The fixture tests catch lost or extra
  blank lines, so check the fixture diff for whitespace changes you didn't intend.
- `team_name` is lowercased in slugs and namespaces but is used as typed for `runner:`, and
  uppercased for secret names (`<TEAM>_GITHUB_PAT`, `<TEAM>_ARGOCD_TOKENS`).

## Known issues

These are left in deliberately, so don't "fix" them without asking:

- `build.yaml` hard-codes `secrets.CAD_GITHUB_PAT`. `deploy` and `release` use `<TEAM>_GITHUB_PAT`.
- The generated `helm/README.md` links `templates/_common.tpl`, which doesn't exist (the helpers
  come from the `common` library chart). It also says there are two environments, "test and
  prod", whatever environments were chosen.
- Replay files store the already-rendered `project_slug` and `container_image`. Changing
  `project_type` or `deploy_3rdparty_chart` in a replay file does not change the suffix. Edit
  those values too, or re-run without `--replay`.
- `hooks/post_gen_project.py` has an unused `import cookiecutter`.
- Workflows target the GHES org `OIT/`, while `git_repository` defaults to `github.com/ohioit/`.

## Related repos (siblings in `~/Documents/OHIO/Code`)

- `ais-helm-commons`: the `common` library chart (`common.all`, `common.labels`, and others). Its
  own AGENTS.md explains the values it supports.
- `ais-reusable-workflows`: the `build.yaml`, `deploy.yaml` and `release.yaml` called by the
  generated workflows.
- `vscode-devcontainer-base`: the devcontainer image both devcontainers use.

## Kubernetes

Only use Ohio University clusters, meaning API servers on `ohio.edu`. Ignore other kube contexts,
such as `gaea`. See `~/Documents/OHIO/Code/CLAUDE.md`.
