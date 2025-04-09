FROM python:3.13.3-alpine3.21@sha256:7162b2925f5b34b36deffa3430c7209e994046a5ad412f163eab8dca4a6a6e38

RUN adduser --disabled-password app \
    && apk --update-cache add py3-uv

USER app
WORKDIR /opt/github-status-pushover

COPY main.py pyproject.toml /opt/github-status-pushover/
ENTRYPOINT [ "uv", "run", "main.py" ]
