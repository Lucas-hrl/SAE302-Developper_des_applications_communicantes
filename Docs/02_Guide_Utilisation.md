# Guide d'Utilisation et Déploiement
## Projet : Routage en Oignon Distribué avec Anonymisation
**Date** : Décembre 2025 
**Auteur** : Lucas HERCHUEL 

> Ce document suppose que le système est **déjà installé et configuré**  
> (Python, environnement virtuel, dépendances, MariaDB, etc.).  
> Pour l’installation complète, se référer au **Guide d’Installation**.  
---

## Table des matières
1. [Architecture du Système](#architecture)
2. [Déploiement Multi-Machines](#multi-machines)
3. [Scénarios de Test](#scenarios)

---

## 1. Architecture du Système {#architecture}

### Diagramme d'Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      MASTER (Centraliser)                    │
│  • Écoute port 9016                                          │
│  • Gère annuaire routeurs                                    │
│  • Distribue clés publiques                                  │
│  • Base MariaDB : routeurs, logs                             │
│  • Interface PyQt6 : statut, routeurs, logs                 │
└─────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
    ROUTEUR 1             ROUTEUR 2            ROUTEUR 3
  ┌─────────────┐      ┌─────────────┐     ┌─────────────┐
  │ Port 8000   │      │ Port 8001   │     │ Port 8002   │
  │ Clé K1      │      │ Clé K2      │     │ Clé K3      │
  │ Thread Rx   │      │ Thread Rx   │     │ Thread Rx   │
  │ Déchiffre   │      │ Déchiffre   │     │ Déchiffre   │
  │ Transfère   │      │ Transfère   │     │ Transfère   │
  └─────────────┘      └─────────────┘     └─────────────┘
         │                    │                    │
         └────────────────────┴────────────────────┘
                              │
    ┌─────────────────────────┼─────────────────────────┐
    │                         │                         │
  CLIENT A                 CLIENT B                  CLIENT C
┌──────────────┐       ┌──────────────┐          ┌──────────────┐
│ Port 6016    │       │ Port 6017    │          │ Port 6018    │
│ Interface Qt │       │ Interface Qt │          │ Interface Qt │
│ Construis    │       │ Construis    │          │ Construis    │
│  oignon      │       │  oignon      │          │  oignon      │
│ Reçoit msg   │       │ Reçoit msg   │          │ Reçoit msg   │
└──────────────┘       └──────────────┘          └──────────────┘
```

- Le **Master** écoute sur un port (par défaut 9016) et gère l’annuaire des routeurs, leurs clés et les logs. 
- Chaque **Routeur** se connecte au Master, envoie une clé et écoute sur son propre port (8000, 8001, …).
- Chaque **Client** écoute sur un port différent (6016, 6017, …) et communique via les routeurs. 

### Flux de Communication (Oignon)

```
CLIENT A                    RÉSEAU                        DESTINATAIRE B
─────────────────────────────────────────────────────────────────────

[Message M]
    │
    ├─ Chiffrer avec K3:
    │  C3 = Enc(K3, "Adresse: DEST_B" + M)
    │
    ├─ Chiffrer avec K2:
    │  C2 = Enc(K2, "Adresse: Routeur3" + C3)
    │
    ├─ Chiffrer avec K1:
    │  C1 = Enc(K1, "Adresse: Routeur2" + C2)
    │
    └─ Envoyer C1 à Routeur1
             │
             └─→ ROUTEUR 1
                 • Déchiffre avec K1 (clé privée)
                 • Extrait "Adresse: Routeur2" et C2
                 • Envoie C2 à Routeur2
                        │
                        └─→ ROUTEUR 2
                            • Déchiffre avec K2
                            • Extrait "Adresse: Routeur3" et C3
                            • Envoie C3 à Routeur3
                                   │
                                   └─→ ROUTEUR 3
                                       • Déchiffre avec K3
                                       • Extrait "DEST_B" et M
                                       • Envoie M à Client B
                                              │
                                              └─→ CLIENT B reçoit M
                                                  Message anonyme livré
```


## 2. Déploiement Multi-Machines {#multi-machines}

Pour un déploiement réaliste avec plusieurs VMs ou machines physiques.


### 2.1 Étapes de Déploiement


#### Phase 1 : Lancer le Master

**Sur MACHINE 1** :
- Ouvrez un terminal dans le dossier du projet.
- Lancez l'interface Master sur le port 9016 (ou n'importe quel port voulu):
```bash
python interface_master.py 9016
```
- Une **fenêtre PyQt6** s'ouvre, cliquez sur **"Démarrer Serveur"**.

**Notez l'IP affichée** en haut de la fenêtre (ex: `192.168.1.50`).
Vérifiez que le Master est EN LIGNE 


#### Phase 2 : Lancer les Routeurs

**Sur MACHINE 2 et MACHINE 3** :

Les routeurs doivent se connecter au Master pour s'enregistrer.

1.  Ouvrez un terminal dans le repertoire du projet.
2.  Lancez un ou plusieurs routeurs en indiquant l'IP du Master :
    ```bash
    # Syntaxe : python routeur_crypt.py <IP_MASTER> <PORT_MASTER> <PORT_LOCAL_ROUTEUR>
    python routeur_crypt.py 192.168.1.50 9016 8000
    ```
3.  *Optionnel* : Pour lancer 3 routeurs d'un coup sur la même machine :
    ```bash
    # Syntaxe : python lancer_routeurs.py <IP_MASTER> <PORT_MASTER> <NB_ROUTEURS> [PORT_DEBUT]
    python lancer_routeurs.py 192.168.1.50 9016 3 8000
	```
	**Arguments** :
- `192.168.1.50` : IP du Master
- `9016` : Port du Master
- `3` : Nombre de routeurs à lancer
- `8000` : Port de départ (routeurs sur 8000, 8001, 8002)

4.  **Vérification** : Sur l'écran de la Machine 1 (Master), les routeurs doivent apparaître dans l'onglet "Routeurs" avec le statut **Active**.


#### Phase 3 : Lancer les Clients

**Sur MACHINE 4 et MACHINE 5** :
Lancer l'interface client:
```bash
python client.py
```

**Résultat attendu** :

→ Une **fenêtre PyQt6** s'ouvre avec :
- Section **"CONFIGURATION MASTER"**
- Section **"MON CLIENT"** (pour configurer le port d'écoute)
- Section **"ENVOI DE MESSAGE"**
- Zone de **logs** en bas

**Configuration du Client** :

**Étape 1 : Connexion au Master**

```
1. Vérifier que Master IP = 192.168.1.50 (l'IP de MACHINE 1) et Master Port = 9016 (le port de MACHINE 1)
2. Cliquer sur [Connexion]
3. Attendre que le status passe à "Connecté : N routeurs trouvés"
```

**Étape 2 : Démarrer l'Écoute Locale**

```
1. Aller à "MON CLIENT"
2. Définissez un port d'écoute
3. Cliquer sur [Démarrer Écoute]
```

**Important** : Sans l'écoute active, vous ne pourrez pas recevoir les réponses.

**Étape 3 : Configurer le Message**

```
1. IP Destinataire     : 192.168.1.xx  (Adresse IP du Destinataire)
2. Port Destinataire   : 6017       (port d'écoute du Destinataire)
3. Nombre de Sauts     : 3          (min 1, max nombre de routeurs)
4. Message             : "Bonjour monde anonyme !"
```

**Étape 4 : Envoyer le Message**

```
1. Cliquer sur [Envoyer]
2. Observer les logs pour voir la progression

```

---

## 3. Scénarios de Test {#scenarios}

### 3.1 Scénario 1 : Gestion de Panne

**Objectif** : Vérifier que le système détecte une panne routeur.

```bash
# Configuration initiale
# Terminal 1 : Master en cours d'exécution
# Terminal 2 : 3 routeurs en cours d'exécution (Ctrl+C ne pas appuyer)
# Terminal 3 : Client prêt à envoyer
```

**Procédure** :

1. Dans Terminal 2, **arrêter le Routeur 2** : appuyer sur `Ctrl+C` dans le processus du routeur du milieu

2. **Immédiatement**, depuis le client, essayer d'envoyer un message

3. **Observer** :
   - Terminal 2 : Le routeur arrêté ne reçoit plus rien
   - Master : Le routeur passe en DOWN dans l'interface (après timeout)
   - Client : Un message d'erreur apparaît ou relance avec une autre route
---

### 3.3 Scénario 3 : Envoi Multi-Client

**Objectif** : Vérifier que 2 clients peuvent envoyer des messages indépendamment.

```bash
# Terminal 1 : Master
python interface_master.py 9016

# Terminal 2 : 3 Routeurs
python lancer_routeurs.py 127.0.0.1 9016 3 8000

# Terminal 3 : Client A
python client.py
# Dans Client A : Port 6016, Envoyer "Message de A"

# Terminal 4 : Client B
python client.py
# Dans Client B : Port 6017, Envoyer "Message de B"
```

Les deux clients reçoivent les messages mutuellement, chacun via un chemin d'oignon différent.

---

