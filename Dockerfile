FROM alpine:3.24.1@sha256:28bd5fe8b56d1bd048e5babf5b10710ebe0bae67db86916198a6eec434943f8b

# uv
COPY --from=ghcr.io/astral-sh/uv:0.12.4@sha256:d0a6eca6c669dc7e9c51218707b8438a3d30402733d739dcc00adb3e213e8f5c /uv /uvx /bin/

RUN adduser --disabled-password app

USER app
WORKDIR /opt/github-status-pushover

COPY main.py pyproject.toml /opt/github-status-pushover/
ENTRYPOINT [ "uv", "run", "main.py" ]
