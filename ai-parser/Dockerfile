FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir fastapi uvicorn httpx pydantic
COPY app.py parser_engine_compat.py ./
CMD ["uvicorn", "app:api", "--host", "0.0.0.0", "--port", "8090"]
