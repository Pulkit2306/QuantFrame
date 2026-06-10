FROM python:3.12-slim
WORKDIR /app
COPY layer1_pipeline/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY layer1_pipeline/ ./layer1_pipeline/
CMD ["python", "-m", "layer1_pipeline", "ingest"]
