import socket
import threading
import time


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


if __name__ == "__main__":
    mon_ip = get_ip()
    print(f"Mon IP : {mon_ip}")

    # démarre le client en mode écoute (Port 5000 par défaut)
    moi = Client(mon_ip, 5000)
    moi.demarrer_ecoute()
    time.sleep(1)

    while True:
        print("\n--- CONSTRUCTION DE L'OIGNON ---")

        print("--- DESTINATAIRE FINAL ---")
        ip_finale = input("IP du Destinataire final : ")
        port_final = int(input("Port du Destinataire (ex: 5000) : "))
        message = input("Votre message secret : ")

        try:
            nbr_router = int(input("\nPar combien de routeurs voulez-vous passer ? "))
        except ValueError:
            nbr_router = 0

        routeurs = []
        for i in range(nbr_router):
            print(f"--- ROUTEUR N°{i + 1} ---")
            r_ip = input(f"IP du Routeur {i + 1} : ")
            r_port = int(input(f"Port du Routeur {i + 1} (ex: 8000) : "))
            routeurs.append((r_ip, r_port))

        if nbr_router > 0:
            paquet_a_envoyer = f"{ip_finale}:{port_final}|{message}"
            routeurs_intermediaires = routeurs[1:] # On prend tous les routeurs sauf le premier

            # On inverse la liste pour emballer de la fin vers le début
            for ip_r, port_r in reversed(routeurs_intermediaires):
                # On encapsule le paquet actuel dans une nouvelle couche
                paquet_a_envoyer = f"{ip_r}:{port_r}|{paquet_a_envoyer}"
                print(f"Encapsulation pour {ip_r}")

            # On envoie le paquet final au premier routeur de la liste
            first_router_ip, first_router_port = routeurs[0]
            print(f"\nEnvoi du paquet au premier routeur ({first_router_ip}:{first_router_port})")
            # print(f"Contenu du paquet : {paquet_a_envoyer}") # Décommenter pour voir l'oignon
            moi.envoyer_message(first_router_ip, first_router_port, paquet_a_envoyer)

        else:
            # Si 0 routeur, envoi direct
            print("Envoi direct sans routeur.")
            moi.envoyer_message(ip_finale, port_final, message)