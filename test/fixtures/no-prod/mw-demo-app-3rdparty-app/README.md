# Demo App

Helm chart for Demo App. Generated from the Ohio application template by Cookiecutter.

This repository includes a devcontainer for Visual Studio Code that contains all
of the dependencies and plugins needed to work with the project.

## Introduction

There are a variety of ways to deploy applications to Kubernetes. You could use
bare Kubernetes manifests and deploy with [kubectl](https://kubernetes.io/docs/reference/kubectl/overview/)
or you can customize them with [kustomize](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/).
You could render those manifests with templates using [helm](https://helm.sh/docs/), bringing
in other dependencies as well or deploy and manage entire lifecycles with
[operators](https://olm.operatorframework.io/).

For now, we have chosen to manage third party applications using
[helm](https://helm.sh/docs/). Helm allows us to both pull in third party
definitions _and_ customize them by adding our own resources like
secrets. Additionally, helm can be integrated with _both_ [skaffold](https://skaffold.dev/docs/)
and [ArgoCD](https://argo-cd.readthedocs.io/en/stable/).

## Usage

First, you'll need the following tools installed:

- [Docker](https://docs.docker.com/get-docker/)
- [Skaffold](https://skaffold.dev/)
- [Helm](https://helm.sh/)

You will also need the following configuration for your local machine:

1. A kubernetes configuration in `~/.kube/config`. This is a YAML file that describes
   the clusters and users you want to use. Rancher [has instructions](https://ranchermanager.docs.rancher.com/how-to-guides/new-user-guides/manage-clusters/access-clusters/use-kubectl-and-kubeconfig#accessing-clusters-with-kubectl-from-your-workstation)
   for creating this file.

   > NOTE: Rancher will download a complete Kubeconfig file for each cluster. You will need to manually merge the files to create
   > a single configuration and set your default context to the minimum risk cluster: `kubectl config use-context {context}`. You
   > can get a list of contexts with `kubectl config get contexts`. Afterwards, use a different context with
   > `kubectl --context={context} ...`. Generally, `skaffold` will handle this for you.
2. Docker registry credentials for Artifactory. Use `docker login registry.example.com` to set them up. **NOTE** you will
   need your API token from Artifactory, not your password here. Generate a new token by going
   [here](https://registry.example.com/ui/user_profile) and using it as your password.
3. The Artifactory helm repository will have to be added. You'll need to use your Artifactory token you generated for Docker
   (or a new one). Unfortunately, the credentials have to be typed in as a CLI argument so it may be good to `export HISTFILE=""`
   before doing this. Simply run
   `helm repo add artifactory https://registry.example.com/artifactory/helm --username={ohio id} --password={token}`. Verify
   this works with `helm repo update`.

Once this is done, you can use the standard `skaffold` commands
or even the [Cloud Code](https://marketplace.visualstudio.com/items?itemName=GoogleCloudTools.cloudcode)
extension to work with the project:

- `skaffold dev`: Deploy to Kubernetes, tailing log files, and delete everything when finished.
- `skaffold build`: Build and push the project's Docker images, if any.
- `skaffold delete`: Delete everything.
- `skaffold run`: Deploy everything to Kubernetes
- `skaffold render`: Render the helm chart and show what _would_ be deployed.

> Note: Some of these commands will not work until the Helm chart dependencies are downloaded. You can
> manually do that with `helm dependency update helm` or simply do a `skaffold run` to grab them.

## Common Library

This template utilizies the [Ohio Helm Common Library](https://github.com/ohioit/ais-helm-commons)
which provides a lot of useful functionality both in templates and in values. For example, configmaps,
secrets, jobs, and even simple deployments can be defined entirely in values. See
[the documentation](https://github.com/ohioit/ais-helm-commons) for usage details.

## Repository Structure

Note, each subdirectory has it's own README with more information
about that part of the repository.


### [skaffold.yaml](skaffold.yaml)

The main entrypoint for command line work, see [the docs](https://skaffold.dev/docs/)
for details.

### [helm](helm)

Contains all of the deployment manifests and configuration, including
secrets.

### Profiles

There is not a valid default profile. Because of a lack of dev environment, you must
specify a profile with `-p`. Currently, the following profiles exist:

- dev: Deploys to mw-dev in k8s-sand
