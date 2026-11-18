"""Jinja filters used by the template (loaded via "_extensions" in cookiecutter.json).

All environment and cluster logic lives here instead of being repeated in every
template and hook. Templates call:

    {% for env in cookiecutter|k8s_environments %}   every environment, in order
    cookiecutter|k8s_environment_errors               validation errors (pre_gen hook)

Each environment is a dict with these keys:

    name             environment name, also the skaffold profile and values file name
    kind             "test" (deployed by deploy.yaml) or "prod" (deployed by release.yaml)
    cluster          kube context / key of _k8s_cluster_details
    cluster_url      API server URL of the cluster
    namespace        namespace to deploy to
    argo_project     ArgoCD project suffix (the full project is <team>-<argo_project>)
    argo_server_var  name of the GitHub variable holding the ArgoCD server

Environments come from these answers, in this order:

    test_cluster / test_environment   one test environment, unless test_cluster is "none"
    additional_environments           "name:cluster" pairs, comma separated (all "test" kind)
    prod_cluster / prod_environment   the production environment, unless prod_cluster is "none"
"""

import re

from cookiecutter.utils import simple_filter

NO_CLUSTER = "none"
ENVIRONMENT_NAME = re.compile(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$")
DEFAULT_ARGO_SERVER_VAR = "ARGOCD_SERVER"


def _parse(context):
    """Return (environments, errors) for a cookiecutter context."""
    clusters = context["_k8s_cluster_details"]
    errors = []
    requested = []  # (name, cluster, kind, where the answer came from)

    if context["test_cluster"] != NO_CLUSTER:
        requested.append((context["test_environment"].strip(), context["test_cluster"], "test", "test_environment"))

    for entry in context["additional_environments"].split(","):
        entry = entry.strip()
        if not entry:
            continue
        name, separator, cluster = (part.strip() for part in entry.partition(":"))
        if not separator or not name or not cluster or ":" in cluster:
            errors.append(f"additional_environments: {entry!r} must look like 'name:cluster'")
            continue
        requested.append((name, cluster, "test", "additional_environments"))

    if context["prod_cluster"] != NO_CLUSTER:
        requested.append((context["prod_environment"].strip(), context["prod_cluster"], "prod", "prod_environment"))

    if not requested and not errors:
        errors.append(
            "no environments: set test_cluster or prod_cluster to a cluster, or add additional_environments"
        )

    seen = set()
    for name, cluster, _, source in requested:
        if not ENVIRONMENT_NAME.match(name):
            errors.append(
                f"{source}: environment name {name!r} must be lowercase letters, numbers and hyphens, "
                "starting and ending with a letter or number"
            )
        if name in seen:
            errors.append(f"{source}: environment {name!r} is defined more than once")
        seen.add(name)
        if cluster not in clusters:
            errors.append(
                f"{source}: unknown cluster {cluster!r} for environment {name!r} "
                f"(known clusters: {', '.join(clusters)})"
            )

    if errors:
        return [], errors

    cluster_use = {}
    for _, cluster, _, _ in requested:
        cluster_use[cluster] = cluster_use.get(cluster, 0) + 1

    team = context["team_name"].lower()
    specs = context["_k8s_environment_spec"]
    environments = []
    for name, cluster, kind, _ in requested:
        if not context["use_app_specific_namespace"]:
            namespace = f"{team}-{name}"
        elif cluster_use[cluster] > 1:
            # Several environments share this cluster; give each its own namespace.
            namespace = f"{context['project_slug']}-{name}"
        else:
            namespace = context["project_slug"]
        spec = specs.get(name, {})
        environments.append(
            {
                "name": name,
                "kind": kind,
                "cluster": cluster,
                "cluster_url": clusters[cluster]["url"],
                "namespace": namespace,
                "argo_project": spec.get("argo_project", name),
                "argo_server_var": spec.get("argo_server_var", DEFAULT_ARGO_SERVER_VAR),
            }
        )
    return environments, []


@simple_filter
def k8s_environments(context):
    environments, errors = _parse(context)
    if errors:
        # The pre_gen hook reports these nicely before any file is rendered.
        raise ValueError("; ".join(errors))
    return environments


@simple_filter
def k8s_environment_errors(context):
    return _parse(context)[1]
