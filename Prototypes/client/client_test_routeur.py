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
            client_socket_envoi.close()  # Ajout conseillé pour fermer proprement après envoi
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
            self.client_socket_ecoute.listen(2)  # 2 est le nombre de connexions en attente max (backlog)
            print(f"Écoute démarrée sur {self.host}:{self.port}...")

            while self.running:
                conn, addr = self.client_socket_ecoute.accept()
                print(f"\n[EVENT] Connection acceptée de {addr}")

                donnee = conn.recv(1024)
                if donnee:
                    message_reçu = donnee.decode()
                    print(f"[EVENT] Message reçu : {message_reçu}")
                    print("Appuyez sur Entrée pour continuer...")  # Juste pour l'affichage
                conn.close()

        except Exception as e:
            print(f"Erreur lors de la mise en écoute : {e}")


def get_ip():
    # On crée un socket pour tester la route vers internet
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  #AF_INET car ipv4 et SOCK_DGRAM car UDP
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

    #démarre le client en mode écoute (Port 5000 par défaut)
    moi = Client(mon_ip, 5000)
    moi.demarrer_ecoute()
    time.sleep(1)

    while True:
        print("\n--- NOUVEL ENVOI ---")

        ip_routeur = input("IP du Routeur : ")
        port_routeur = int(input("Port du Routeur (ex: 8000) : "))

        ip_finale = input("IP du Destinataire final : ")
        port_final = int(input("Port du Destinataire (ex: 5000) : "))

        message = input("Votre message : ")

        # On colle l'adresse finale devant le message avec un séparateur "|"
        # Le routeur va lire ce qu'il y a avant le "|" pour savoir où envoyer
        paquet_complet = f"{ip_finale}:{port_final}|{message}"

        print(f"Envoi du paquet au routeur ({ip_routeur}:{port_routeur})...")

        moi.envoyer_message(ip_routeur, port_routeur, paquet_complet)