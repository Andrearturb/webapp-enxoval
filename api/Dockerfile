FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt requirements-dev.txt ./
ARG INSTALAR_DEV=true
RUN pip install --no-cache-dir -r requirements.txt \
 && if [ "$INSTALAR_DEV" = "true" ]; then pip install --no-cache-dir -r requirements-dev.txt; fi
COPY . .
RUN useradd --create-home --uid 1000 app && chown -R app /app
USER app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
