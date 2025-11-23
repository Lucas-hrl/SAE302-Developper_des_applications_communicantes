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




# --- Programme pour tester ---
if __name__ == "__main__":

    # On demande l'IP de la machine actuelle pour savoir où écouter
    my_ip = input("Entrez l'IP de cette machine : ")
    my_port = 6000

    moi = Client(my_ip, my_port)
    moi.demarrer_ecoute() # On lance l'écoute
    time.sleep(1)  # Petite pause pour laisser le temps au thread de démarrer

    while True:
        choix = input("\nVoulez-vous envoyer un message ? (o/n) : ")
        if choix.lower() == 'o':
            target_ip = input("IP du destinataire : ")
            msg = input("Votre message : ")
            moi.envoyer_message(target_ip, 5000, msg)
        else:
            print("En attente de réception... (Ctrl+C pour quitter)")