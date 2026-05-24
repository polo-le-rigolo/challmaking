from django.shortcuts import render
from django.core.cache import cache

def home(request):
    temperature = cache.get('current_temperature', 0)
    
    if temperature < 25:
        pepe_image = 'images/pepe_too_cold.jpeg'  
        flag = None
    elif 25 <= temperature <= 26:
        pepe_image = 'images/happy_pepe.gif'  
        flag = 'NBCTF{MQ77_S0_3ASY}'
    else:
        pepe_image = 'images/pepe_burning.gif'  
        flag = None
    
    return render(request, 'temperature/home.html', {
        'pepe_image': pepe_image,
        'flag': flag,
        'temperature': temperature  
    })


