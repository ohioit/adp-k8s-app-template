import sys

DEPLOY_3RDPARTY_CHART = {{ cookiecutter.deploy_3rdparty_chart }}

# Problems with the environment and cluster answers, found by local_extensions.py.
ENVIRONMENT_ERRORS = {{ cookiecutter|k8s_environment_errors|jsonify }}

REQUIRED_FOR_3RDPARTY = {
    "upstream_project_name": "{{ cookiecutter.upstream_project_name }}",
    "upstream_project_helm_repo": "{{ cookiecutter.upstream_project_helm_repo }}",
    "upstream_project_version": "{{ cookiecutter.upstream_project_version }}",
}

if DEPLOY_3RDPARTY_CHART:
    missing = [name for name, value in REQUIRED_FOR_3RDPARTY.items() if not value.strip()]
    if missing:
        print(
            "ERROR: deploy_3rdparty_chart is enabled but these are empty: "
            + ", ".join(missing),
            file=sys.stderr,
        )
        sys.exit(1)

if ENVIRONMENT_ERRORS:
    print("ERROR: invalid environments:", file=sys.stderr)
    for error in ENVIRONMENT_ERRORS:
        print(f"  - {error}", file=sys.stderr)
    sys.exit(1)
