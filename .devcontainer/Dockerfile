FROM ghcr.io/astral-sh/uv:0.13.9 AS uv

FROM ghcr.io/ohioit/vscode-devcontainer-base:latest

# The base image already provides skaffold, but its system Python is Ubuntu's
# 3.12. uv installs a standalone Python 3.14 and creates a virtualenv with
# cookiecutter and the test suite's dependencies.
# Build context is the repository root (see devcontainer.json).
COPY --from=uv /uv /usr/local/bin/uv

ENV UV_PYTHON_INSTALL_DIR=/opt/uv-python \
    UV_NO_CACHE=1

COPY test/requirements.txt /tmp/test-requirements.txt
RUN uv python install 3.14 \
    && uv venv --python 3.14 /opt/template-venv \
    && uv pip install --python /opt/template-venv/bin/python -r /tmp/test-requirements.txt \
    && rm /tmp/test-requirements.txt \
    && chown -R vscode:vscode /opt/template-venv /opt/uv-python

# Put python3.14, cookiecutter, pytest and actionlint on PATH for every shell.
ENV PATH=/opt/template-venv/bin:${PATH}
