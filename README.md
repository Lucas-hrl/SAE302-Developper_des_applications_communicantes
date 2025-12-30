# Routage en oignon distribué

Projet de SAE (BUT RT) visant à mettre en place une architecture distribuée avec routage en oignon : un client A envoie un message à un client B de façon anonyme via une chaîne de routeurs. 
Une vidéo de démonstration du projet est disponible via ce lien : https://youtu.be/wlzfgyH6P2k

## 1. Contenu du dépôt

- `master_crypt.py` : serveur Master (annuaire des routeurs + base MariaDB + logs).
- `routeur_crypt.py` : implémentation d’un routeur (génération de clé, écoute, déchiffrement, transfert, signalement de pannes).
- `client_allege.py` : client graphique PyQt6 (construction de l’oignon, envoi, réception).
- `lancer_routeurs.py` : script pour lancer plusieurs routeurs d’un coup.
- `interface_master.py` : interface graphique du Master.
- `crypt.py` : chiffrement symétrique XOR.
- `01_Installation_Guide.md` : guide d’installation détaillé.
- `02_Guide_Utilisation.md` : guide d’utilisation (scénarios de test).
- `03_Reponse_Cahier_Des_Charges.pdf` : réponse au cahier des charges + rapport de projet.

## 2. Comment démarrer ?

Pour les étapes complètes d’installation et de lancement (Python, dépendances, MariaDB, commandes), se référer à :

- `01_Installation_Guide.md`
- `02_Guide_Utilisation.md`
**Note** : Ces fichiers sont dans le dossier Docs

En résumé :

1. Installer l’environnement (Python + dépendances + MariaDB).
2. Lancer le Master.
3. Lancer quelques routeurs.
4. Lancer au moins deux clients pour tester l’envoi de messages anonymes.

## 3. Documentation

- **Installation** : `01_Installation_Guide.md`
- **Utilisation** : `02_Guide_Utilisation.md`
- **Technique et réponse au cahier des charges** : `03_Reponse_Cahier_Des_Charges.pdf`
