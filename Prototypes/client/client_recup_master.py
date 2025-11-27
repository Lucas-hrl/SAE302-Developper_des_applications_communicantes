import socket
import threading
import random


class Client:
    def __init__(self, host: str, port: int):
        self.__host = host
        self.__port = port
        self.client_socket_ecoute = None  # Pour garder une trace du socket d'écoute
        self.running = False  # Pour pouvoir arrêter proprement le thread

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
        return f"L'adress ip du client est : {self.host}, il écoute sur le port:{self.port}"

    def envoyer_message(self, ip_dist: str, port_dist: int, message: str) -> bool:
        """Se connecte à un serveur distant et envoie un message"""
        try:
            client_socket_envoi = socket.socket()
            client_socket_envoi.connect((ip_dist, port_dist))
            print(f"Connecté avec succès à {ip_dist}:{port_dist}")
            client_socket_envoi.send(message.encode())
            print(f"Message envoyé")
            client_socket_envoi.close()
            return True
        except ConnectionRefusedError:
            print(f"Impossible de se connecter à {ip_dist}:{port_dist}")
            return False

    def demarrer_ecoute(self):
        """Lance le thread d'écoute pour ne pas bloquer le programme"""
        self.running = True
        thread = threading.Thread(target=self._boucle_ecoute)
        thread.start()

    def _boucle_ecoute(self):
        """Méthode interne qui tourne en boucle pour accepter les connexions"""
        try:
            self.client_socket_ecoute = socket.socket()
            self.client_socket_ecoute.bind((self.host, self.port))
            self.client_socket_ecoute.listen(2)  # 2 est le nombre de connexions en attente max
            print(f"Écoute démarrée sur {self.host}:{self.port}...")

            while self.running:
                conn, addr = self.client_socket_ecoute.accept()
                print(f"\nConnection acceptée de {addr}")

                donnee = conn.recv(1024)
                if donnee:
                    message_reçu = donnee.decode()
                    print(f"Message reçu : {message_reçu}")
                    print("Appuyez sur Entrée pour continuer...")
                conn.close()

        except Exception as e:
            print(f"Erreur lors de la mise en écoute : {e}")


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



def recuperer_liste_routeurs(ip_master, port_master):
    """Se connecte au Master, récupère la string et retourne une liste de tuples"""
    try:
        s = socket.socket()
        s.connect((ip_master, port_master))
        s.send(b"LIST")
        data = s.recv(4096).decode()
        s.close()

        if data == "vide":
            return []
        liste_propre = []
        for item in data.split(','):
            ip, port = item.split(':')
            liste_propre.append((ip, int(port)))

        return liste_propre

    except Exception as e:
        print(f"Erreur connexion Master: {e}")
        return []


if __name__ == "__main__":
    moi = Client(get_ip(), 5000)
    moi.demarrer_ecoute()

    ip_master = input("IP du master : ")
    port_master = 9016

    while True:
        print("\n--- NOUVEAU MESSAGE ---")
        dest = input("IP Destinataire : ")
        msg = input("Message : ")

        routeurs_dispos = recuperer_liste_routeurs(ip_master, port_master)

        if not routeurs_dispos:
            print("Erreur : Aucun routeur disponible via le Master !")
            continue

        max_dispo = len(routeurs_dispos)
        print(f"\n({max_dispo} routeurs disponibles en ligne)")

        try:
            nb = int(input(f"Par combien de routeurs passer ? (max {max_dispo}) : "))
            # Sécurité : on borne le chiffre entre 1 et le max disponible
            if nb > max_dispo: nb = max_dispo
            if nb < 1: nb = 1
        except:
            nb = 1  # Par défaut si l'utilisateur tape n'importe quoi

        # séléction aleatoire des routeurs
        circuit = random.sample(routeurs_dispos, nb)

        # Affichage du chemin
        chemin_str = " -> ".join([r[0] for r in circuit])
        print(f"Circuit généré : Moi -> {chemin_str} -> Destinataire")

        paquet = f"{dest}:5000|{msg}"

        # Emballage (sauf pour le premier routeur)
        for ip_r, port_r in reversed(circuit[1:]):
            paquet = f"{ip_r}:{port_r}|{paquet}"

        # envoi
        premier = circuit[0]
        moi.envoyer_message(premier[0], premier[1], paquet)