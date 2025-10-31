# Ohio University Third Party Application Template

This repository contains a template for third party applications. While
not strictly required, the repo is a good way to build and deploy
applications in a repeatable and familiar way.

The template is based on [cookiecutter](https://cookiecutter.readthedocs.io/)
so is not usable directly, cookiecutter should be used to generate a new directory
on your system for the project and then commit the changes to a new repository.

## Usage

First, [install cookiecutter](https://cookiecutter.readthedocs.io/en/stable/installation.html).

Next, navigate to a folder on your system where you want your new project to be, then
run:

```bash
cookiecutter https://github.com/ohioit/example-3rdparty-app.git
```

> [!NOTE] If you are using SSH keys, be sure to change that to `git@github.com/ohioit/example-3rdparty-app.git`

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
cookiecutter /workspaces/template-3rdparty-app
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
> again, or simply manually edit `~/.cookiecutter_replay/template-3rdparty-app.json`.

For more information, check out the
[extensive cookiecutter documentation](https://cookiecutter.readthedocs.io).
