FROM python:3.13.2-alpine3.21

USER app
WORKDIR /opt/github-status-pushover

COPY main.py pyproject.toml /opt/github-status-pushover/
RUN apk --update-cache add py3-uv
ENTRYPOINT [ "uv", "run", "main.py" ]
