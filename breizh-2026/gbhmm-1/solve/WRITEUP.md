# Writeup GBHMM 1/3 : Datasheet

Ce premier challenge, classé en **très simple**, permet aux joueurs de se familiariser avec la lecture d’une datasheet.

Les deux fichiers PNG fournis servent uniquement à mettre en contexte le challenge (caméra connectée Wi-Fi). Il s’agit de clichés d’une vraie caméra, la même que celle utilisée pour le bootlog du challenge 2/3 et le firmware du challenge 3/3.

## Résolution du challenge

La résolution consiste à lire la datasheet et à répondre aux questions suivantes :

### 1. Nom du protocole de communication

**Question :** Quel est le nom du protocole de communication utilisé par la puce mémoire pour communiquer avec le MCU (Ingenic T23) ?  
**Réponse :** `SPI` (visible sur la photo du PCB ou dans le titre de la datasheet)

### 2. Capacité de stockage de la puce

**Question :** Quelle est la capacité de stockage de la puce (en MB) ?  
**Explication :** La datasheet indique 64 M-bits. Pour obtenir la valeur en mégaoctets (MB), il faut convertir les bits en octets : 64 / 8 = 8 MB.

### 3. Numéro du pinout correspondant à la masse

**Question :** Quel est le numéro du pinout correspondant à la masse ?  
**Explication :** À la page 9 de la datasheet, un schéma de la puce montre que le pin GND est le numéro **4**.

### 4. Protection d’écriture

**Question :** Lorsque la protection d’écriture est activée, quelle est la plus petite quantité de mémoire qui peut être protégée (en KB) ?
La protection d'écriture, en anglais WP (write protect) est détaillée page 12 : "a portion as small as a 4KB sector or the entire memory array can be hardware protected"


On a donc BZHCTF{SPI_8_4_4}