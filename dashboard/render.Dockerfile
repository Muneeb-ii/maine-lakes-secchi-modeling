FROM node:20-alpine AS frontend-build

WORKDIR /app

COPY dashboard/app/frontend/package*.json ./
RUN npm ci

COPY dashboard/app/frontend ./
ENV VITE_API_URL=/api
RUN npm run build

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MODEL_ARTIFACTS_PATH=/app/artifacts/models \
    PORT=10000

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx gettext-base \
    && rm -rf /var/lib/apt/lists/*

COPY dashboard/app/backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY dashboard/app/backend /app/dashboard/app/backend
COPY artifacts/models /app/artifacts/models
COPY --from=frontend-build /app/dist /usr/share/nginx/html
COPY dashboard/nginx.render.conf.template /etc/nginx/templates/default.conf.template
COPY dashboard/start-render.sh /app/start-render.sh

RUN chmod +x /app/start-render.sh

EXPOSE 10000

CMD ["/app/start-render.sh"]
