"""
Définition de la classe Routeur.
Note : Nous utilisons ici un chiffrement symétrique (XOR) via la classe CryptoSym.
Le routeur génère sa clé au démarrage et l'envoie au Master.
"""

import socket
import threading
import sys
import time
from crypt import CryptoSym

class Routeur:
    def __init__(self, hote: str, port: int):
        self.__hote = hote
        self.__port = port
        self.socket_ecoute = None
        self.en_cours = False

        # Gestion de la cryptographie
        # On utilise une seule clé car c'est du symétrique (CryptoSym)
        self.crypto = None
        self.cle = None

    # --- Getters / Setters ---
    @property
    def hote(self):
        return self.__hote

    @property
    def port(self):
        return self.__port

    def envoyer_message(self, ip_dist: str, port_dist: int, message: bytes) -> bool:
        """
        Transfère le paquet au noeud suivant
        On ouvre un socket temporaire juste pour l'envoi
        """
        socket_envoi = None
        try:
            socket_envoi = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_envoi.connect((ip_dist, port_dist))

            print(f"Transfert du paquet vers {ip_dist}:{port_dist}")
            socket_envoi.sendall(message)
            return True
        except ConnectionRefusedError:
            print(f"Erreur : Impossible de joindre {ip_dist}:{port_dist}")
            self.signaler_panne(ip_dist, port_dist)
            return False
        except OSError as e:
            print(f"Erreur technique envoi : {e}")
            return False
        finally:
            if socket_envoi:
                socket_envoi.close()

    def demarrer_ecoute(self):
        """Lance le serveur d'écoute dans un thread dédié"""
        self.en_cours = True
        thread = threading.Thread(target=self.boucle_ecoute)
        thread.start()

    def definir_infos_master(self, ip, port):
        self.master_ip = ip
        self.master_port = port

    def signaler_panne(self, ip_hs, port_hs):
        if not hasattr(self, 'master_ip'): return
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.master_ip, self.master_port))
            msg = f"REPORT_DOWN;{ip_hs};{port_hs}"
            s.send(msg.encode("latin1"))
            s.close()
            print(f"[!] Panne signalée au Master pour {ip_hs}:{port_hs}")
        except OSError:
            pass

    def boucle_ecoute(self):
        """
        Boucle principale du serveur
        Attend les connexions et lance un thread par message reçu
        """
        try:
            self.socket_ecoute = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Option pour pouvoir relancer le script sans attendre le timeout système du port
            self.socket_ecoute.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            self.socket_ecoute.bind(("0.0.0.0", self.port))
            self.socket_ecoute.listen(5)

            # Le print est commenté pour ne pas polluer la console du script de lancement
            # print(f"Routeur en écoute sur {self.hote}:{self.port}")

            while self.en_cours:
                try:
                    conn, addr = self.socket_ecoute.accept()
                    # Gestion multi-thread pour ne pas bloquer les autres paquets
                    t = threading.Thread(target=self._traiter_connexion, args=(conn, addr))
                    t.start()
                except OSError:
                    break

        except OSError as e:
            print("Erreur Serveur :", e)
        finally:
            if self.socket_ecoute:
                self.socket_ecoute.close()

    def _traiter_connexion(self, conn, addr):
        """
        Logique de traitement Oignon :
        1. On reçoit
        2. On déchiffre avec notre clé symétrique
        3. On lit l'entête (IP;PORT)
        4. On transmet le reste
        """
        try:
            donnees = conn.recv(4096)
            if donnees:
                # Déchiffrement (Symétrique XOR)
                texte = self.crypto.dechiffrer(donnees)
                print(f"[Recu] Paquet de {addr}")

                # IP;PORT;PAYLOAD
                # Le payload peut contenir des ';', donc on limite le split à 2
                parties = texte.split(";", 2)

                if len(parties) == 3:
                    ipdest, portdest_str, reste = parties
                    ipdest = ipdest.strip()
                    portdest_str = portdest_str.strip()

                    if ipdest and portdest_str:
                        # Cas Relai : On transmet au suivant
                        portdest = int(portdest_str)
                        # On ré-encode en bytes car 'envoyer_message' attend des bytes
                        reste_bytes = reste.encode("latin1")
                        self.envoyer_message(ipdest, portdest, reste_bytes)
                    else:
                        # Cas Final : IP/Port vides, c'est pour nous
                        print(f"Message final déchiffré : {reste}")
                else:
                    print("Erreur : Format de paquet invalide.")
        except (ValueError, OSError) as e:
            print(f"Erreur traitement : {e}")
        finally:
            conn.close()

# --- Fonctions Utilitaires ---

def obtenir_ip():
    """Récupère l'ip de la machine (ex: 192.168.x.x)"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
    except OSError:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def s_inscrire_au_master(ipmaster, portmaster, monport, cle):
    """Envoie REGISTER au Master avec la clé symétrique"""
    s = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ipmaster, portmaster))

        msg = f"REGISTER;{monport};{cle}"
        s.send(msg.encode("latin1"))

        # On lit juste la confirmation pour être sûr que c'est bon
        s.recv(1024)
    except OSError as e:
        print(f"Erreur inscription Master ({ipmaster}): {e}")
        return False
    finally:
        if s: s.close()
    return True

# --- Main (Exécution manuelle) ---
if __name__ == "__main__":
    # Vérification des arguments pour éviter les erreurs de lancement
    if len(sys.argv) < 4:
        print("Usage : python routeur_crypt.py <IP_MASTER> <PORT_MASTER> <PORT_ROUTEUR>")
        sys.exit(1)

    ip_master = sys.argv[1]
    port_master = int(sys.argv[2])
    mon_port = int(sys.argv[3])
    mon_ip = obtenir_ip()

    # Initialisation du routeur
    r = Routeur(mon_ip, mon_port)

    # Génération de la clé unique (Symétrique)
    r.crypto = CryptoSym()
    r.cle = r.crypto.get_cle()

    print(f"Routeur manuel lancé sur {mon_ip}:{mon_port}")
    print(f"Clé symétrique : {r.cle}")

    r.demarrer_ecoute()

    # Inscription au Master pour qu'il connaisse notre clé
    s_inscrire_au_master(ip_master, port_master, mon_port, r.cle)
    
    # On sauvegarde les infos du Master pour pouvoir signaler les pannes plus tard
    r.definir_infos_master(ip_master, port_master)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        r.en_cours = False
        if r.socket_ecoute:
            r.socket_ecoute.close()