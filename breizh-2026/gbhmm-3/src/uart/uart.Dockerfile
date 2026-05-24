FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=root:root static ./static
COPY --chown=root:root templates ./templates
COPY --chown=root:root server.py .
COPY --chown=root:root uart_bootlog.txt /
COPY --chown=root:root firmware.bin /

EXPOSE 5000
EXPOSE 1337
CMD ["python", "server.py"]


