"""Named sets of cookiecutter answers ("scenarios") shared by all tests.

Each scenario has a fixture in test/fixtures/<scenario name>/ holding the
expected generated project. Add a scenario here when you add an option or a
combination of options worth covering, then run
`pytest --generate-fixtures` and review the new fixture before committing it.
"""

# Answers shared by every scenario. Values are fixed so the output, and therefore
# the fixtures, don't depend on the machine running the tests.
BASE = {
    "author_name": "Test Author",
    "author_email": "test.author@example.com",
    "team_name": "mw",
    "project_name": "Demo App",
}

# Answers needed when deploy_3rdparty_chart is true (enforced by hooks/pre_gen_project.py).
UPSTREAM = {
    "upstream_project_name": "demo",
    "upstream_project_github": "https://github.com/example/demo",
    "upstream_project_helm_repo": "https://charts.example.com",
    "upstream_project_helm_documentation": "https://charts.example.com/demo",
    "upstream_project_version": "1.2.3",
}

THIRD_PARTY = {**BASE, **UPSTREAM, "deploy_3rdparty_chart": "yes"}
GENERIC = {**BASE, "deploy_3rdparty_chart": "no"}

SCENARIOS = {
    # 3rd-party chart with the common library, no container, dev on k8s-sand and prod on k8s-prod.
    "default": THIRD_PARTY,
    "3rdparty-container": {**THIRD_PARTY, "create_container": "yes"},
    "app-specific-namespace": {**THIRD_PARTY, "use_app_specific_namespace": "yes"},
    # Test and prod on the same cluster.
    "shared-cluster": {**THIRD_PARTY, "test_cluster": "k8s-sand", "prod_cluster": "k8s-sand"},
    # Same, with app-specific namespaces: each environment gets <slug>-<env> so they don't collide.
    "shared-cluster-app-namespace": {
        **THIRD_PARTY,
        "test_cluster": "k8s-sand",
        "prod_cluster": "k8s-sand",
        "use_app_specific_namespace": "yes",
    },
    # "sand" is in _k8s_environment_spec (its own ArgoCD server); "stage" uses the defaults.
    "additional-environments": {**THIRD_PARTY, "additional_environments": "sand:k8s-sand, stage:k8s-dev"},
    # Names that aren't in _k8s_environment_spec.
    "custom-names": {**THIRD_PARTY, "test_environment": "qa", "prod_environment": "production"},
    "no-prod": {**THIRD_PARTY, "prod_cluster": "none"},
    "no-test": {**THIRD_PARTY, "test_cluster": "none"},
    # Not a 3rd-party chart.
    "generic-app": GENERIC,
    "generic-bare": {**GENERIC, "ohio_helm_common_version": ""},
    "generic-ui-container": {**GENERIC, "project_type": "ui", "create_container": "yes"},
}

# Expected environments per scenario: (name, kind, cluster, namespace), in profile order.
DEFAULT_ENVIRONMENTS = [
    ("dev", "test", "k8s-sand", "mw-dev"),
    ("prod", "prod", "k8s-prod", "mw-prod"),
]
ENVIRONMENTS = {name: DEFAULT_ENVIRONMENTS for name in SCENARIOS}
ENVIRONMENTS.update(
    {
        "app-specific-namespace": [
            ("dev", "test", "k8s-sand", "mw-demo-app-3rdparty-app"),
            ("prod", "prod", "k8s-prod", "mw-demo-app-3rdparty-app"),
        ],
        "shared-cluster": [
            ("dev", "test", "k8s-sand", "mw-dev"),
            ("prod", "prod", "k8s-sand", "mw-prod"),
        ],
        "shared-cluster-app-namespace": [
            ("dev", "test", "k8s-sand", "mw-demo-app-3rdparty-app-dev"),
            ("prod", "prod", "k8s-sand", "mw-demo-app-3rdparty-app-prod"),
        ],
        "additional-environments": [
            ("dev", "test", "k8s-sand", "mw-dev"),
            ("sand", "test", "k8s-sand", "mw-sand"),
            ("stage", "test", "k8s-dev", "mw-stage"),
            ("prod", "prod", "k8s-prod", "mw-prod"),
        ],
        "custom-names": [
            ("qa", "test", "k8s-sand", "mw-qa"),
            ("production", "prod", "k8s-prod", "mw-production"),
        ],
        "no-prod": [("dev", "test", "k8s-sand", "mw-dev")],
        "no-test": [("prod", "prod", "k8s-prod", "mw-prod")],
    }
)

# Scenarios whose generated workflows fail actionlint because of a known bug, as
# {scenario: reason}. Remove an entry once the bug is fixed (the strict xfail will
# start failing to remind you).
KNOWN_ACTIONLINT_FAILURES = {}
