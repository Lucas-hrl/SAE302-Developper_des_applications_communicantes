"""
Description :
Ce script est le serveur central (Annuaire).
- Il gère une base de données MariaDB pour stocker la liste des routeurs actifs.
- Il répond aux routeurs qui s'inscrivent (REGISTER).
- Il répond aux clients qui cherchent des noeuds (LIST).
- Il est multithreadé pour gérer plusieurs demandes en même temps.
"""

import socket
import threading
import time
import sys
import mysql.connector

# --- CONFIGURATION MARIADB STANDARD ---
# Configuration par défaut
DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = ""


def get_ip():
    """Petite fonction pour récupérer l'adresse IP LAN de la machine."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'


class Master:
    def __init__(self, host: str, port: int):
        self.__host = host
        self.__port = port
        self.master_socket_ecoute = None
        self.running = False

        # Sémaphore pour la BDD :
        # Comme on est en multithreading (plusieurs routeurs peuvent s'inscrire en même temps),
        # on utilise un sémaphore (ou Mutex) pour qu'un seul thread écrive dans la BDD à la fois.
        # Cela évite les conflits et les crashs SQL.
        self.sem_bdd = threading.Semaphore(1)

        # Au démarrage, on vérifie que la BDD existe, sinon on la crée.
        self._preparer_base_de_donnees()

    @property
    def host(self):
        return self.__host

    @property
    def port(self):
        return self.__port

    def _preparer_base_de_donnees(self):
        """
        Initialisation automatique de l'environnement SQL.
        Permet de rendre le projet portable : pas besoin d'importer un fichier .sql manuellement.
        """
        print("--- Initialisation de la Base de Données ---")
        conn = None
        try:
            # 1. Connexion au serveur sans préciser de base (car elle n'existe peut-être pas encore)
            conn = mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASS
            )
            cursor = conn.cursor()

            # 2. Création de la base 'sae_routage_oignon_lh'
            cursor.execute("CREATE DATABASE IF NOT EXISTS sae_routage_oignon_lh")

            # 3. On rentre dans la base
            cursor.execute("USE sae_routage_oignon_lh")

            # 4. Création de la table 'routeurs'
            # On stocke l'IP, le Port et la Clé (nécessaire pour le chiffrement oignon)
            cursor.execute("""
                           CREATE TABLE IF NOT EXISTS routeurs
                           (
                               id
                               INT
                               AUTO_INCREMENT
                               PRIMARY
                               KEY,
                               ip
                               VARCHAR
                           (
                               50
                           ),
                               port INT,
                               cle TEXT
                               )
                           """)

            # OPTIONNEL : On vide la table au lancement pour éviter d'avoir des routeurs "fantômes"
            # d'une session précédente qui n'existent plus.
            cursor.execute("TRUNCATE TABLE routeurs")

            print("BDD 'sae_routage_oignon_lh' et table 'routeurs' prêtes.")
            conn.commit()

        except mysql.connector.Error as err:
            print(f"ERREUR CRITIQUE SQL : {err}")
            print("Vérifiez que MariaDB est lancé et que l'user est bien 'root' sans mot de passe.")
            sys.exit(1)  # On arrête tout si pas de BDD
        finally:
            if conn: conn.close()

    def _get_db_connection(self):
        """Fonction utilitaire pour récupérer une connexion propre vers la base sae_routage_oignon_lh"""
        return mysql.connector.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASS, database="sae_routage_oignon_lh"
        )

    def demarrer_ecoute(self):
        """Lance le thread principal du serveur"""
        self.running = True
        # On utilise un thread pour ne pas bloquer le terminal
        thread = threading.Thread(target=self._boucle_ecoute)
        thread.start()

    def _boucle_ecoute(self):
        """Boucle d'attente des connexions (TCP)"""
        try:
            self.master_socket_ecoute = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Permet de relancer le Master immédiatement sans attendre le timeout du port
            self.master_socket_ecoute.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            self.master_socket_ecoute.bind((self.host, self.port))
            self.master_socket_ecoute.listen(10)  # File d'attente
            print(f"Master en écoute sur {self.host}:{self.port}")

            while self.running:
                try:
                    # accept() est bloquant, on attend un client
                    conn, addr = self.master_socket_ecoute.accept()
                    # À chaque client, on lance un thread dédié pour traiter sa demande
                    threading.Thread(target=self._traiter_demande, args=(conn, addr)).start()
                except OSError:
                    break  # On sort proprement si le socket est fermé

        except Exception as e:
            print(f"Erreur Serveur Master : {e}")
        finally:
            if self.master_socket_ecoute:
                self.master_socket_ecoute.close()

    def _traiter_demande(self, conn, addr):
        """
        Traite les messages reçus :
        - REGISTER : Un routeur s'inscrit
        - LIST : Un client demande la liste
        """
        try:
            # On lit le message (buffer large pour la clé)
            data = conn.recv(4096).decode("latin1")

            if not data: return

            # cas 1 : Inscription d'un routeur
            if data.startswith("REGISTER"):
                try:
                    # Format : REGISTER;PORT;CLE
                    parts = data.split(";")
                    port_routeur = int(parts[1])
                    cle_routeur = parts[2]
                    ip_routeur = addr[0]  # On prend l'IP réelle de la connexion

                    # Accès BDD
                    self.sem_bdd.acquire()
                    db = None
                    try:
                        db = self._get_db_connection()
                        cursor = db.cursor()

                        # On regarde si ce routeur existe déjà (IP + Port)
                        cursor.execute("SELECT id FROM routeurs WHERE ip=%s AND port=%s", (ip_routeur, port_routeur))
                        existe = cursor.fetchone()

                        if not existe:
                            cursor.execute("INSERT INTO routeurs (ip, port, cle) VALUES (%s, %s, %s)",
                                           (ip_routeur, port_routeur, cle_routeur))
                            db.commit()
                            print(f"Nouveau routeur inscrit : {ip_routeur}:{port_routeur}")
                            conn.send(b"OK")
                        else:
                            # S'il existe, on met à jour sa clé (cas de redémarrage)
                            cursor.execute("UPDATE routeurs SET cle=%s WHERE id=%s", (cle_routeur, existe[0]))
                            db.commit()
                            print(f"Routeur mis à jour : {ip_routeur}:{port_routeur}")
                            conn.send(b"UPDATED")

                    except mysql.connector.Error as e:
                        print(f"Erreur SQL : {e}")
                    finally:
                        if db: db.close()
                        self.sem_bdd.release()  # IMPORTANT : Toujours libérer le sémaphore

                except Exception as e:
                    print(f"Erreur protocole REGISTER : {e}")

            # cas 2 : Demande de la liste par un client
            elif data == "LIST":
                # Lecture BDD
                self.sem_bdd.acquire()
                db = None
                try:
                    db = self._get_db_connection()
                    cursor = db.cursor()

                    cursor.execute("SELECT ip, port, cle FROM routeurs")
                    lignes = cursor.fetchall()

                    if lignes:
                        # On formate la réponse : ip:port:cle,ip:port:cle...
                        liste_str = ",".join([f"{r[0]}:{r[1]}:{r[2]}" for r in lignes])
                        conn.send(liste_str.encode("latin1"))
                        print(f"[?] Liste envoyée à {addr[0]} ({len(lignes)} routeurs)")
                    else:
                        conn.send(b"EMPTY")

                except Exception as e:
                    print(f"Erreur SQL LIST : {e}")
                finally:
                    if db: db.close()
                    self.sem_bdd.release()

        except Exception as e:
            print(f"Erreur connexion client : {e}")
        finally:
            conn.close()


if __name__ == "__main__":
    # Ce bloc ne s'exécute que si on lance ce fichier directement (sans le script de lancement)
    # C'est une sécurité pour que le fichier soit autonome

    print("ATTENTION : Lancement manuel du Master !!!")
    print("Pour plus d'options, utilisez : python lancer_master.py")

    # On prend des valeurs par défaut simples
    ip_defaut = get_ip()
    port_defaut = 9016

    print(f"--- Démarrage Master sur {ip_defaut}:{port_defaut} ---")

    master = Master(ip_defaut, port_defaut)
    master.demarrer_ecoute()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        master.running = False
        if master.master_socket_ecoute:
            master.master_socket_ecoute.close()