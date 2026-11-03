FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app
WORKDIR /app
# Versiones exactas del uv.lock (las mismas con las que corren las pruebas). Regenerar con:
#   uv export --frozen --no-dev --no-emit-project --no-hashes -o requirements.txt
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY gemela ./gemela
COPY migraciones ./migraciones
EXPOSE 8000 8001
