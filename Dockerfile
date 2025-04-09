FROM python:3.13.3-alpine3.21@sha256:7ce9864f2f4181df6ad32ea6625fb80bee3031d679faec6015623525ba753706

RUN adduser --disabled-password app \
    && apk --update-cache add py3-uv

USER app
WORKDIR /opt/github-status-pushover

COPY main.py pyproject.toml /opt/github-status-pushover/
ENTRYPOINT [ "uv", "run", "main.py" ]
