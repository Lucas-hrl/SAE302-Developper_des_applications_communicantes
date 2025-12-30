# Guide d'Installation et Configuration
## Projet : Routage en Oignon Distribué avec Anonymisation
**Date** : Décembre 2025  
**Auteur** : Lucas HERCHUEL

---

## Table des matières
1. [Prérequis Système](#prérequis)
2. [Configuration Environnement Python](#python)
3. [Installation MariaDB](#mariadb)
4. [Installation du Projet](#installation)
5. [Vérification de l'Installation](#verification)
6. [Troubleshooting](#troubleshooting)

---

## 1. Prérequis Système {#prérequis}

Avant de commencer, vérifiez que vous disposez de :

### Logiciels requis

| Composant | Version | Remarques |
|-----------|---------|----------|
| Python | 3.9+ | Ajouter au PATH |
| MariaDB/MySQL | 10.5+ | Service en cours d'exécution |

### Installation des outils système

#### Sous Windows
```powershell
# Vérifier Python
python --version

# Vérifier MariaDB
mysql --version
```

#### Sous Linux (Debian/Ubuntu)
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Vérifier les versions
python3 --version
mariadb --version
```

#### Configuration Réseau

Pour un déploiement multi-machines :

- Les machines doivent être connectées au même réseau (Wi-Fi ou Ethernet).
- Pare-feu : Sur la machine Master, autorisez le port utilisé (TCP) en entrée si besoin. 
Sur les machines Routeurs, autorisez les ports que vous souhaitez utiliser.
- Vérifiez la connectivité avec une commande `ping <IP_DESTINATION>`.

---

## 2. Configuration Environnement Python {#python}

### 2.1 Création de l'Environnement Virtuel

L'utilisation d'un **environnement virtuel** (venv) est fortement recommandée pour isoler les dépendances du projet.

#### Sur Windows
```powershell
# Naviguez à la racine du projet
cd C:\Users\YourUser\Documents\SAE302-Developper_des_applications_communicantes

# Créer l'environnement virtuel
python -m venv env

# Activer l'environnement
.\env\Scripts\activate

# Vérifier l'activation (vous devez voir "(env)" en début de ligne)
# (env) C:\Users\YourUser\Documents\SAE302-Developper_des_applications_communicantes>
```

#### Sur Linux
```bash
# Naviguez à la racine du projet
cd ~/Documents/SAE302-Developper_des_applications_communicantes

# Créer l'environnement virtuel
python3 -m venv env

# Activer l'environnement
source env/bin/activate

# Vérifier l'activation
# (env) user@machine:~/Documents/SAE302-Developper_des_applications_communicantes$
```

### 2.2 Installation des Dépendances Python

Une fois l'environnement activé, installez les bibliothèques requises :

```bash
pip install -r requirements.txt
```

#### Vérification de l'installation
```bash
pip list

# Résultat attendu (parmi d'autres) :
# PyQt6                    6.6.0
# mysql-connector-python   8.2.0
```

---

## 3. Installation et Configuration MariaDB {#mariadb}

### 3.1 Installation du Serveur

#### Sous Windows

1. Téléchargez le **MSI Installer** depuis [mariadb.org](https://mariadb.org/download/)
2. Lancez `mariadb-XX.X.msi` (XX.X = version)
3. Dans l'assistant d'installation :
   - Acceptez les conditions
   - Choisissez le répertoire d'installation (par défaut : `C:\Program Files\MariaDB`)
   - **À l'étape « Services »** : cochez « Install as a service »
   - **Définissez un mot de passe root** (ex: `root123`) et notez-le
   - Cliquez « Next » jusqu'au bout

4. Après installation, MariaDB devrait démarrer automatiquement. Vérifiez dans les services Windows.

#### Sous Linux (Debian/Ubuntu)

```bash
# Mise à jour du répertoire de paquets
sudo apt update

# Installation du serveur
sudo apt install mariadb-server

# Démarrer le service
sudo systemctl start mariadb

# Vérifier le statut
sudo systemctl status mariadb

# (Optionnel) Lancer MariaDB au démarrage
sudo systemctl enable mariadb
```

### 3.2 Création de l'Utilisateur et des Droits d'Accès

Le script `master_crypt.py` se connecte par défaut avec l'utilisateur **`sae`** et mot de passe **`sae`**. Nous allons créer cet utilisateur avec les droits nécessaires.

#### Connexion au serveur MariaDB en tant que root

**Sous Windows :**
```bash
mysql -u root -p
# Entrez le mot de passe root que vous avez défini
```

**Sous Linux :**
```bash
mysql -u root -p
```

> **Note Linux** : Si `mysql -u root -p` retourne une erreur "Access denied", utilisez plutôt :
> ```bash
> sudo mariadb
> ```
> Cette commande contourne l'authentification par mot de passe en utilisant les droits root du système.

#### Exécution des commandes SQL

Une fois dans le prompt `MariaDB [(none)]>`, exécutez :

```sql
-- Créer l'utilisateur 'sae' avec mot de passe 'sae'
CREATE USER IF NOT EXISTS 'sae'@'localhost' IDENTIFIED BY 'sae';

-- Lui donner tous les droits (pour créer la base et les tables)
GRANT ALL PRIVILEGES ON *.* TO 'sae'@'localhost';

-- Appliquer les modifications
FLUSH PRIVILEGES;

-- Quitter
EXIT;
```

---

## 4. Installation du Projet {#installation}

### 4.1 Téléchargement du Code Source

#### Avec Git 
```bash
# Cloner le dépôt
git clone https://github.com/Lucas-hrl/SAE302-Developper_des_applications_communicantes
cd SAE302-Developper_des_applications_communicantes

# Optionnel : afficher le statut
git status
```

#### Manuellement
Téléchargez tous les fichiers `.py` et `requirements.txt` dans un dossier local.

### 4.2 Structure du Projet

Après téléchargement, votre structure doit ressembler à :

```
SAE302-Developper_des_applications_communicantes/
│
├── env/                              # Environnement virtuel (créé localement)
│   ├── lib/
│   ├── bin/ (ou Scripts/ sous Windows)
│   └── ...
│
├── master_crypt.py                   # Serveur Master (logique)
├── interface_master.py               # Master (interface graphique PyQt6)
│
├── routeur_crypt.py                  # Script d'un routeur
├── lancer_routeurs.py                # Script pour lancer N routeurs
│
├── client.py                         # Client (interface graphique PyQt6)
│
├── crypt.py                          # Fonctions de chiffrement XOR
│
├── requirements.txt                  # Dépendances Python
├── README.md                         # Documentation rapide
│
├── Docs/                             # Documentation complète
│   ├── 01_Installation_Guide.md
│   ├── 02_Guide_Utilisation.md
│   └── 03_Reponse_Cahier_Des_Charges.pdf
│
└── .git/                             # Métadonnées Git (si cloné)
```

### 4.3 Vérification des Fichiers Critiques

```bash
# Sous Linux/macOS
ls -la *.py requirements.txt

# Sous Windows PowerShell
Get-Item *.py, requirements.txt
```

Vous devez voir au minimum :
- `master_crypt.py`
- `interface_master.py`
- `routeur_crypt.py`
- `lancer_routeurs.py`
- `client.py`
- `crypt.py`
- `requirements.txt`

---

## 5. Vérification de l'Installation {#verification}

### 5.1 Test de Python et des Dépendances

Assurez-vous d'avoir suivi la section 2.2 (installation des dépendances), puis exécutez :

```bash
# Vous devez avoir l'environnement virtuel activé
# (env) doit apparaître au début de votre ligne de commande

python --version
# Python 3.9.X ou supérieur

python -c "import PyQt6; print('PyQt6 OK')"
python -c "import mysql.connector; print('MySQL connector OK')"
python -c "from crypt import *; print('crypt.py OK')"
```

Résultat attendu :
```
PyQt6 OK
MySQL connector OK
crypt.py OK
```

### 5.2 Test de Connexion à MariaDB

Reportez-vous à la section 3.2 pour la création de l'utilisateur `sae`, puis testez la connexion :

```bash
mysql -u sae -p
# Mot de passe : sae

# Une fois connecté, vérifier la version
SELECT VERSION();

# Voir les bases de données
SHOW DATABASES;
# Vous devriez voir quelques bases de données (information_schema, mysql, performance_schema, etc.)
# La base 'sae_routage_oignon_lh' sera créée automatiquement au premier lancement du Master.

# Quitter
EXIT;
```

---

## 6. Troubleshooting {#troubleshooting}

### Problème : `ModuleNotFoundError: No module named 'PyQt6'`

**Cause** : L'environnement virtuel n'est pas activé ou les dépendances ne sont pas installées.

**Solution** :
```bash
# Windows
.\env\Scripts\activate

# Linux/macOS
source env/bin/activate

# Réinstaller les dépendances
pip install -r requirements.txt
```

---

### Problème : `Error: Can't connect to MySQL server on 'localhost'`

**Causes possibles** :
1. MariaDB n'est pas en cours d'exécution
2. L'utilisateur `sae` n'existe pas
3. Mauvais mot de passe

**Solutions** :

```bash
# Windows : Vérifier le service
Get-Service MariaDB
# Devrait afficher : Status = Running

# Linux : Redémarrer le service
sudo systemctl restart mariadb

# Vérifier les identifiants
mysql -u sae -p
# Mot de passe : sae

# Si erreur « Access denied for user 'sae' »
# Recréez l'utilisateur en suivant la section 3.2
```

---

### Problème : `No module named 'mysql'`

**Cause** : `mysql-connector-python` n'est pas installé.

**Solution** :
```bash
# Avec l'environnement virtuel activé
pip install mysql-connector-python --upgrade
```

---

### Problème : Port déjà utilisé (`Address already in use`)

**Cause** : Un autre processus utilise le port (ex: 9016 pour le Master).

**Solution** :
```bash
# Windows : trouver le processus
netstat -ano | findstr :9016
taskkill /PID <PID> /F

# Linux/macOS : trouver et tuer le processus
lsof -i :9016
kill -9 <PID>

# Ou changer le port
python interface_master.py 9017  # nouveau port
```