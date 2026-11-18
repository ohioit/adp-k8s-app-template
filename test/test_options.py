"""Behavior checks for individual cookiecutter options and hooks.

These complement the fixtures: a fixture says "the output is exactly this",
these say *why* the output looks that way, so a failure points at the option
or hook that broke.
"""

from pathlib import Path

import pytest

from scenarios import ENVIRONMENTS, GENERIC, SCENARIOS, THIRD_PARTY

PROJECT_TYPES = ["app", "ui", "api", "integration"]


def files(project_path):
    return {p.relative_to(project_path).as_posix() for p in project_path.rglob("*") if p.is_file()}


def bake_ok(bake, context):
    result = bake(context)
    assert result.exception is None, result.exception
    return Path(result.project_path)


# --- Project naming ---------------------------------------------------------------


@pytest.mark.parametrize("project_type", PROJECT_TYPES)
@pytest.mark.parametrize(
    "base, middle",
    [(THIRD_PARTY, "-3rdparty"), (GENERIC, "")],
    ids=["3rdparty", "generic"],
)
def test_suffix(bake, project_type, base, middle):
    project = bake_ok(bake, {**base, "project_type": project_type, "create_container": "yes"})
    suffix = f"{middle}-{project_type}"
    assert project.name == f"mw-demo-app{suffix}"
    skaffold = (project / "skaffold.yaml").read_text()
    assert f"image: docker.registry.example.com/mw/demo-app{suffix}\n" in skaffold


def test_invalid_project_type_is_rejected(bake):
    result = bake({**GENERIC, "project_type": "web"})
    assert result.exit_code != 0
    assert "choices are" in str(result.exception)


# --- hooks/pre_gen_project.py -----------------------------------------------------


@pytest.mark.parametrize(
    "field", ["upstream_project_name", "upstream_project_helm_repo", "upstream_project_version"]
)
def test_3rdparty_requires_upstream_field(bake, capfd, field):
    result = bake({**THIRD_PARTY, field: ""})
    assert result.exit_code != 0
    assert "Hook script failed" in str(result.exception)
    # The hook runs as a subprocess, so its message is on the real stderr.
    assert f"these are empty: {field}" in capfd.readouterr().err


def test_generic_ignores_empty_upstream_fields(baked_scenario):
    # GENERIC has no upstream_* answers at all; generation must still succeed.
    project = baked_scenario("generic-app")
    assert "upstream" not in (project / "helm" / "Chart.yaml").read_text().lower()


# --- hooks/post_gen_project.py ----------------------------------------------------

CONTAINER_FILES = {"Dockerfile", ".dockerignore", ".github/workflows/build.yaml"}


@pytest.mark.parametrize("scenario", ["default", "generic-app"])
def test_no_container_removes_container_files(baked_scenario, scenario):
    assert not CONTAINER_FILES & files(baked_scenario(scenario))


@pytest.mark.parametrize("scenario", ["3rdparty-container", "generic-ui-container"])
def test_container_keeps_container_files(baked_scenario, scenario):
    assert CONTAINER_FILES <= files(baked_scenario(scenario))


def test_no_common_library_removes_common_template(baked_scenario):
    assert "helm/templates/common.yaml.tpl" not in files(baked_scenario("generic-bare"))
    assert "helm/templates/common.yaml.tpl" in files(baked_scenario("generic-app"))


def test_helm_gitignore_only_when_chart_has_dependencies(baked_scenario):
    assert "helm/.gitignore" not in files(baked_scenario("generic-bare"))
    assert "helm/.gitignore" in files(baked_scenario("generic-app"))
    assert "helm/.gitignore" in files(baked_scenario("default"))


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_values_file_per_environment(baked_scenario, scenario):
    generated = {f for f in files(baked_scenario(scenario)) if f.startswith("helm/values/")}
    assert generated == {f"helm/values/{name}.yaml" for name, *_ in ENVIRONMENTS[scenario]}


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_workflows_match_environment_kinds(baked_scenario, scenario):
    """deploy.yaml only with test environments, release.yaml only with production."""
    kinds = {kind for _, kind, *_ in ENVIRONMENTS[scenario]}
    generated = files(baked_scenario(scenario))
    assert (".github/workflows/deploy.yaml" in generated) == ("test" in kinds)
    assert (".github/workflows/release.yaml" in generated) == ("prod" in kinds)


# --- Environments and clusters ------------------------------------------------------


def workflow_jobs(project, workflow):
    """Return {job name: {input: value}} for a generated workflow."""
    import yaml

    data = yaml.safe_load((project / ".github" / "workflows" / workflow).read_text())
    return {name: job["with"] for name, job in data["jobs"].items()}


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_workflow_targets(baked_scenario, scenario):
    project = baked_scenario(scenario)
    for name, kind, cluster, namespace in ENVIRONMENTS[scenario]:
        workflow = "deploy.yaml" if kind == "test" else "release.yaml"
        job = workflow_jobs(project, workflow)[f"deploy-{name}"]
        assert job["target_cluster"] == f"https://{cluster.removeprefix('k8s-')}.k8s.example.com"
        assert job["target_namespace"] == namespace
        assert job["argocd_token_key"] == name


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_readme_lists_profiles(baked_scenario, scenario):
    readme = (baked_scenario(scenario) / "README.md").read_text()
    for name, _, cluster, namespace in ENVIRONMENTS[scenario]:
        assert f"- {name}: Deploys to {namespace} in {cluster}" in readme


def test_argocd_spec_and_fallback(baked_scenario):
    jobs = workflow_jobs(baked_scenario("additional-environments"), "deploy.yaml")
    # "sand" is in _k8s_environment_spec with its own ArgoCD server variable.
    assert jobs["deploy-sand"]["argocd_project"] == "mw-sand"
    deploy = (baked_scenario("additional-environments") / ".github/workflows/deploy.yaml").read_text()
    assert "vars.ARGOCD_SERVER_SANDBOX" in deploy.split("deploy-sand:")[1].split("deploy-stage:")[0]
    # "stage" and "production" aren't, so they fall back to their own name and ARGOCD_SERVER.
    assert jobs["deploy-stage"]["argocd_project"] == "mw-stage"
    release = workflow_jobs(baked_scenario("custom-names"), "release.yaml")
    assert release["deploy-production"]["argocd_project"] == "mw-production"


@pytest.mark.parametrize(
    "answers, message",
    [
        ({"test_cluster": "none", "prod_cluster": "none"}, "no environments"),
        ({"test_environment": "Dev"}, "environment name 'Dev' must be lowercase"),
        ({"prod_environment": "my_prod"}, "environment name 'my_prod' must be lowercase"),
        ({"test_environment": "prod"}, "environment 'prod' is defined more than once"),
        ({"additional_environments": "dev:k8s-dev"}, "environment 'dev' is defined more than once"),
        ({"additional_environments": "stage"}, "'stage' must look like 'name:cluster'"),
        ({"additional_environments": "stage:"}, "'stage:' must look like 'name:cluster'"),
        ({"additional_environments": "stage:k8s-nope"}, "unknown cluster 'k8s-nope'"),
        ({"additional_environments": "stage:none"}, "unknown cluster 'none'"),
    ],
    ids=lambda value: value if isinstance(value, str) else None,
)
def test_invalid_environments_are_rejected(bake, capfd, answers, message):
    result = bake({**THIRD_PARTY, **answers})
    assert result.exit_code != 0
    assert "Hook script failed" in str(result.exception)
    assert message in capfd.readouterr().err


def test_ignored_names_are_not_validated(bake):
    """A name for an environment set to 'none' is ignored, so it can't fail generation."""
    result = bake({**THIRD_PARTY, "prod_cluster": "none", "prod_environment": "Not Valid"})
    assert result.exception is None, result.exception


def test_cluster_choices_match_cluster_details():
    """Every cluster offered in a question must have an entry in _k8s_cluster_details."""
    import json

    config = json.loads((Path(__file__).resolve().parent.parent / "cookiecutter.json").read_text())
    known = set(config["_k8s_cluster_details"]) | {"none"}
    for question in ("test_cluster", "prod_cluster"):
        assert set(config[question]) <= known, question
        assert set(config[question]) == known, f"{question} doesn't offer every cluster"
