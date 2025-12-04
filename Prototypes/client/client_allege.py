import socket
import threading
import random
from crypt import CryptoSym


class Client:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.clientsocketecoute = None
        self.running = False

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    @host.setter
    def host(self, host: str):
        self._host = host

    @port.setter
    def port(self, port: int):
        self._port = port

    def __str__(self):
        return f"L'adresse ip du client est {self.host}, il écoute sur le port {self.port}"

    def envoyermessage(self, ipdist: str, portdist: int, message) -> bool:
        """
        Se connecte à un serveur distant et envoie un message.
        'message' peut être un str ou des bytes.
        """
        try:
            clientsocketenvoi = socket.socket()
            clientsocketenvoi.connect((ipdist, portdist))

            if isinstance(message, bytes):
                clientsocketenvoi.sendall(message)
            else:
                clientsocketenvoi.send(message.encode("latin1"))

            print(f"Message envoyé vers {ipdist}:{portdist}")
            clientsocketenvoi.close()
            return True
        except ConnectionRefusedError:
            print(f"Impossible de se connecter à {ipdist}:{portdist}")
            return False

    def demarrerecoute(self):
        """Lance le thread d'écoute pour ne pas bloquer le programme"""
        self.running = True
        thread = threading.Thread(target=self.boucleecoute)
        thread.start()

    def boucleecoute(self):
        """Méthode interne qui tourne en boucle pour accepter les connexions"""
        try:
            self.clientsocketecoute = socket.socket()
            self.clientsocketecoute.bind((self.host, self.port))
            self.clientsocketecoute.listen(2)
            print(f"Écoute démarrée sur {self.host}:{self.port}...")

            while self.running:
                conn, addr = self.clientsocketecoute.accept()
                donnee = conn.recv(1024)
                if donnee:
                    messagerecu = donnee.decode("latin1", errors="ignore")
                    print(f"Message reçu : {messagerecu}")
                conn.close()
        except Exception as e:
            print(f"Erreur lors de la mise en écoute : {e}")


def getip():
    """Récupère l'IP locale"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 1))
        ip = s.getsockname()[0]
    except:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def recupererlisterouteurs(ipmaster, portmaster):
    """Se connecte au Master et retourne une liste de tuples (ip, port, cle)."""
    try:
        s = socket.socket()
        s.connect((ipmaster, portmaster))
        s.send(b"LIST")
        data = s.recv(4096).decode("latin1")
        s.close()

        if data == "" or data == "vide":
            return []

        listepropre = []
        for item in data.split(","):
            ip, port, cle = item.split(":", 2)
            listepropre.append((ip, int(port), cle))
        return listepropre
    except Exception as e:
        print(f"Erreur connexion Master : {e}")
        return []


def construire_oignon(message_final: str, ip_dest: str, port_dest: int, circuit: list) -> bytes:
    """
    Construit le paquet "oignon" en chiffrant couche par couche.

    Format attendu par chaque routeur après déchiffrement :
      - "ip_suivante;port_suivant;reste"  -> relais
      - ";;message_final"                 -> destinataire final
    """
    # Couche la plus interne : message pour le destinataire final
    paquet = f";;{message_final}"

    # Construire les couches en partant du DERNIER routeur vers le PREMIER
    for i in range(len(circuit) - 1, -1, -1):
        ip_routeur, port_routeur, cle_routeur = circuit[i]

        # Déterminer la prochaine destination
        if i == len(circuit) - 1:
            ip_suivante, port_suivante = ip_dest, port_dest
        else:
            ip_suivante, port_suivante = circuit[i + 1][0], circuit[i + 1][1]

        # Construire et chiffrer la couche
        texte_clair = f"{ip_suivante};{port_suivante};{paquet}"
        crypto = CryptoSym(cle=cle_routeur)
        paquet_chiffre = crypto.chiffrer(texte_clair)
        paquet = paquet_chiffre.decode("latin1")

    return paquet.encode("latin1")


if __name__ == "__main__":
    moi = Client(getip(), 5000)
    moi.demarrerecoute()

    ipmaster = input("IP du master : ")
    portmaster = 9016

    while True:
        print("\n--- NOUVEAU MESSAGE ---")
        dest = input("IP Destinataire : ")
        msg = input("Message : ")

        routeursdispos = recupererlisterouteurs(ipmaster, portmaster)
        if not routeursdispos:
            print("Erreur : Aucun routeur disponible via le Master !")
            continue

        maxdispo = len(routeursdispos)
        print(f"{maxdispo} routeur(s) disponible(s) en ligne")

        try:
            nb = int(input(f"Par combien de routeurs passer ? (max {maxdispo}) : "))
            nb = max(1, min(nb, maxdispo))
        except:
            nb = 1

        circuit = random.sample(routeursdispos, nb)
        cheminstr = " -> ".join(r[0] for r in circuit)
        print(f"Circuit généré : Moi -> {cheminstr} -> Destinataire")

        paquet = construire_oignon(msg, dest, 5000, circuit)
        moi.envoyermessage(circuit[0][0], circuit[0][1], paquet)
