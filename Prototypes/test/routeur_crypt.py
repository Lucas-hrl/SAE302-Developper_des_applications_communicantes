import socket
import threading
import time
from crypt import  CryptoSym


class Routeur:
    def __init__(self, host: str, port: int):
        self.__host = host
        self.__port = port
        self.router_socket_ecoute = None
        self.running = False
        self.cle_publique = None
        self.cle_privee = None

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
        return f"Le Routeur est sur l'IP : {self.host}, il écoute sur le port : {self.port}"

    def envoyer_message(self, ip_dist: str, port_dist: int, message: bytes) -> bool:
        """
        Envoie des bytes vers ip_dist:port_dist.
        Le 'message' ici est le reste du paquet (encore chiffré ou message final).
        """
        try:
            socket_envoi = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_envoi.connect((ip_dist, port_dist))

            print(f"Transfert vers {ip_dist}:{port_dist}")
            socket_envoi.sendall(message)
            socket_envoi.close()
            return True
        except ConnectionRefusedError:
            print(f"Erreur Impossible de transférer à {ip_dist}:{port_dist}")
            return False

    def demarrer_ecoute(self):
        """Lance le thread d'écoute"""


        self.running = True
        thread = threading.Thread(target=self.boucleecoute)
        thread.start()

    def boucleecoute(self):
        """
        Logique:
        - reçoit des bytes
        - déchiffre avec self.crypto
        - attend un format "ip;port;reste"
          * si ip et port non vides -> transfert à ip:port avec 'reste' comme bytes
          * sinon -> on considère que c'est le destinataire final et on affiche le message
        """
        try:
            self.router_socket_ecoute = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.router_socket_ecoute.bind((self.host, self.port))
            self.router_socket_ecoute.listen(5)
            print("Routeur actif sur", self.host, self.port, "...")

            while self.running:
                conn, addr = self.router_socket_ecoute.accept()
                donnees = conn.recv(2048)
                if donnees:
                    # 1) déchiffrer avec la clé de ce routeur
                    texte = self.crypto.dechiffrer(donnees)
                    print("Paquet déchiffré reçu de", addr, ":", texte)

                    # 2) essayer de parser "ip;port;reste"
                    parties = texte.split(";", 2)
                    if len(parties) == 3:
                        ipdest, portdest_str, reste = parties

                        ipdest = ipdest.strip()
                        portdest_str = portdest_str.strip()

                        if ipdest and portdest_str:
                            # encore un saut à faire
                            portdest = int(portdest_str)
                            # 'reste' doit redevenir des bytes pour le prochain
                            reste_bytes = reste.encode("latin1")
                            self.envoyer_message(ipdest, portdest, reste_bytes)
                        else:
                            # pas d'ip / port -> on est le destinataire final
                            print("Message final arrivé à ce routeur :", reste)
                    else:
                        print("Format inconnu après déchiffrement:", texte)
                conn.close()
        except Exception as e:
            print("Erreur :", e)


def get_ip():
    # On crée un socket pour tester la route vers internet
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # AF_INET car ipv4 et SOCK_DGRAM car UDP
    try:
        # On fait semblant de se connecter à Google (8.8.8.8)
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
    except:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


def sinscrireaumaster(ipmaster, portmaster, monport, cle):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ipmaster, portmaster))
        msg = f"REGISTER;{monport};{cle}"
        s.send(msg.encode("latin1"))
        reponse = s.recv(1024).decode("latin1")
        print("Master - Réponse inscription :", reponse)
        s.close()
    except Exception as e:
        print("Erreur : Impossible de contacter le Master", e)



if __name__ == "__main__":
    ip = get_ip()
    portecoute = 8000
    r = Routeur(ip, portecoute)

    # Créer l’objet de chiffrement + clé aléatoire
    r.crypto = CryptoSym()
    cle_routeur = r.crypto.get_cle()
    print("Clé de ce routeur :", cle_routeur)

    r.demarrer_ecoute()

    print("--- Inscription master ---")
    ipmaster = input("Entrez l'IP du master : ")
    portmaster = 9016
    sinscrireaumaster(ipmaster, portmaster, portecoute, cle_routeur)

    import time
    while True:
        time.sleep(1)