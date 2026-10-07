FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
# Dependências de sistema para WeasyPrint (Cairo, Pango, GDK-PixBuf)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libffi8 \
    libgdk-pixbuf-2.0-0 \
    shared-mime-info \
 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt requirements-dev.txt ./
ARG INSTALAR_DEV=true
RUN pip install --no-cache-dir -r requirements.txt \
 && if [ "$INSTALAR_DEV" = "true" ]; then pip install --no-cache-dir -r requirements-dev.txt; fi
COPY . .
RUN useradd --create-home --uid 1000 app && chown -R app /app
USER app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
