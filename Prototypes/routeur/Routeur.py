import socket
import threading


class Routeur:
    def __init__(self, host: str, port: int):
        self.__host = host
        self.__port = port
        self.router_socket_ecoute = None
        self.running = False

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

    def envoyer_message(self, ip_dist: str, port_dist: int, message: str) -> bool:
        try:
            #nouveau socket pour transférer le message au suivant
            socket_envoi = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_envoi.connect((ip_dist, port_dist))

            print(f"Transfert vers {ip_dist}:{port_dist}")
            socket_envoi.send(message.encode())
            socket_envoi.close()
            return True
        except ConnectionRefusedError:
            print(f"Erreur Impossible de transférer à {ip_dist}:{port_dist}")
            return False

    def demarrer_ecoute(self):
        """Lance le thread d'écoute"""
        self.running = True
        thread = threading.Thread(target=self._boucle_ecoute)
        thread.start()

    def _boucle_ecoute(self):
        try:
            self.router_socket_ecoute = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.router_socket_ecoute.bind((self.host, self.port))
            self.router_socket_ecoute.listen(5)
            print(f"Routeur actif sur {self.host}:{self.port}...")

            while self.running:
                # 1. On reçoit un paquet
                conn, addr = self.router_socket_ecoute.accept()
                donnee = conn.recv(2048)  # On lit un peu plus large (2048)

                if donnee:
                    paquet_complet = donnee.decode() #On décode le paquet
                    print(f"Paquet reçu de {addr} : {paquet_complet}")

                    if "|" in paquet_complet: # On attend un format : "IP_DESTINATION:PORT|MESSAGE"
                        instruction, vrai_message = paquet_complet.split("|", 1) # On coupe en deux au niveau du symbole "|"
                        # On récupère l'IP et le port
                        dest_ip, dest_port = instruction.split(":")
                        dest_port = int(dest_port)
                        self.envoyer_message(dest_ip, dest_port, vrai_message) #le routeur transfere le message
                    else:
                        print("[Erreur] Paquet mal formaté (pas de '|').")
                conn.close()

        except Exception as e:
            print(f"Erreur Routeur : {e}")