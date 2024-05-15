FROM python:3.11.5-slim-bookworm

ARG ENV

ENV ENV=${ENV} \
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  POETRY_NO_INTERACTION=1 \
  POETRY_VIRTUALENVS_CREATE=false \
  POETRY_CACHE_DIR='/var/cache/pypoetry' \
  POETRY_HOME='/usr/local'
  POETRY_VERSION=1.8.2

RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /app
COPY poetry.lock pyproject.toml /app/

RUN poetry install $(test "$ENV" == production && echo "--only=main") --no-interaction --no-ansi

COPY backend ./backend
COPY frontend ./frontend
COPY main.py .

CMD ["sh", "-c", "alembic upgrade head && python ./main.py"]



