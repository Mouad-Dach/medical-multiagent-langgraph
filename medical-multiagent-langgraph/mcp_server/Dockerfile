FROM python:3.11-slim
WORKDIR /app
RUN pip install fastapi uvicorn httpx
COPY . .
EXPOSE 8001
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
