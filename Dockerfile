FROM python:3.13.3-alpine3.21@sha256:f50e1ca5ac620527f8a8acc336cab074dc8a418231380cd6d9eafb4103931f91

RUN adduser --disabled-password app \
    && apk --update-cache add py3-uv

USER app
WORKDIR /opt/github-status-pushover

COPY main.py pyproject.toml /opt/github-status-pushover/
ENTRYPOINT [ "uv", "run", "main.py" ]
