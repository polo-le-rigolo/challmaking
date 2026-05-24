
# Savoureux Filet

![yummy](images/yummy-nom-nom.gif)

## Identification

Plusieurs éléments dans l’énoncé permettent d’identifier rapidement la technologie utilisée :

- le nom *"Savoureux Filet"* =>  "mesh tasty/tastic"
- la mention Longfast => on tombe rapidement sur meshtastic sur les premiers liens en cherchant

**Meshtastic** est un protocole de communication (réseau maillé) basé sur LoRa.

---
## Analyse de la doc

En cherchant la documentation officielle, on tombe sur la section suivante :

https://meshtastic.org/docs/about/overview/encryption/comments/

On y trouve des informations précises sur le fonctionnement du chiffrement :

> We use AES256-CTR as a stream cypher (with zero padding on the last BLOCK) because it is well supported with hardware acceleration.
> Our AES key is 128 or 256 bits, shared as part of the 'Channel' specification.
> The node number concatenated with the packet number is used as the NONCE.
> The packet number is sent in cleartext with each packet.
> The node number can be derived from the "from" field of each packet.

---

Grâce à ces informations on a l'algorithme (**AES-CTR**) et le nonce composé l'id du paquet et de l'id du noeud expéditeur

Bonne nouvelle : ces deux valeurs sont présentes en clair dans le JSON (`packet_id` et `from`)

On a tout ce qu’il faut pour déchiffrer les paquets sauf la clé..
En cherchant un peu plus dans la documentation de meshtastic on tombe sur la clé par défaut utilisé en LongFast :

https://meshtastic.org/docs/configuration/radio/channels/

> Matching PSKs are required in order to communicate on the same channel with other devices.
> Example: If your device is using a channel with the default PSK of AQ== [...]

On a donc : PSK = `AQ==`

---

## Déchiffrement

Le processus est donc :

1. Décoder le payload (Base64)
2. Construire le nonce :
	`nonce = packet_id || from`
3. Initialiser AES en mode CTR avec :
- clé = PSK
- compteur basé sur le nonce
4. Déchiffrer le payload

Une fois les paquets déchiffrés on retrouve ce qui ressemble à l'alphabet phonétique de l'OTAN :

```
BravoZuluHotelCharlieTangoFoxtrot
Mikeechosierrahoteltangoalfasierratangoindiacharlie
Deltaechofoxtrotalfauniformlimatango
Kiloechoyankee
Indiasierra
Novemberoscartango
Sierraechocharlieuniformromeoecho
```

Un petit tour sur `dcode.fr` et on obtient :

=> `BZHCTF MESHTASTIC DEFAULT KEY IS NOT SECURE`

On suit les consignes (en majuscule, séparé par un underscore) et on obtient :

 **BZHCTF{MESHTASTIC_DEFAULT_KEY_IS_NOT_SECURE}**

