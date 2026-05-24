FROM eclipse-mosquitto:latest

RUN mkdir -p /mosquitto/config /mosquitto/data /mosquitto/log

COPY ./config/mosquitto.conf /mosquitto/config/mosquitto.conf
COPY ./config/passwd /mosquitto/config/passwd

EXPOSE 1883

CMD ["mosquitto", "-c", "/mosquitto/config/mosquitto.conf"]
