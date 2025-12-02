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
        self.registrerouteurs = []  # chaque élément: (ip, port, cle)

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
        return f"Master sur : {self.host}:{self.port}"

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
            print(f"Master en ligne sur {self.host}:{self.port}")

            while self.running:
                conn, addr = self.master_socket_ecoute.accept()
                threading.Thread(target=self._traiter_demande, args=(conn, addr)).start()

        except Exception as e:
            print(f"Erreur Master : {e}")

    def _traiter_demande(self, conn, addr):
        """Analyse le message avec gestion des CLÉS PUBLIQUES"""
        try:
            ip_source = addr[0]
            # On augmente un peu la taille du buffer (4096) car les clés peuvent être longues
            message = conn.recv(1024).decode("latin1")

            if message.startswith("REGISTER"):
                try:
                    _, port_str, cle = message.split(";")
                    portrouteur = int(port_str)
                    ipsource = addr[0]
                    noeud = (ipsource, portrouteur, cle)
                    if noeud not in self.registrerouteurs:
                        self.registrerouteurs.append(noeud)
                        print("Routeur ajouté :", noeud)
                        conn.send(b"OK")
                    else:
                        conn.send(b"ALREADYREGISTERED")
                except Exception as e:
                    print("Erreur REGISTER:", e)
                    conn.send(b"ERROR")


            elif message == "LIST":
                if self.registrerouteurs:
                    reponse = ",".join(f"{ip}:{port}:{cle}" for (ip, port, cle) in self.registrerouteurs)
                else:
                    reponse = ""
                conn.send(reponse.encode("latin1"))


        except Exception as e:
            print(f"Erreur traitement demande : {e}")
        finally:
            conn.close()


if __name__ == "__main__":
    mon_ip = get_ip()
    mon_port = 9016

    master = Master(mon_ip, mon_port)
    master.demarrer_ecoute()

    # Boucle infinie pour garder le programme ouvert
    while True:
        time.sleep(1)