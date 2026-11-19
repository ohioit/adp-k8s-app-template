# Agent Instructions

## Overview

This is a cookiecutter template for Ohio app repos. It generates a Helm chart (which can use the
`common` library chart from `ais-helm-commons`), skaffold profiles, and GitHub Actions that deploy
through ArgoCD.

- Nothing at the top level is deployed.
- Generated repos that people have since worked on sit next to this one, e.g.
  `ais-minio-3rdparty-app`.
- Hostnames (`*.example.com`) are sanitized placeholders. Keep them unless asked.

The project type sets the suffix through `__project_suffix`, which `project_slug` and
`container_image` use. The suffix also depends on `deploy_3rdparty_chart`:

| Setting | Suffix | Chart | Version | pre_gen hook |
| --- | --- | --- | --- | --- |
| `project_type`, one of `app`/`ui`/`api`/`integration` | `-<type>` | | | |
| `deploy_3rdparty_chart: true` (default) | `-3rdparty-<type>` | Wraps an upstream chart | `<upstream>-OHIO-<n>` | Requires `upstream_project_name`, `upstream_project_helm_repo` and `upstream_project_version` |
| `deploy_3rdparty_chart: false` | `-<type>` | Generic; upstream answers are ignored | `chart_version` (default `0.1.0`) | |

Generated docs and comments must be generic. Put 3rd-party wording inside
`{% if cookiecutter.deploy_3rdparty_chart %}`.

## Layout

| Path | Purpose |
| --- | --- |
| `cookiecutter.json` | Prompts, defaults, and the private tables `_k8s_cluster_details` and `_k8s_environment_spec` |
| `local_extensions.py` | Filters `k8s_environments` and `k8s_environment_errors`, which hold all environment logic |
| `hooks/pre_gen_project.py` | Validates the upstream fields and the environments |
| `hooks/post_gen_project.py` | Removes optional files and copies `helm/values/environment.yaml` to `<env>.yaml` for each environment |
| `{{cookiecutter.project_slug}}/` | The generated project |
| `test/`, `.github/workflows/test.yaml` | The pytest suite and the CI that runs it |
| `.devcontainer/` | Base image (with skaffold) plus a Python 3.14 venv with the test requirements |

In the generated project:

- **`skaffold.yaml`** has one profile per environment. Each sets `helm/values/<env>.yaml`,
  `kubeContext` and the namespace.
- **The workflows** call `OIT/ais-reusable-workflows`:
  - `build`: builds the container;
  - `deploy`: deploys test environments on manual dispatch;
  - `release`: deploys prod when a release is published.
- **`helm/templates/common.yaml.tpl`** is in `_copy_without_render`.

## Environments

Change environment behavior in `local_extensions.py` only.

- **Order:** environments come from these questions, in profile order:
  1. `test_cluster` + `test_environment`;
  2. `additional_environments`, as `name:cluster,...` (all test environments);
  3. `prod_cluster` + `prod_environment`.

  A cluster of `none` disables that environment.
- **Clusters:** any environment can use any cluster.
- **Namespace:** `<team>-<env>`. With `use_app_specific_namespace`, it's the slug, or
  `<slug>-<env>` when another environment shares the cluster.
- **ArgoCD:** settings come from `_k8s_environment_spec[<env>]`. Names that aren't there get
  `argo_project: <env>` and `ARGOCD_SERVER`.
- **Validation:** pre_gen fails, listing every error, when there are no environments, a name
  isn't a lowercase slug, a name is duplicated, an `additional_environments` entry is malformed,
  or a cluster is unknown.

## GitHub repositories

Repos for generated projects are **internal** by default.
- Fall back to **private** only when internal isn't available. Internal needs GitHub Enterprise:
  github.ohio.edu has it, while a github.com org may not.
- Never default to private or public. Make a repo public only when the user explicitly asks.
- This applies to code that creates repos and to repos you create by hand.

## Files removed by `hooks/post_gen_project.py`

Add new removals in the same hook.

| Condition | Removed |
| --- | --- |
| `create_container: false` | `Dockerfile` (a deliberately broken placeholder), `.dockerignore` and `build.yaml` |
| No test environment | `deploy.yaml` |
| No prod environment | `release.yaml` |
| Empty `ohio_helm_common_version` | `common.yaml.tpl` |
| No chart dependencies | `helm/.gitignore` |

## Testing

Run `pytest` after every change. In the devcontainer it's ready to run. Elsewhere, install
`test/requirements.txt` into `.venv` first. Details are in `test/README.md`.

- **Fixtures:** `test/fixtures/<scenario>/` is the exact expected output for each scenario in
  `test/scenarios.py`.
  - For an intended output change, run `pytest --overwrite-fixtures`, review
    `git diff test/fixtures`, and commit it with the template change.
  - Never overwrite fixtures to silence a failure you don't understand.
- **New options or combinations:** add a scenario, run `pytest --generate-fixtures`, and review
  the new fixture. Put behavior checks in `test/test_options.py`, and expected environments in
  `ENVIRONMENTS`.
- **Known bugs:** recorded as strict `xfail` tests. A fix makes the test XPASS; then remove its
  marker.
- **Scope:** no chart rendering, cluster or Artifactory. Skaffold is checked only with
  `skaffold diagnose --yaml-only`.

## Jinja gotchas

- **Literal `{{ }}`** for Actions or Helm: wrap in `{% raw %}`, or write `{{ "{{" }}`.
- **Cluster choices:** `test_cluster` and `prod_cluster` must list every key of
  `_k8s_cluster_details` plus `none`, and a test enforces this. The first entry is the default.
- **Environment loops:** use
  `{% for env in cookiecutter|k8s_environments if env.kind == "prod" %}`, even for a single
  environment. `|first` fails when there's none.
- **Whitespace:** `{%-`/`-%}` also strip blank lines, so check fixture diffs for whitespace
  changes.
- **`team_name`:** lowercased in slugs and namespaces, used as typed in `runner:`, and uppercased
  in secret names (`<TEAM>_GITHUB_PAT`).

## Known issues

These are deliberate. Don't fix them without asking.

- `build.yaml` uses `CAD_GITHUB_PAT`, while the other workflows use `<TEAM>_GITHUB_PAT`.
- The generated `helm/README.md` links the nonexistent `_common.tpl` and always says "test and
  prod".
- Replay files store the rendered slug. Changing `project_type` there doesn't change the suffix.
- `hooks/post_gen_project.py` has an unused `import cookiecutter`.
- The workflows target the GHES org `OIT/`, but `git_repository` defaults to github.com `ohioit/`.

## Kubernetes

Use only clusters whose API servers are on `ohio.edu`. Ignore other contexts, such as `gaea`.
