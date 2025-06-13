FROM python:3.13.5-alpine3.22@sha256:d49ec50fe9db96f85a908bac1d9e23cba93211a5721ae93b64ab1849f2370397

RUN adduser --disabled-password app \
    && apk --update-cache add py3-uv

USER app
WORKDIR /opt/github-status-pushover

COPY main.py pyproject.toml /opt/github-status-pushover/
ENTRYPOINT [ "uv", "run", "main.py" ]
