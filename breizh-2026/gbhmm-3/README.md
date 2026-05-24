# Glitch Better Have My Money 3/3

Ce challenge est le dernier d'une série de 3 challenges, réalisés par Philippe_Katerine, qui se suivent mais sont résolvables indépendamment les uns les autres. 
Ce troisième challenge est classé en difficile : les joueurs doivent brancher correctement l'adaptateur uart virtuel pour avoir un shell sur le device, le device boot (SPL => Uboot => firmware) mais affiche un login. 
L'objectif du challenge est de glitcher la puce mémoire SPI lors du boot afin de rentrer dans un shell uboot (https://www.trellix.com/assets/docs/atr-library/ms-glitching-uboot_als5.pdf / https://www.youtube.com/watch?v=F-G-7-qo7Xg).

Une fois que le glitch est effectué, le joueur doit dump le contenu de la mémoire (enlever le glitch, loader le firmware dans la RAM puis afficher le contenu avec md)
Ensuite md hex => bin par exemple avec : https://github.com/nmatt0/firmwaretools/blob/master/parse-uboot-dump.py

Ensuite le joueur utilise les offset présents dans le boot log pour parser l'image et extraire le squashfs et le jffs2.
Trouver la backdoor dans le squashfs et trouver la méthode d'authentification dans le jffs2 pour pouvoir se connecter au C2
de l'attaquant et récuperer le flag. 



