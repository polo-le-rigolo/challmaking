# Under the sea OSINT Writeup

Pour résoudre ce challenge attardons nous d'abord sur l'énoncé avec de bien comprendre la tâche demandée et de ne louper aucuns détails. Le texte fourni est en breton et peut être traduit en ligne facilement en : 

"A la recherche de deux bateaux, près de l'île de Groix, les deux sont sous l'eau depuis 1917, le second une semaine après le premier." 

On note la date (1917) le lieu (île de Groix), et la cible (2 bateaux) et on a également l'information d'une semaine d'écart (pas très clair pour le moment). Dans le reste de l'énoncé on voit également un mot qui attire notre attention "SHomer". 

On a également une photo à notre disposition pour le challenge. Avec google reverse image search on tombe sur : 

https://memorial-national-des-marins.fr/marin/3675-tapir.html

Le lieu semble correspondre ("aux environs de Groix") mais également la date ainsi que la mention "une semaine" ("Il sauta sur une mine le 24 Mars 1917 une semaine après le Tasso"). 

Et enfin info très intéressante, on a la mention suivante "La position de cette épave est 47°39' 819N - 003°34' 133W. Elle est répertoriée par le Shom sous le n° 14573.112." 

En faisant quelques recherches sur le "shom" on tombe sur shom.fr "L'organisation des groupes hydrographiques et océanographiques du Shom est expressément prévue par l'arrêté du 27 juin 2007." Et également data.shom.fr : "Reference maritime geographic information portal." 

On peut aller dans l'onglet "Data catalog" et chercher "epave" ou "wreck" afin de load la carte des épaves. 
https://data.shom.fr/donnees#001=eyJjIjpbLTM5MDkyMy40MDU4ODQ1MDc2NCw2MDUzMTczLjI1MTIzNDk4OF0sInoiOjExLCJyIjowLCJsIjpbeyJ0eXBlIjoiSU5URVJOQUxfTEFZRVIiLCJpZGVudGlmaWVyIjoiRVBBVkVTX1BZUi1QTkdfV0xEXzM4NTdfV01UUyIsIm9wYWNpdHkiOjEsInZpc2liaWxpdHkiOnRydWV9LHsidHlwZSI6IklOVEVSTkFMX0xBWUVSIiwiaWRlbnRpZmllciI6IkZEQ19HRUJDT19QWVItUE5HXzM4NTdfV01UUyIsIm9wYWNpdHkiOjEsInZpc2liaWxpdHkiOnRydWV9XX0= 

On se rend ensuite aux coordonnées GPS données par le premier site pour le TAPIR et on trouve effectivement deux épaves côte à côte : le TASSO et le TAPIR. 

En cliquant sur les épaves on a plus d'informations et notammment un identifiant unique, l'orientation du TASSO et le nombre de tonnaux du TAPIR : NBCTF{TASSO_ FR000000138500001_270/90_TAPIR_FR000012804600001_200}

