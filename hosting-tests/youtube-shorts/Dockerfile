FROM node:24.22.2-bookworm-slim AS javascript
FROM python:3.13-slim-bookworm
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PORT=10000
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY --from=javascript /usr/local/bin/node /usr/local/bin/node
WORKDIR /app
COPY requirements.txt .
RUN pip install --disable-pip-version-check --no-cache-dir -r requirements.txt
COPY app.py probe_worker.py ./
USER 10001:10001
EXPOSE 10000
CMD ["python", "app.py"]
