FROM python:3.13.5-alpine@sha256:d005934d99924944e826dc659c749b775965b21968b1ddb10732f738682db869

RUN adduser --disabled-password app \
    && apk --update-cache add py3-uv

USER app
WORKDIR /opt/github-status-pushover

COPY main.py pyproject.toml /opt/github-status-pushover/
ENTRYPOINT [ "uv", "run", "main.py" ]
