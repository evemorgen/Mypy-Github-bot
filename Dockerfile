FROM python:3.8-slim-buster

COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-root
COPY . .
RUN poetry install

CMD python3 app/__main__.py
