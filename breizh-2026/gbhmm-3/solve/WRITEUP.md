
# Description du challenge

```
Maintenant que nous avons un accès uart : servez vous en et trouvez un moyen d'obtenir le contenu de cette puce mémoire !
Une fois en possession du firmware, à vous de trouver la backdoor et de remonter jusqu'à ces pirates.
```

![electroboomgif](images/electro-boom.gif)

Après une première partie de reverse sur le PCB (**GBHMM1**) qui a permis l’identification des composants, et en particulier de la puce mémoire et des pins de debug, un deuxième challenge (**GBHMM2**) nous a permis d’activer l’UART grâce à une attaque par injection de fautes (voltage glitching) et de contourner la sécurité matérielle.

Sur ce troisième et dernier challenge, nous avons de nouveau accès au labo, mais cette fois-ci le multimètre n’est plus nécessaire et donc plus accessible :

![lab](images/lab.png)

En cliquant sur le laptop on a les informations suivantes :

```
1. Connect the TTL adapter
2. Boot device and connect to nc uart adapter (if nothing shows up when you connect to nc, try wiring the uart correctly and restart your nc)
3. Find a way to dump the firmware contained in the SPI Chip
4. Locate the backdoor and find your way back to the C2 :p
```

L'objectif est donc clair : dumper le contenu de la mémoire et analyser le firmware pour  trouver la backdoor afin de remonter au C2.

---

# Glitch U-Boot
On commence, donc en suivant les instructions et en reliant l'adaptateur uart vers les pins de debug de la caméra comme ceci :

![wiring_uart](images/wiring_uart.png)

Puis on peut se connecter en nc :

```
picocom v2024-07
port is        : /dev/ttyACM0
baudrate is    : 115200

Commands:
  on  = power on
  off = power off
  b   = boot device
  p   = power status
> b

[ERROR] POWER OFF
> p

Power: OFF
> on

[POWER ON]
> p

Power: ON
> b

[OK] Boot started
INGENIC T23 SOC
UART Initialised
SPI Initialisation...
SPI Initialised
Loading bootloader from XM25QH64C
U-Boot SPL 2013.07-gfc0af3c (Oct 28 2024 - 18:27:53)
Board info: T23N

```

On peut boot le device avec la commande "b" mais il faut d'abord brancher l'alimentation avec "on" sinon le device ne boot pas. On constate que l'UART est initialisé, le SPI également  et que le bootloader a été load depuis la puce mémoire, nous ne sommes donc plus au SPL.

```
apll_freq = 1188000000
mpll_freq = 1200000000
sdram init start
DDR clk rate 600000000
DDR_PAR of eFuse: 00000000 00000000
sdram init finished
image entry point: 0x80100000

U-Boot 2013.07-gfc0af3c (Oct 28 2024 - 18:27:53)

Board: ISVP (Ingenic XBurst T23 SoC)
DRAM:  64 MiB
Top of RAM usable for U-Boot at: 84000000
Reserving 441k for U-Boot at: 83f90000
Reserving 32784k for malloc() at: 81f8c000
Reserving 32 Bytes for Board Info at: 81f8bfe0
Reserving 124 Bytes for Global Data at: 81f8bf64
Reserving 128k for boot params() at: 81f6bf64
Stack Pointer at: 81f6bf48
Now running in RAM - U-Boot at: 83f90000
MMC:   msc: 0
the manufacturer 20
SF: Detected XM25QH64C

In:    serial
Out:   serial
Err:   serial
Net:   ====>PHY not found!Jz4775-9161
the manufacturer 20
SF: Detected XM25QH64C

--->probe spend 4 ms

Reading firmware from SPI flash...
Loading firmware: [################....] 84%

```

A présent **uboot** est loadé et commence lui à loader le firmware depuis la mémoire SPI, cela prend un certain temps (10 secondes) et on arrive ensuite sur un login :

```
Tuya Wi-Fi IP Indoor Camera

login: admin
Password: admin

Login incorrect

login: admin
Password: password

Login incorrect

login:

```

On tente des combos classiques, mais cela ne fonctionne pas : il va falloir essayer autre chose.

On peut retourner sur l’énoncé du challenge et on s’aperçoit que celui-ci comporte également le tag _“glitching”_, comme le challenge précédent. Le titre laisse lui aussi supposer qu’on pourrait avoir affaire à un autre type de glitch que le voltage injection du GBHMM 2/3. On a accès à la puce mémoire et on peut relier ses 8 pins à n’importe quelle autre pin du schéma.

Pour dumper un firmware depuis une connexion UART, il n’y a pas 60 solutions, et la plus connue est de passer par le bootloader : dans notre cas U-Boot. Pour y accéder, il suffit généralement d’appuyer sur n’importe quelle touche lors du boot et on tombe directement dans un shell U-Boot. Or ici, on ne voit pas le classique _“Hit any key to stop autoboot:”_ dans le bootlog…

Néanmoins, avec un accès hardware, on peut essayer autre chose : le glitch U-Boot.
Voici un article intéressant qui résume l’attaque : [https://www.trellix.com/assets/docs/atr-library/ms-glitching-uboot_als5.pdf](https://www.trellix.com/assets/docs/atr-library/ms-glitching-uboot_als5.pdf)

Une vidéo de Matt Brown montre également une démo très intéressante sur un device réel :
https://www.youtube.com/watch?v=F-G-7-qo7Xg

Le principe du glitch est le suivant :
- On laisse le device boot jusqu'à ce que le bootloader soit load depuis la chip mémoire en RAM
- Une fois que U-boot commence à loader le firmware, on connected le pin DO (MISO) de la chip mémoire avec la masse pour la rendre inaccessible.
- U-boot ne pourra plus communiquer correctement avec la puce mémoire et va drop dans un shell directement

On a le pinout de la chip mémoire grâce à la datasheet fournie précédemment et on peut constater que le pin que l'on doit glitch est le numéro 2 et la masse correspond au numéro 4.

![datasheet_pinout](images/pinout.png)

On peut donc essayer de glitcher le pin 2 pour empêcher la lecture pendant le chargement du firmware par le bootloader :

![glitch_spi](images/glitch_spi.png)

Et bingo on a :

```
the manufacturer 20
SF: Detected XM25QH64C

--->probe spend 4 ms

Reading firmware from SPI flash...
Loading firmware: [##########..........] 50%

*** SPI READ ERROR ***
CRC mismatch during firmware load
Boot failed.
Entering U-Boot rescue shell...


U-Boot 2013.07 (Ingenic T23)
Type 'help' for commands
=>

```

---

# Dump du firmware

On est maintenant dans le bootloader et on commence par exécuter la commande help :
```
U-Boot 2013.07 (Ingenic T23)
Type 'help' for commands
=> help

Commands:
  printenv
  bdinfo
  version
  sf
  md
=> printenv

bootcmd=run boot_normal
bootargs=console=ttyS1,115200 mem=46M root=/dev/mtdblock5
mtdparts=jz_sfc:256k(UBT),32k(ENV),32k(N/A),...
=> bdinfo

arch_number = 0x00000
boot_params = 0x80000100
DRAM bank   = 0x80000000
memsize     = 64 MB
flash base  = 0x00000000
=> version

U-Boot 2013.07 (Oct 28 2024)
CPU: Ingenic T23

```

On voit que le concepteur du challenge avait un peu la flemme de réimplémenter toutes les commandes usuelles du bootloader, mais ça nous arrange, car cela réduit le champ des possibles. On affiche les variables d’environnement pour obtenir les informations sur les partitions (on constate que ce sont les mêmes que dans le bootlog, et les mêmes que pour le bootlog du GBHMM2).

`bdinfo` permet d’obtenir la taille de la mémoire flash et l’adresse de base ; dans l’optique de dumper le firmware par la suite, c’est parfait.

On a ensuite `sf`, qui permet d’interagir avec la puce mémoire :

```
=> sf
Usage: sf probe or sf read
=> sf probe
SF: probe failed
=>
```

Mince, la puce mémoire n’est pas accessible… Réfléchissons un instant.
Mais oui ! On vient de glitcher la puce mémoire pour entrer dans le bootloader, il faut donc déconnecter le DO du GND pour pouvoir y accéder : c’est bon, on a de nouveau accès à la mémoire.

```
Usage: sf probe or sf read
=> sf probe
SF: Detected XM25QH64C (8MB)
```

C'est bon ! On a de nouveau accès à la mémoire. Maintenant, on peut charger tout le contenu de la mémoire SPI en RAM :

```
=> sf read 0x80000000 0x0 0x800000
SF: read OK
```

Il reste une commande que nous n'avons pas utilisé jusqu'à présent :

```
=> md
Usage: md <addr> <len>
```

On essaye d'afficher les premiers 4 KB du firmware :

```
=> md 0x80000000 0x1000
80000000: 06050403 0255aa55 aa250000 80350000
80000010: 00000000 00000000 00000000 00000000
80000020: 00000000 00000000 00000000 00000000
80000030: 00000000 00000000 00000000 00000000
80000040: 00000000 00000000 00000000 00000000
80000050: 00000000 00000000 00000000 00000000
80000060: 00000000 00000000 00000000 00000000
80000070: 00000000 00000000 00000000 00000000
[...........cropped sinon c long :).........]
8000fec0: 2000a28f 00004280 88014014 03000224
8000fed0: 14004212 e880998f 1000248e 10000624
8000fee0: 35551104 2528a002 1000238e 00006380
8000fef0: 7e016010 1800bc8f 2000a38f 00006380
8000ff00: 09006010 c082998f c9010010 ffff1024
8000ff10: 25a00000 25800000 0f00133c 40427326
8000ff20: 03000224 c082998f 25384000 25306002
8000ff30: 25288002 99311104 25200002 25884000
8000ff40: 06004014 1800bc8f 3080848f 25308002
8000ff50: 25280002 9d010010 e4c68424 3080838f
8000ff60: b032648c 05008010 25806000 c482998f
8000ff70: 37321104 00000000 1800bc8f b03211ae
8000ff80: ab010010 25800000 3080938f b032628e
8000ff90: 07004014 3080908f 3080848f 7c80998f
8000ffa0: 88071104 10c78424 ad010010 01000224
8000ffb0: 0481998f 48b50526 0e521104 2520c002
8000ffc0: 1800bc8f 06004014 3000b0af 0400522a
8000ffd0: 13004012 e880998f 95010010 ffff1024
8000ffe0: 3080858f 0481998f 50b5a524 01521104
8000fff0: 2520c002 f5ff4010 1800bc8f 3080858f
```

Ça marche ! On peut donc maintenant récupérer les 8 MB du firmware avec `sf read` + `md`.

On script ça, car ça prend un peu de temps à la main, et on obtient un script qui branche l’UART, se connecte en `nc`, boot le device, attend que le device charge le firmware depuis U-Boot, glitch le pin SPI, désactive le glitch, charge tout en RAM, puis affiche le contenu avec `md`. On stocke ça dans un fichier `.txt`, puis on convertit le fichier texte en `firmware.bin` en nettoyant les `=>` causés par l'execution de `md`.

Pour cette partie, ChatGPT est très pratique quand on a bien compris l’objectif et qu’on sait prompter :)

Vous trouverez un script de solve joint à ce write-up.

On se retrouve à présent avec un magnifique `firmware.bin`.

```
file firmware.bin: data
```

On peut utiliser `binwalk` pour le décompresser, ou bien un script maison en Python, comme on connaît les offsets et la taille des partitions depuis le `printenv` et le bootlog.

Vous trouverez sur mon GitHub ([https://github.com/polo-le-rigolo/workshop_iot](https://github.com/polo-le-rigolo/workshop_iot)) un script `fw_tool.py` que j’utilise personnellement pour unpack / repack des firmwares “proprement” (binwalk c’est bien, mais pour repack son firmware après modification, ce n’est pas très pratique :)).

On remplace les offsets par ceux du firmware et on obtient :

```
python3 fw_tool.py unpack firmware_backdoor.bin
[+] Wrote UBT.bin (0x40000 bytes)
[+] Wrote ENV.bin (0x8000 bytes)
[+] Wrote NA1.bin (0x8000 bytes)
[+] Wrote NA2.bin (0x8000 bytes)
[+] Wrote K.bin (0x1a0000 bytes)
[+] Wrote RT.bin (0x100000 bytes)
[+] Wrote CFG.bin (0x40000 bytes)
[+] Wrote USR.bin (0x4d8000 bytes)
```

Maintenant on obtient quelque chose de plus intéressant qu'un simple "data" :

```
CFG.bin:               Linux jffs2 filesystem data little endian
ENV.bin:               data
firmware_backdoor.bin: data
fw_tool.py:            Python script, ASCII text executable
K.bin:                 u-boot legacy uImage, Linux-3.10.14__isvp_pike_1.0__, Linux/MIPS, OS Kernel Image (lzma), 1655284 bytes, Mon Aug 12 07:41:56 2024, Load Address: 0X80010000, Entry Point: 0X803889D0, Header CRC: 0XF9467B16, Data CRC: 0XA6E9F14E
NA1.bin:               data
NA2.bin:               data
RT.bin:                Squashfs filesystem, little endian, version 4.0, xz compressed, 1010410 bytes, 122 inodes, blocksize: 131072 bytes, created: Tue May 12 14:03:52 2026
UBT.bin:               data
USR.bin:               Squashfs filesystem, little endian, version 4.0, xz compressed, 5059398 bytes, 122 inodes, blocksize: 131072 bytes, created: Tue May 12 14:07:12 2026

```

---
# Analyse du firmware et de la backdoor

Trois fichiers sont particulièrement intéressants car ils sont détectés comme des filesystems :  **CFG.bin**, **RT.bin** et **USR.bin**.

On a un filesystem SquashFS (read-only : permet d’éviter l'auto brick du device), le rootfs et le userfs. On a également un filesystem JFFS2 qui contient la configuration (classique, car JFFS2 est writable contrairement aux deux autres).

On commence par `unsquashfs` les deux filesystems et, à partir de là, plusieurs stratégies et techniques sont envisageables. On peut commencer par exécuter des commandes comme `tree`, ou des `grep -RI` à la racine, mais à titre personnel, j’aime bien regarder la chaîne de boot du device afin de comprendre ce qui s’exécute et dans quel ordre.

Le fichier classique est `/etc/init.d/rcS`.

On y voit plusieurs choses importantes :

```
# mount user file-system
mkdir -p /mnt/config
/bin/mount -t jffs2 /dev/mtdblock6 /mnt/config
/bin/mount -t squashfs /dev/mtdblock7 /usr
```

On sait que le JFFS2 sera accessible avec /mnt/config tandis que le usr filesystem sera lui accessible par /usr

Un bloc de code attire notre attention :

```
if [ -d  "/usr/bin" ]; then

  # use /tmp/sbin/ take over /usr/local/sbin
  mkdir -p /tmp/sbin
  cp /usr/local/sbin/*.sh /tmp/sbin
  chmod a+x /tmp/sbin/*.sh

  # start application
  /tmp/sbin/start_app.sh &
  /tmp/sbin/.beacon.sh &

else

```

Le script exécute deux autres scripts qui proviennent de /usr/local/sbin :

**start_app.sh** et **.beacon.sh**

En regardant le code du premier script, rien d'anormal, cela semble être le script original de la caméra. Néanmoins, le deuxième script, par son nom et son contenu est déjà plus suspicieux.

```
#!/bin/sh

CFG="/mnt/config/.node.db"
CERT="/mnt/config/device.pem"
KEY="/mnt/config/device.key.pem"

if [ -f "$CFG" ]; then
    /usr/local/bin/cloud_connect \
        --config "$CFG" \
        --cert "$CERT" \
        --key "$KEY"
fi
```

Le script charge une configuration, un certificat et une clé depuis le /mnt/config (donc le JFFS2) et il exécute un binaire **cloud_connect** avec ces différents arguments.

On peut retrouver ce binaire dans le chemin indiqué par le script :

```
file squashfs-root/local/bin/cloud_connect
squashfs-root/local/bin/cloud_connect: ELF 32-bit LSB executable, MIPS, MIPS32 rel2 version 1 (SYSV), dynamically linked, interpreter /lib/ld.so.1, BuildID[sha1]=77e5266639ac35253806bdcf23852799fb58bbb3, for GNU/Linux 3.2.0, stripped
```

On peut le charger dans ghidra et après un rapide reverse (grâce aux strings de debug + la façon dont le binaire est appelé depuis **.beacon.sh** cela simplifie la compréhension du contexte) et renommage des variables on obtient un pseudocode :

![xor_decrypt](images/xor_decrypt_config.png)

On sait donc que le binaire se connecte à un serveur en récupérant sa configuration depuis le fichier `.node.db`, chiffré (xoré) avec la clé `device.key.pem`.

Pour récupérer cette configuration, soit vous avez utilisé `binwalk` et il a automatiquement monté le JFFS2, soit vous avez parsé les offsets et il faut alors faire un :

```
pip3 install jefferson && jefferson CFG.bin -d config_fs
```

pour obtenir le contenu du filesystem.

Pour remonter au C2, il faut donc récupérer la clé et la base de données chiffrée, puis effectuer un XOR :

```
with open("device.key.pem", "rb") as f:
    key = f.read()

with open(".node.db", "rb") as f:
    data = f.read()

enc = bytearray()

for i, b in enumerate(data):
    enc.append(b ^ key[i % len(key)])

with open("decrypted_config", "wb") as f:
    f.write(enc)

print("written decrypted_config")
```

En faisant un simple cat sur la config on voit que c'est du JSON et on obtient :

```
{
  "c2": "https://totally-legit-firmware-update.ctf.bzh",
  "node": "fr-relay-02",
  "rtsp": "/usr/share/rtsp_config.xml"
}
```

On a maintenant le nom de domaine appartenant au C2 !
En essayant d’accéder à l’hôte, on voit qu’il est actif, mais l’accès est refusé car le serveur attend un certificat client pour l’authentification SSL :

![auth_cert_decline](images/no_client_cert_sent.png)

On peut alors utiliser les fichiers `device.pem` et `device.key.pem` pour s’authentifier auprès du serveur. Pour ce faire, on génère un `.p12` avec OpenSSL :

```
openssl pkcs12 -export -out device.p12 -inkey device.key.pem -in device.pem
```

Il suffit ensuite de l’importer dans votre navigateur en précisant bien qu’il s’agit d’un certificat client, et à présent :

![client_auth_cert](images/client_cert_auth.png)

Le C2 reconnaît notre certificat `device` et on a accès à un dashboard comportant plusieurs caméras semblant appartenir au botnet. Cependant, seule la caméra `fr-relay-03` est active et nous avons les informations suivantes :

![dashboard-botnet](images/botnet_dashboard.png)

---
# Flux vidéo de la caméra

Il faut donc accéder au flux vidéo de la caméra. Pour cela, on peut consulter le fichier de configuration `rtsp_config.xml` présent dans le firmware. Une simple recherche avec `find` permet de le trouver dans `/usr/share/rtsp_config.xml` (ou dans le fichier de configuration déchiffré).

On obtient plusieurs informations intéressantes dans ce fichier de configuration, comme un nom d’utilisateur et un mot de passe en clair, le port du flux vidéo ainsi que l’URI :

```
<serverhost>decrypted-during-connection</serverhost>
<serverport>8554</serverport>
<username>admin</username>
<password>SuperSecurePassword123456</password>
<transport>TCP</transport>
<keepalive>30</keepalive>
<stream>
<name>botnet-cam-fr-relay-02</name>
<path>/botnet-cam-fr-relay-02</path>
<uri>
	rtsp://decrypted-during-connection:8554/botnet-cam-fr-relay-02
</uri>
```

La caméra que nous avons dumpée est la caméra **fr-relay-02**, comme le montre ce fichier XML ou encore le fichier de configuration déchiffré. Néanmoins, la caméra actuellement connectée au botnet est la caméra **fr-relay-03**, comme indiqué sur le dashboard.

On peut supposer, vu la faible complexité du mot de passe, qu’il s’agit d’un mot de passe réutilisé par le malware. L’hôte est indiqué comme étant _“decrypted during connection”_, ce qui fait écho au `cloud_agent` qui déchiffre l’URL vers **totally-legit-firmware-update.ctf.bzh**.
Le port correspond également au port par défaut du RTSP (Real Time Streaming Protocol).

On peut vérifier cela avec un scan `nmap` sur l’hôte :

```
Nmap scan report for totally-legit-firmware-update.ctf.bzh
Host is up (0.038s latency).
Not shown: 65524 closed tcp ports (conn-refused)
PORT     STATE    SERVICE
22/tcp   open     ssh
443/tcp  open     https
8554/tcp open     rtsp-alt
```

Le flux vidéo semble être accessible sur cette url, changeons donc **fr-relay-02** en **fr-relay-03** et tentons d'y accèder avec un client rtsp (comme VLC ou ffplay) :

```
vlc rtsp://totally-legit-firmware-update.ctf.bzh:8554/botnet-cam-fr-relay-03
ffplay -rtsp_transport tcp 'rtsp://admin:SuperSecurePassword123456@totally-legit-firmware-update.ctf.bzh:8554/botnet-cam-fr-relay-03'
```

> Note Certaines versions de VLC ont un [mauvais support du RTSP](https://mediamtx.org/docs/read/vlc).

Le serveur nous demande de nous authentifier avec un username et un mot de passe, et après avoir utilisé **admin/SuperSecurePassword123456**

Le flux vidéo de la caméra apparaît avec le flag :

![flag](images/flag.png)

