FROM python:3.12-slim
WORKDIR /app
COPY layer1_pipeline/requirements.txt /tmp/req1.txt
COPY layer3_analytics/requirements.txt /tmp/req3.txt
COPY layer4_dashboard/backend/requirements.txt /tmp/req4.txt
RUN pip install --no-cache-dir -r /tmp/req1.txt -r /tmp/req3.txt -r /tmp/req4.txt
COPY layer1_pipeline/ ./layer1_pipeline/
COPY layer3_analytics/ ./layer3_analytics/
COPY layer4_dashboard/backend/ ./layer4_dashboard/backend/
CMD ["uvicorn", "layer4_dashboard.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
