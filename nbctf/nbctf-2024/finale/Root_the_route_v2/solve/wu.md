### Étape 1 : Extraction du Contenu du Firmware

1. **Inspection du fichier firmware2.bin**: Utilisez `binwalk` pour examiner la structure de `firmware2.bin` et identifier d’éventuels systèmes de fichiers ou données compressées.   
    `binwalk firmware2.bin`
     
    - Comme dans root the router 1, on retrouve le bootloader (uboot), un kernel linux et un système de fichiers `SquashFS`. C'est ici que les fichiers du serveur web et le fichier `flag.txt` se trouvent.
    
1. **Extraction du firmware** : Utilisez `binwalk` avec l'option `-e` pour extraire le contenu de `firmware2.bin`.
    
    `binwalk -e firmware2.bin`
    

### Étape 2 : Localisation du Flag
   
    `cat var/www/flag.txt`
    
    `NBCTF{this_is_a_fake_flag} Bien joué pour l'extraction du système de fichiers ! Maintenant analysez le code source du serveur web et exploitez l'instance dynamique pour récupérer le vrai flag ;)`
    
---

### Étape 3 : Analyse des Fichiers du Serveur Web

1. Dans le dossier `html` se trouvent les fichiers du serveur web. Ici, vous trouverez plusieurs fichiers `.php`, y compris `login.php`, `diagnostics.php` et `admin_pannel.php`.

2. Ouvrez `login.php` pour identifier les identifiants de connexion. Vous découvrirez que l’utilisateur est `admin` et le mot de passe est `ensibs123`.
    
3. Examinez `diagnostics.php` pour identifier des vulnérabilités potentielles. Ce fichier utilise `shell_exec` pour exécuter une commande ping :
      
    `$output = shell_exec("ping -c 3 " . $target);`
    
    Comme l'entrée utilisateur (`$target`) est directement concaténée à la commande sans filtrage, cela ouvre la possibilité d’une **injection de commande**.


---

### Étape 4 : Exploitation de la Vulnérabilité

 Accédez à l’IP de l’application web et connectez-vous avec les identifiants trouvés dans `login.php` :
    
- **Nom d’utilisateur** : `admin`
- **Mot de passe** : `ensibs123`

Allez sur la page de diagnostic (`diagnostics.php`).
Dans le champ de saisie du test de ping, entrez une commande pour lire le fichier `flag.txt` : `127.0.0.1; cat /var/www/flag.txt`
        
La fonction `shell_exec` va exécuter `ping`, puis `cat /var/www/flag.txt`, affichant le contenu du flag dans la page Diagnostics