"""
Client graphique pour réseau en oignon
Gère la connexion au Master, la création du circuit et l'envoi/réception des messages.
"""

import sys
import socket
import threading
import random
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QGridLayout,
                             QLabel, QLineEdit, QPushButton, QTextEdit, QSpinBox)
from PyQt6.QtCore import pyqtSignal
from crypt import CryptoSym


# Fonction pour récupérer mon IP locale sur le réseau (pas 127.0.0.1)
def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'


class ClientWindow(QMainWindow):
    # Signaux pour communiquer entre les threads et l'interface
    signal_log = pyqtSignal(str)
    signal_update_routeurs = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Client Tor")
        self.resize(550, 650)

        self.host = get_ip()
        self.port = 5000

        # Etats pour gérer l'activation du bouton Envoyer
        self.listening = False
        self.routeurs_found = False

        # Configuration de l'interface
        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        layout = QGridLayout()
        widget_central.setLayout(layout)

        # --- Configuration du Master ---
        layout.addWidget(QLabel("<b>CONFIGURATION MASTER</b>"), 0, 0, 1, 3)

        layout.addWidget(QLabel("IP Master:"), 1, 0)
        self.input_master_ip = QLineEdit("192.168.1.28")
        layout.addWidget(self.input_master_ip, 1, 1)

        layout.addWidget(QLabel("Port Master:"), 2, 0)
        self.input_master_port = QLineEdit("9016")
        layout.addWidget(self.input_master_port, 2, 1)

        self.btn_check = QPushButton("Connexion Master")
        self.btn_check.clicked.connect(self.action_verifier_routeurs)
        layout.addWidget(self.btn_check, 1, 2, 2, 1)

        self.lbl_info_routeurs = QLabel("Statut : Non connecté")
        self.lbl_info_routeurs.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(self.lbl_info_routeurs, 3, 0, 1, 3)

        # --- Configuration Client (Moi) ---
        layout.addWidget(QLabel("<b>MON CLIENT</b>"), 4, 0, 1, 3)
        layout.addWidget(QLabel("Mon Port:"), 5, 0)
        self.input_mon_port = QLineEdit("6016")
        layout.addWidget(self.input_mon_port, 5, 1)

        self.btn_demarrer = QPushButton("Démarrer Écoute")
        self.btn_demarrer.clicked.connect(self.action_demarrer)
        layout.addWidget(self.btn_demarrer, 5, 2)

        # --- Configuration Envoi ---
        layout.addWidget(QLabel("<b>DESTINATAIRE</b>"), 6, 0, 1, 3)
        layout.addWidget(QLabel("IP Dest:"), 7, 0)
        self.input_dest = QLineEdit("127.0.0.1")
        layout.addWidget(self.input_dest, 7, 1)
        layout.addWidget(QLabel("Port Dest:"), 8, 0)
        self.input_port_dest = QLineEdit("5000")
        layout.addWidget(self.input_port_dest, 8, 1)

        layout.addWidget(QLabel("Nb Sauts:"), 9, 0)
        self.spin_sauts = QSpinBox()
        self.spin_sauts.setRange(0, 0)
        self.spin_sauts.setEnabled(False)
        layout.addWidget(self.spin_sauts, 9, 1)

        self.input_msg = QLineEdit()
        self.input_msg.setPlaceholderText("Message à envoyer...")
        layout.addWidget(self.input_msg, 10, 0, 1, 2)

        self.btn_envoyer = QPushButton("Envoyer")
        self.btn_envoyer.clicked.connect(self.lancer_thread_envoi)
        self.btn_envoyer.setEnabled(False)
        layout.addWidget(self.btn_envoyer, 10, 2)

        # Zone de logs
        self.logs = QTextEdit()
        self.logs.setReadOnly(True)
        layout.addWidget(self.logs, 11, 0, 1, 3)

        # Connexions
        self.signal_log.connect(self.append_log)
        self.signal_update_routeurs.connect(self.update_ui_routeurs)

    # --- Fonctions de l'interface ---

    def check_enable_send(self):
        # On active le bouton seulement si on écoute ET qu'on a la liste des routeurs
        if self.listening and self.routeurs_found:
            self.btn_envoyer.setEnabled(True)
            self.btn_envoyer.setText("Envoyer")
        else:
            self.btn_envoyer.setEnabled(False)
            if not self.listening:
                self.btn_envoyer.setText("Démarrez l'écoute d'abord")
            elif not self.routeurs_found:
                self.btn_envoyer.setText("Connectez le Master d'abord")

    def append_log(self, text):
        self.logs.append(text)

    def update_ui_routeurs(self, nb):
        if nb > 0:
            self.lbl_info_routeurs.setText(f"Connecté : {nb} routeur(s) trouvés")
            self.lbl_info_routeurs.setStyleSheet("color: green; font-weight: bold;")
            self.spin_sauts.setEnabled(True)
            self.spin_sauts.setRange(1, nb)
            self.spin_sauts.setValue(min(2, nb))
            self.routeurs_found = True
        else:
            self.lbl_info_routeurs.setText("Connecté mais 0 routeur disponible")
            self.lbl_info_routeurs.setStyleSheet("color: orange; font-weight: bold;")
            self.routeurs_found = False

        self.check_enable_send()

    # --- Gestion Réseau ---

    def action_demarrer(self):
        # Démarre le serveur d'écoute pour recevoir les réponses
        try:
            self.port = int(self.input_mon_port.text())

            self.signal_log.emit(f"Démarrage serveur écoute sur {self.host}:{self.port}...")
            # Thread daemon pour qu'il se ferme avec l'application
            threading.Thread(target=self.thread_ecoute, daemon=True).start()

            self.btn_demarrer.setEnabled(False)
            self.btn_demarrer.setText("En ligne")
            self.input_mon_port.setDisabled(True)

            self.listening = True
            self.check_enable_send()

        except ValueError:
            self.signal_log.emit("Erreur: Port invalide")

    def thread_ecoute(self):
        # Boucle principale d'écoute des messages entrants
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((self.host, self.port))
            s.listen(5)
            while True:
                try:
                    conn, addr = s.accept()
                    data = conn.recv(4096).decode("latin1")
                    if data:
                        # On enlève les ';;' qui servent de marqueur de fin dans notre protocole
                        if data.startswith(";;"): data = data[2:]
                        self.signal_log.emit(f"[REÇU de {addr[0]}] {data}")
                    conn.close()
                except:
                    break
        except Exception as e:
            self.signal_log.emit(f"Erreur écoute: {e}")
        finally:
            s.close()

    def action_verifier_routeurs(self):
        master_ip = self.input_master_ip.text()
        try:
            master_port = int(self.input_master_port.text())
            threading.Thread(target=self.thread_get_info_master, args=(master_ip, master_port)).start()
        except ValueError:
            self.signal_log.emit("Erreur: Port Master invalide")

    def thread_get_info_master(self, ip, port):
        try:
            routeurs = self.get_liste_routeurs(ip, port)
            nb = len(routeurs)
            self.signal_log.emit(f"Réponse Master: {nb} routeur(s).")
            self.signal_update_routeurs.emit(nb)
        except Exception as e:
            self.signal_log.emit(f"Erreur connexion Master: {e}")
            self.signal_update_routeurs.emit(0)

    def get_liste_routeurs(self, ip_master, port_master):
        # Récupère la liste des routeurs sous forme IP:PORT:CLE
        s_master = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s_master.settimeout(3)
        s_master.connect((ip_master, port_master))
        s_master.send(b"LIST")
        data = s_master.recv(4096).decode("latin1")
        s_master.close()

        routeurs = []
        if data and data != "EMPTY":
            for item in data.split(","):
                if item:
                    # On split seulement 2 fois car la clé peut contenir des ':'
                    parts = item.split(":", 2)
                    if len(parts) == 3:
                        ip, port, cle = parts
                        routeurs.append((ip, int(port), cle))
        return routeurs

    def lancer_thread_envoi(self):
        msg = self.input_msg.text()
        if not msg: return

        dest_ip = self.input_dest.text()
        try:
            dest_port = int(self.input_port_dest.text())
            nb_sauts = self.spin_sauts.value()
            master_ip = self.input_master_ip.text()
            master_port = int(self.input_master_port.text())

            # On lance le traitement dans un thread pour ne pas geler l'interface
            threading.Thread(target=self.processus_envoi,
                             args=(msg, dest_ip, dest_port, nb_sauts, master_ip, master_port)).start()
        except ValueError:
            self.signal_log.emit("Erreur: Ports invalides.")

    def processus_envoi(self, message, ip_dest, port_dest, nb_sauts, master_ip, master_port):
        # Construction de l'oignon et chiffrement en couches
        try:
            self.signal_log.emit("Construction du circuit...")

            # On récupère la liste à jour
            routeurs = self.get_liste_routeurs(master_ip, master_port)
            if not routeurs:
                self.signal_log.emit("Erreur: Liste vide")
                return

            nb_sauts = min(nb_sauts, len(routeurs))

            # Choix aléatoire du circuit
            circuit = random.sample(routeurs, nb_sauts)

            chemin_str = " -> ".join([f"{r[0]}:{r[1]}" for r in circuit])
            self.signal_log.emit(f"Route: Moi -> {chemin_str} -> {ip_dest}:{port_dest}")

            # Chiffrement en couches
            # Le message final commence par ;; pour indiquer la fin du routage
            paquet = f";;{message}"

            # On parcourt le circuit à l'envers (du dernier nœud vers le premier)
            # Chaque routeur ajoute sa couche de chiffrement
            for i in range(len(circuit) - 1, -1, -1):
                if i == len(circuit) - 1:
                    # Le dernier routeur envoie au destinataire final
                    next_ip = ip_dest
                    next_port = port_dest
                else:
                    # Les autres envoient au routeur suivant
                    next_ip = circuit[i + 1][0]
                    next_port = circuit[i + 1][1]

                # Format du message pour le routeur : IP_SUIVANTE;PORT_SUIVANT;PAYLOAD
                texte_clair = f"{next_ip};{next_port};{paquet}"

                # Chiffrement avec la clé du routeur actuel
                crypto = CryptoSym(cle=circuit[i][2])
                paquet = crypto.chiffrer(texte_clair).decode("latin1")

            # 4. Envoi au premier routeur
            first = circuit[0]
            self.signal_log.emit(f"Envoi vers {first[0]}:{first[1]}...")

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((first[0], first[1]))
            s.sendall(paquet.encode("latin1"))
            s.close()

            self.signal_log.emit("Message envoyé !")

        except Exception as e:
            self.signal_log.emit(f"Erreur envoi: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ClientWindow()
    window.show()
    sys.exit(app.exec())