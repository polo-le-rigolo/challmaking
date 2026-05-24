from django.apps import AppConfig

class TemperatureConfig(AppConfig):
    name = 'temperature'

    def ready(self):
        from . import mqtt_client
    
