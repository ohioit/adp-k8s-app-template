# Ohio University Application Template

This repository contains a template for applications deployed to Kubernetes
with Helm, skaffold and ArgoCD. While not strictly required, the repo is a
good way to build and deploy applications in a repeatable and familiar way.

The first questions describe the project. "What kind of project is this?"
picks the project type, which for now mainly sets the suffix of the project
slug and container image name:

| Type | Use it for | Suffix |
| --- | --- | --- |
| `app` | A full application (UI and backend) | `-app` |
| `ui` | A UI only: static, in-browser, depending on backend services not in the repo | `-ui` |
| `api` | An API only | `-api` |
| `integration` | A batch job, scheduled task, or other integration | `-integration` |

The template also supports two kinds of chart, chosen by the
"Will this project deploy a 3rd-party application that already has a Helm chart?"
question:

- **Yes (3rd-party application):** the generated Helm chart pulls in the
  upstream application's chart as a dependency and adds Ohio-specific
  configuration on top, such as sealed secrets and per-environment values.
  The chart version follows the `{upstream version}-OHIO-{n}` convention and
  `-3rdparty` is added before the type suffix, e.g. `-3rdparty-app`. The upstream questions (chart name,
  Helm repository and version) are required.
- **No:** the generated Helm chart contains only your own resources (and the
  Ohio Helm Common Library, if enabled). It uses a plain semantic version
  (`0.1.0` by default), the slug ends in just the type suffix, e.g. `-app`,
  and the upstream questions are ignored.

The template is based on [cookiecutter](https://cookiecutter.readthedocs.io/)
so is not usable directly, cookiecutter should be used to generate a new directory
on your system for the project and then commit the changes to a new repository.

## Environments

The template asks for up to three kinds of environment. Each one can use any
cluster:

- **Production:** pick a cluster, or `none` if the project has no production
  environment, and give it a name (default `prod`). It is deployed by the
  generated `release` workflow when a GitHub release is published. With `none`,
  no release workflow is generated.
- **Test:** pick a cluster, or `none`, and give it a name (default `dev`). It is
  deployed on demand by the generated `deploy` workflow.
- **Additional test environments:** optional `name:cluster` pairs, for example
  `sand:k8s-sand,stage:k8s-dev`. These are also deployed by the `deploy` workflow.

You need at least one environment. Every environment gets a skaffold profile and a
`helm/values/<name>.yaml` file. Its namespace is `<team>-<name>`. If you choose an
application-specific namespace, it is the project slug instead, or
`<slug>-<name>` when several environments share a cluster.

Generation stops with an explanation if the answers are invalid. For example: no
environments, a name that isn't lowercase letters, numbers and hyphens, a
duplicate name, or an unknown cluster.

## Usage

First, [install cookiecutter](https://cookiecutter.readthedocs.io/en/stable/installation.html).

Next, navigate to a folder on your system where you want your new project to be, then
run:

```bash
cookiecutter https://github.com/ohioit/adp-k8s-app-template.git
```

> [!NOTE] If you are using SSH keys, be sure to change that to `git@github.com:ohioit/adp-k8s-app-template.git`

Answer the questions presented by Cookiecutter. When you're finished, there
should be a new directory with your project name. If you would like, you
should be able to open that in your favorite editor. A devcontainer is included.

Next, create a new repository on [https://github.com](GitHub). Note that
while this template should work on either our cloud or on-prem version, the
included GitHub Actions were intended to work only with GHES repositories.

> [!NOTE] TODO: Document configuring the repository for use with the included actions.
> For now, ask someone what you need to do.

Once you have the repository configured, use the instructions provided to
commit your "existing code", the generated project directory, to
your new repository.

## Development

Template development is fairly easy inside of the devcontainer. When you
are ready to test the template, simply `cd ~` and run:

```bash
cookiecutter /workspaces/adp-k8s-app-template
```

A new directory will be generated using the project slug you specified. You
can either look at in the console, or use `code {project-slug}` to open it
in Visual Studio Code.

To facilitate more rapid iteration, add the `-f --replay` tags to:

- `-f`: Overwrite the existing generated project
- `--replay`: Use a saved replay file to prevent being prompted for all
  of the questions again.

> [!WARNING] A replay file saves a fully generated `cookiecutter.json`.
> If you make changes to the `cookiecutter.json` in the template, those
> changes **will not** be reflected in a replay. Either run without replaying
> again, or simply manually edit `~/.cookiecutter_replay/adp-k8s-app-template.json`.

For more information, check out the
[extensive cookiecutter documentation](https://cookiecutter.readthedocs.io).

## Testing

The template has an automated test suite in [test/](test/README.md). It renders the
template with a set of answers ("scenarios") and compares each result to committed
fixtures. It also checks that the generated YAML, workflows and skaffold profiles
are valid. It needs no Kubernetes cluster or Artifactory access, and it runs on
every push via [GitHub Actions](.github/workflows/test.yaml).

Inside the devcontainer, run:

```bash
pytest
```

Outside it, you need Python 3.14 or newer. Install the dependencies once and then
run the tests:

```bash
python3 -m venv .venv
.venv/bin/pip install -r test/requirements.txt
.venv/bin/pytest
```

If you change the generated output on purpose, update the fixtures with
`pytest --overwrite-fixtures`. Review `git diff test/fixtures` and commit it with
your change. See [test/README.md](test/README.md) for details.
