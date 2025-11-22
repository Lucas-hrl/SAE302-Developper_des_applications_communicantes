import socket
import threading


class Client:
    def __init__(self,host:str,port:int):
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
    def host(self,host:str):
        self.__host = host
    @port.setter
    def port(self,port:int):
        self.__port = port

    def __str__(self):
        return f"L'adress ip du client est : {self.host}, il écoute sur le port:{self.port}"

    def envoyer_message(self,ip_dist:str,port_dist:int,message:str)->bool:
        """Se connecte à un serveur distant et envoie un message"""
        try:
            client_socket_envoi = socket.socket()
            client_socket_envoi.connect((ip_dist,port_dist))
            print(f"Connecté avec succès à {ip_dist}:{port_dist}")
            client_socket_envoi.send(message.encode())
            print(f"Message envoyé")
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
            self.client_socket_ecoute.bind((self.host,self.port))
            self.client_socket_ecoute.listen(2) # 2 est le nombre de connexions en attente max (backlog)
            print(f"Écoute démarrée sur {self.host}:{self.port}...")

            while self.running:
                conn, addr = self.client_socket_ecoute.accept()
                print(f"Connection accepté de {addr}")

                donnee = conn.recv(1024)
                if donnee:
                    message_reçu = donnee.decode()
                    print(f"Message reçu : {message_reçu}")
                conn.close()

        except Exception as e:
            print(f"Erreur lors de la mise en écoute : {e}")






