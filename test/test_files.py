"""Check that generated files are well-formed for the tools that consume them.

Nothing here needs a Kubernetes cluster or access to Artifactory. The Helm chart
is not rendered: the common chart is tested in ais-helm-commons and upstream
charts by their own projects.
"""

import json
import re
import subprocess
from pathlib import Path

import pytest
import yaml

from conftest import REPO_ROOT, require_tool
from scenarios import ENVIRONMENTS, KNOWN_ACTIONLINT_FAILURES, SCENARIOS

SEMVER = re.compile(r"^\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?(\+[0-9A-Za-z.-]+)?$")


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_yaml_and_json_parse(baked_scenario, scenario):
    project = baked_scenario(scenario)
    for path in list(project.rglob("*.yaml")) + list(project.rglob("*.yml")):
        yaml.safe_load(path.read_text())
    for path in project.rglob("*.json"):
        json.loads(path.read_text())


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_chart_metadata(baked_scenario, scenario):
    project = baked_scenario(scenario)
    chart = yaml.safe_load((project / "helm" / "Chart.yaml").read_text())
    context = SCENARIOS[scenario]
    third_party = context.get("deploy_3rdparty_chart") == "yes"
    common = context.get("ohio_helm_common_version", "<1.0.0") != ""

    assert chart["apiVersion"] == "v2"
    assert chart["name"] == project.name
    assert chart["type"] == "application"
    assert SEMVER.match(str(chart["version"])), chart["version"]
    if third_party:
        assert chart["version"].endswith("-OHIO-1")

    dependencies = chart.get("dependencies") or []
    for dependency in dependencies:
        assert dependency.get("name") and dependency.get("version") and dependency.get("repository"), dependency
    names = [d["name"] for d in dependencies]
    assert ("common" in names) == common
    assert (context.get("upstream_project_name") in names) == third_party


def actionlint_params():
    for scenario in SCENARIOS:
        reason = KNOWN_ACTIONLINT_FAILURES.get(scenario)
        marks = [pytest.mark.xfail(strict=True, reason=reason)] if reason else []
        yield pytest.param(scenario, marks=marks, id=scenario)


@pytest.mark.parametrize("scenario", list(actionlint_params()))
def test_generated_workflows_pass_actionlint(baked_scenario, scenario):
    actionlint = require_tool("actionlint")
    workflows = sorted((baked_scenario(scenario) / ".github" / "workflows").glob("*.yaml"))
    if not workflows:
        pytest.skip("scenario generates no workflows")
    result = subprocess.run([actionlint, "-no-color", *map(str, workflows)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_repo_workflows_pass_actionlint():
    actionlint = require_tool("actionlint")
    workflows = sorted((REPO_ROOT / ".github" / "workflows").glob("*.y*ml"))
    assert workflows, "the repo's own CI workflow is missing"
    result = subprocess.run([actionlint, "-no-color", *map(str, workflows)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def skaffold_params():
    for scenario in SCENARIOS:
        for name, _, cluster, namespace in ENVIRONMENTS[scenario]:
            yield pytest.param(scenario, name, cluster, namespace, id=f"{scenario}-{name}")


@pytest.mark.parametrize("scenario, env, cluster, namespace", list(skaffold_params()))
def test_skaffold_profile(baked_scenario, scenario, env, cluster, namespace):
    """`skaffold diagnose --yaml-only` validates skaffold.yaml and applies the profile offline."""
    skaffold = require_tool("skaffold")
    project = baked_scenario(scenario)
    result = subprocess.run(
        [skaffold, "diagnose", "--yaml-only", "--profile", env],
        cwd=project,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    config = yaml.safe_load(result.stdout)
    release = config["deploy"]["helm"]["releases"][0]

    assert release["name"] == project.name
    values_files = [Path(p) for p in release["valuesFiles"]]
    assert [p.relative_to(project).as_posix() for p in values_files] == [
        "helm/values.yaml",
        f"helm/values/{env}.yaml",
    ]
    assert all(p.is_file() for p in values_files)

    assert release["namespace"] == namespace
    assert config["deploy"]["kubeContext"] == cluster
