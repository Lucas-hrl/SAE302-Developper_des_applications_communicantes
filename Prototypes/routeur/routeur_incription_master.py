import socket
import threading
import time


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
                conn, addr = self.router_socket_ecoute.accept()
                donnee = conn.recv(2048)

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
                        print("Erreur Paquet mal formaté (pas de '|').")
                conn.close()

        except Exception as e:
            print(f"Erreur Routeur : {e}")

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


def s_inscrire_au_master(ip_master, port_master, mon_port):
    """Envoie un signal au Master pour dire qu'on est disponible"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip_master, port_master))
        msg = f"REGISTER|{mon_port}"
        s.send(msg.encode())

        reponse = s.recv(1024).decode()
        print(f"[Master] Réponse inscription : {reponse}")
        s.close()
    except Exception as e:
        print(f"[Erreur] Impossible de contacter le Master : {e}")


if __name__ == "__main__":
    ip = get_ip()
    port_ecoute = 8000  # Port du routeur

    r = Routeur(ip, port_ecoute)
    r.demarrer_ecoute()

    print("--- Inscription master ---")
    ip_master = input("Entrez l'IP du master : ")
    port_master = 9016

    s_inscrire_au_master(ip_master, port_master, port_ecoute)

    # Boucle pour garder le programme en vie
    while True:
        time.sleep(1)