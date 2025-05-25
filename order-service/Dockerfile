FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV MONGO=mongodb://mongo:27017
ENV AUTH_URL=http://auth:8000
ENV CATALOG_URL=http://catalog:8000
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
