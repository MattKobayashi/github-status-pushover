FROM alpine:3.23.2@sha256:865b95f46d98cf867a156fe4a135ad3fe50d2056aa3f25ed31662dff6da4eb62

# uv
COPY --from=ghcr.io/astral-sh/uv:0.9.19@sha256:e614684f5327b44f2c3ef3958c5c121f4a8acb8ee5726207470526e42f4b49b8 /uv /uvx /bin/

RUN adduser --disabled-password app

USER app
WORKDIR /opt/github-status-pushover

COPY main.py pyproject.toml /opt/github-status-pushover/
ENTRYPOINT [ "uv", "run", "main.py" ]
