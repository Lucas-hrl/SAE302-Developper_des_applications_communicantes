import socket
import threading
import time


def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'


class Master:
    def __init__(self, host: str, port: int):
        self.__host = host
        self.__port = port
        self.master_socket_ecoute = None
        self.running = False
        self.registre_routeurs = [] # Cette liste va stocker les tuples (ip, port) des routeurs inscrits

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
        return f"MASTER sur : {self.host}:{self.port}"

    def demarrer_ecoute(self):
        """Lance le thread d'écoute pour ne pas bloquer le programme"""
        self.running = True
        thread = threading.Thread(target=self._boucle_ecoute)
        thread.start()

    def _boucle_ecoute(self):
        """Boucle principale qui attend les connexions"""
        try:
            self.master_socket_ecoute = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.master_socket_ecoute.bind((self.host, self.port))
            self.master_socket_ecoute.listen(5)
            print(f"[Master] Annuaire en ligne sur {self.host}:{self.port}")

            while self.running:
                conn, addr = self.master_socket_ecoute.accept()
                threading.Thread(target=self._traiter_demande, args=(conn, addr)).start()

        except Exception as e:
            print(f"Erreur Master : {e}")

    def _traiter_demande(self, conn, addr):
        """Analyse le message : Est-ce une inscription d'un routeur ou une demande de liste d'un client ?"""
        try:
            ip_source = addr[0]
            message = conn.recv(1024).decode()

            # CAS 1 : Un routeur veut s'inscrire
            # Format attendu : "REGISTER|8000"
            if message.startswith("REGISTER"):
                _, port_routeur_str = message.split("|")
                port_routeur = int(port_routeur_str)

                # On crée le tuple (IP, PORT)
                nouveau_noeud = (ip_source, port_routeur)

                # On l'ajoute seulement s'il n'est pas déjà dedans
                if nouveau_noeud not in self.registre_routeurs:
                    self.registre_routeurs.append(nouveau_noeud)
                    print(f"Routeur ajouté : {ip_source}:{port_routeur}")
                    conn.send("OK".encode())
                else:
                    print(f"Le routeur {ip_source} est déjà inscrit.")
                    conn.send("ALREADY_REGISTERED".encode())

            # CAS 2 : Un client veut la liste des routeurs
            elif message == "LIST":
                print(f"Envoi de la liste à {ip_source}")

                # On transforme la liste [(ip, port), (ip, port)] en string "ip:port,ip:port"
                # Ex: "192.168.1.15:8000,192.168.1.20:8000"
                if self.registre_routeurs:
                    reponse = ",".join([f"{ip}:{port}" for ip, port in self.registre_routeurs])
                else:
                    reponse = "vide"

                conn.send(reponse.encode())

        except Exception as e:
            print(f"Erreur traitement demande : {e}")
        finally:
            conn.close()


if __name__ == "__main__":
    mon_ip = get_ip()
    mon_port = 9016

    master = Master(mon_ip, mon_port)
    master.demarrer_ecoute()