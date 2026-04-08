FROM alpine:3.23.3@sha256:25109184c71bdad752c8312a8623239686a9a2071e8825f20acb8f2198c3f659

# uv
COPY --from=ghcr.io/astral-sh/uv:0.11.5@sha256:555ac94f9a22e656fc5f2ce5dfee13b04e94d099e46bb8dd3a73ec7263f2e484 /uv /uvx /bin/

RUN adduser --disabled-password app

USER app
WORKDIR /opt/github-status-pushover

COPY main.py pyproject.toml /opt/github-status-pushover/
ENTRYPOINT [ "uv", "run", "main.py" ]
