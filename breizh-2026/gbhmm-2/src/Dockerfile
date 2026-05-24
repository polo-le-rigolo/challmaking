FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY uart_bootlog.txt /uart_bootlog.txt
EXPOSE 5000
EXPOSE 1337

CMD ["python", "server.py"]
