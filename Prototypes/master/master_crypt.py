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
        # Cette liste stocke maintenant des triplets : (ip, port, cle_publique)
        self.registre_routeurs = []

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
            message = conn.recv(4096).decode()

            # Un routeur veut s'inscrire
            # Format attendu : "REGISTER|8000|e,n" (avec la clé à la fin)
            if message.startswith("REGISTER"):
                parts = message.split("|")

                # Vérification qu'on a bien les 3 parties (Header, Port, Clé)
                if len(parts) >= 3:
                    port_routeur = int(parts[1])
                    cle_publique = parts[2]  # La clé sous forme "12345,67890"

                    # On crée le triplet (IP, PORT, CLE)
                    nouveau_noeud = (ip_source, port_routeur, cle_publique)

                    # Vérification anti-doublon (basée sur IP et Port uniquement)
                    existe = False
                    for r in self.registre_routeurs:
                        if r[0] == ip_source and r[1] == port_routeur:
                            existe = True

                    if not existe:
                        self.registre_routeurs.append(nouveau_noeud)
                        print(f"Routeur ajouté : {ip_source}:{port_routeur} (avec Clé)")
                        conn.send("OK".encode())
                    else:
                        print(f"Le routeur {ip_source} est déjà inscrit.")
                        conn.send("ALREADY_REGISTERED".encode())
                else:
                    print("Format REGISTER invalide (manque la clé ?)")

            # Un client veut la liste des routeurs
            elif message == "LIST":
                print(f"Envoi de la liste à {ip_source}")

                if self.registre_routeurs:
                    # On construit la réponse : "IP:PORT:CLE ; IP:PORT:CLE"
                    liste_str = []
                    for ip, port, cle in self.registre_routeurs:
                        liste_str.append(f"{ip}:{port}:{cle}")

                    reponse = ";".join(liste_str)
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

    # Boucle infinie pour garder le programme ouvert
    while True:
        time.sleep(1)