# Challenge Write-Up: Pepe's Temperature Control

## Description

You are given the source directory of a Django project. Your task is to help Pepe feel more comfortable by adjusting the temperature. By inspecting the source files, you discover that the temperature is managed through an MQTT broker running locally on port 1883.

## Steps to Solve

1. **Examine `mqtt_client.py`:**
   - This file contains the MQTT broker details:
     ```python
     MQTT_BROKER = 'mosquitto'
     MQTT_PORT = 1883
     MQTT_TOPIC = 'pepe/temperature'
     MQTT_USERNAME = 'mosquitto'
     MQTT_PASSWORD = '12345'
     ```
   - These credentials and topic information are necessary to interact with the MQTT broker.

2. **Understand Temperature Conditions:**
   - The `views.py` file shows that the temperature influences which image of Pepe is displayed:
     - Less than 25°C: Cold Pepe
     - Between 25°C and 26°C: Happy Pepe (and flag displayed)
     - Greater than 26°C: Burning Pepe

3. **Send Correct Temperature:**
   - Use an MQTT client to connect to the broker with the provided credentials (`mosquitto` / `12345`).
   - Publish a temperature value of `25` or `26` to the topic `pepe/temperature`.

4. **Retrieve the Flag:**
   - When the temperature is set between `25°C` and `26°C`, Pepe will display a happy image and provide the flag.

## Example Commands

To publish the correct temperature, use the following commands in an MQTT client:

```
apt install mosquitto-clients

mosquitto_pub -t pepe/temperature -h instance_addr -m 25 -u mosquitto -P 12345
```


