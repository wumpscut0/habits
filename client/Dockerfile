FROM python:3.12.3-alpine

ENV POETRY_VERSION=1.8.2
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV=/opt/poetry-venv
ENV POETRY_CACHE_DIR=/opt/.cache
ENV ROOT=/app
ENV PYTHONPATH=$ROOT


RUN apk add --no-cache bash

RUN python3 -m venv $POETRY_VENV \
    && $POETRY_VENV/bin/pip install -U pip setuptools \
    && $POETRY_VENV/bin/pip install poetry==${POETRY_VERSION}

ENV PATH="${PATH}:${POETRY_VENV}/bin"

WORKDIR $ROOT

COPY poetry.lock pyproject.toml ./
RUN poetry install

COPY . ./frontend
COPY wait-for-it.sh /usr/local/bin/wait-for-it.sh

RUN chmod +x /usr/local/bin/wait-for-it.sh

CMD ["wait-for-it.sh", "redis:6379", "--", "wait-for-it.sh", "api:8000", "--", "sh", "-c", "poetry run python frontend/main.py"]
