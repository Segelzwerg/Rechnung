ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION} AS poetry
RUN pip install poetry
WORKDIR /app
COPY invoice ./invoice/
COPY rechnung ./rechnung/
COPY static/ ./static/
COPY templates/ ./templates/
COPY README.md ./README.md
COPY pyproject.toml poetry.lock ./
RUN poetry build -f wheel -n
LABEL authors="Segelzwerg"

FROM python:${PYTHON_VERSION}-slim
WORKDIR /app
COPY --from=poetry /app/dist/ .
COPY entrypoint.sh .
RUN apt-get update && \
    apt-get install -y --no-install-recommends gettext && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir --find-links . rechnung
CMD ["/app/entrypoint.sh"]
