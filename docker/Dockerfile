FROM python:3.11-slim

WORKDIR /app

# Install with the API + LLM extras so the service can run audits and serve review UI.
COPY pyproject.toml README.md ./
COPY src ./src
COPY api ./api
COPY evals ./evals

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir ".[api,llm]"

EXPOSE 8000

# Overridden by docker-compose; sensible default for `docker run`.
CMD ["uvicorn", "api.app:default_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
