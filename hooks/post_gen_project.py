import cookiecutter
import os
import shutil

REMOVE_PATHS = [
    '{% if not cookiecutter.create_container %}Dockerfile{% endif %}',
    '{% if not cookiecutter.create_container %}.dockerignore{% endif %}',
    '{% if not cookiecutter.create_container %}.github/workflows/build.yaml{% endif %}',
    '{% if cookiecutter.k8s_environments|length == 0 %}.github/workflows/deploy.yaml{% endif %}',
    '{% if cookiecutter.k8s_environments|length == 0 %}.github/workflows/release.yaml{% endif %}',
    '{% if "prod" not in cookiecutter.k8s_environments %}.github/workflows/release.yaml{% endif %}',
    '{% if cookiecutter.ohio_helm_common_version.strip()|length == 0 %}helm/templates/common.yaml.tpl{% endif %}'
]

for path in REMOVE_PATHS:
    path = path.strip()
    if path and os.path.exists(path):
        if os.path.isdir(path):
            os.rmdir(path)
        else:
            os.remove(path)

K8S_ENVIRONMENTS = "{{ cookiecutter.k8s_environments }}".split(',')
K8S_ENVIRONMENTS = [env.strip() for env in K8S_ENVIRONMENTS]
K8S_ENVIRONMENT_VALUES_TEMPLATE = "helm/values/environment.yaml"

for environment in K8S_ENVIRONMENTS:
    destination = os.path.join("helm","values", f'{environment}.yaml')

    if not os.path.exists(os.path.dirname(destination)):
        os.makedirs(os.path.dirname(destination))

    shutil.copyfile(K8S_ENVIRONMENT_VALUES_TEMPLATE, destination)

os.remove(K8S_ENVIRONMENT_VALUES_TEMPLATE)
