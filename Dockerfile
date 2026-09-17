FROM python:3.10-slim

WORKDIR /app

COPY requirements-server.txt .
RUN pip install --no-cache-dir -r requirements-server.txt

COPY . .

EXPOSE 8000

CMD ["python", "src/server.py", "--host", "0.0.0.0"]
