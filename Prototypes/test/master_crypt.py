import socket
import threading
import time
import sys
import mysql.connector

# --- CONFIGURATION MARIADB ---
# À modifier selon ton installation (WAMP/XAMPP mettent souvent root/vide par défaut)
DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = ""


def get_ip():
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

        # NOTE: On remplace la liste 'self.registrerouteurs' par la BDD MariaDB
        # self.registrerouteurs = []  <-- Ancienne version mémoire

        # Sémaphore pour gérer l'accès concurrent à la base de données (Cours p.48)
        # Permet d'éviter que deux threads écrivent en même temps (Mutex)
        self.sem_bdd = threading.Semaphore(1)

        # Initialisation automatique : Crée la BDD et la Table au démarrage
        self._preparer_base_de_donnees()

    @property
    def host(self):
        return self.__host

    @property
    def port(self):
        return self.__port

    @host.setter
    def host(self, host: str):
        self.__host = host

    @port.setter
    def port(self, port: int):
        self.__port = port

    def __str__(self):
        return f"Master sur : {self.host}:{self.port}"

    def _preparer_base_de_donnees(self):
        """
        Crée la base de données 'projet_tor' et la table 'routeurs' si elles n'existent pas.
        Rend le code portable et facilite l'installation.
        """
        print("--- Vérification/Installation de la BDD MariaDB ---")
        try:
            # 1. Connexion au serveur SANS préciser de base (pour pouvoir la créer)
            conn = mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASS
            )
            cursor = conn.cursor()

            # 2. Création de la base
            cursor.execute("CREATE DATABASE IF NOT EXISTS projet_tor")

            # 3. Sélection de la base pour la suite
            cursor.execute("USE projet_tor")

            # 4. Création de la table avec les champs nécessaires
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
            print(">> Base de données prête.")
            conn.close()

        except mysql.connector.Error as err:
            print(f"ERREUR CRITIQUE MARIADB : {err}")
            print("Vérifiez que le service SQL (XAMPP/WAMP) est bien lancé.")
            sys.exit(1)

    def _get_db_connection(self):
        """Helper pour obtenir une connexion vers la base 'projet_tor'"""
        return mysql.connector.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASS, database="projet_tor"
        )

    def demarrer_ecoute(self):
        """Lance le thread d'écoute pour ne pas bloquer le programme"""
        self.running = True
        thread = threading.Thread(target=self._boucle_ecoute)
        thread.start()

    def _boucle_ecoute(self):
        """Boucle principale qui attend les connexions"""
        try:
            self.master_socket_ecoute = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Option pour réutiliser le port rapidement si on relance le script
            self.master_socket_ecoute.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            self.master_socket_ecoute.bind((self.host, self.port))
            self.master_socket_ecoute.listen(5)
            print(f"Master en ligne sur {self.host}:{self.port}")

            while self.running:
                try:
                    conn, addr = self.master_socket_ecoute.accept()
                    # Gestion multi-thread des demandes (Cours p.39)
                    threading.Thread(target=self._traiter_demande, args=(conn, addr)).start()
                except OSError:
                    break  # Interruption propre

        except Exception as e:
            print(f"Erreur Master : {e}")
        finally:
            if self.master_socket_ecoute:
                self.master_socket_ecoute.close()

    def _traiter_demande(self, conn, addr):
        """Analyse le message avec gestion des CLÉS PUBLIQUES et MARIADB"""
        try:
            ip_source = addr[0]
            # On augmente un peu la taille du buffer (4096) car les clés peuvent être longues
            message = conn.recv(4096).decode("latin1")

            if message.startswith("REGISTER"):
                try:
                    _, port_str, cle = message.split(";")
                    portrouteur = int(port_str)
                    ipsource = addr[0]

                    # --- DÉBUT SECTION CRITIQUE (Sémaphore) ---
                    # On verrouille l'accès à la BDD pour éviter les conflits d'écriture
                    self.sem_bdd.acquire()
                    db = None
                    try:
                        db = self._get_db_connection()
                        cursor = db.cursor()

                        # Vérification si le routeur existe déjà
                        cursor.execute("SELECT id FROM routeurs WHERE ip=%s AND port=%s", (ipsource, portrouteur))
                        exist = cursor.fetchone()

                        if not exist:
                            # Insertion du nouveau routeur
                            cursor.execute("INSERT INTO routeurs (ip, port, cle) VALUES (%s, %s, %s)",
                                           (ipsource, portrouteur, cle))
                            db.commit()
                            print("Routeur ajouté en BDD :", (ipsource, portrouteur))
                            conn.send(b"OK")
                        else:
                            # Mise à jour de la clé (au cas où il a redémarré)
                            cursor.execute("UPDATE routeurs SET cle=%s WHERE id=%s", (cle, exist[0]))
                            db.commit()
                            conn.send(b"ALREADYREGISTERED")

                    except mysql.connector.Error as e:
                        print("Erreur SQL REGISTER:", e)
                        conn.send(b"ERROR")
                    finally:
                        if db: db.close()
                        self.sem_bdd.release()  # Toujours libérer le sémaphore
                    # --- FIN SECTION CRITIQUE ---

                except Exception as e:
                    print("Erreur REGISTER:", e)
                    conn.send(b"ERROR")


            elif message == "LIST":
                # --- DÉBUT SECTION CRITIQUE (Sémaphore) ---
                # On protège aussi la lecture pour avoir une liste cohérente
                self.sem_bdd.acquire()
                db = None
                try:
                    db = self._get_db_connection()
                    cursor = db.cursor()

                    cursor.execute("SELECT ip, port, cle FROM routeurs")
                    lignes = cursor.fetchall()

                    if lignes:
                        # On reconstruit la chaine pour le client : ip:port:cle,ip:port:cle
                        reponse = ",".join(f"{r[0]}:{r[1]}:{r[2]}" for r in lignes)
                    else:
                        reponse = "EMPTY"

                    conn.send(reponse.encode("latin1"))

                except Exception as e:
                    print(f"Erreur LIST : {e}")
                    conn.send(b"ERROR")
                finally:
                    if db: db.close()
                    self.sem_bdd.release()
                # --- FIN SECTION CRITIQUE ---

        except Exception as e:
            print(f"Erreur traitement demande : {e}")
        finally:
            conn.close()


if __name__ == "__main__":
    mon_ip = get_ip()
    mon_port = 9016

    master = Master(mon_ip, mon_port)
    master.demarrer_ecoute()

    # Boucle infinie pour garder le programme ouvert
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nArrêt du Master...")
        master.running = False
        if master.master_socket_ecoute:
            master.master_socket_ecoute.close()