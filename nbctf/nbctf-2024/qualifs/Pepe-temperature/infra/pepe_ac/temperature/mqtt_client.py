import paho.mqtt.client as mqtt
from django.core.cache import cache

MQTT_BROKER = 'mosquitto'
MQTT_PORT = 1883
MQTT_TOPIC = 'pepe/temperature'
MQTT_USERNAME = 'mosquitto'
MQTT_PASSWORD = '12345'

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    temperature = int(msg.payload.decode())
    cache.set('current_temperature', temperature)
    print(f"Received temperature: {temperature}")

def start_mqtt():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start() 

start_mqtt()

