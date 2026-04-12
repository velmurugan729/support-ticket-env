FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip config set global.timeout 300 && \
    pip config set global.retries 10 && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

# Run standalone Gradio UI (replaces OpenEnv's default generic UI)
CMD ["python", "gradio_app.py"]
