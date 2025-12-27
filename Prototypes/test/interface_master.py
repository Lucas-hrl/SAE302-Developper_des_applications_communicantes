
import sys
import socket
import threading
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QTabWidget, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QColor

# Importation de la logique du Master existant
from master_crypt import Master, DB_HOST, DB_USER, DB_PASS
import mysql.connector

class MasterGUI(QMainWindow):
    def __init__(self, ip, port):
        super().__init__()
        self.ip = ip
        self.port = port
        self.master = None
        
        self.setWindowTitle("Master Server - Interface de Gestion")
        self.resize(800, 600)
        
        # Widget principal
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # --- Zone de contrôle (Haut) ---
        control_layout = QHBoxLayout()
        
        self.lbl_status = QLabel("Statut : ARRÊTÉ")
        self.lbl_status.setStyleSheet("color: red; font-weight: bold;")
        
        self.btn_start = QPushButton("Démarrer Serveur")
        self.btn_start.clicked.connect(self.start_server)
        
        self.btn_stop = QPushButton("Arrêter Serveur")
        self.btn_stop.clicked.connect(self.stop_server)
        self.btn_stop.setEnabled(False)
        
        control_layout.addWidget(QLabel(f"IP: {self.ip}"))
        control_layout.addWidget(QLabel(f"Port: {self.port}"))
        control_layout.addStretch()
        control_layout.addWidget(self.lbl_status)
        control_layout.addWidget(self.btn_start)
        control_layout.addWidget(self.btn_stop)
        
        layout.addLayout(control_layout)
        
        # --- Onglets (Centre) ---
        self.tabs = QTabWidget()
        
        # Onglet Routeurs
        self.tab_routers = QWidget()
        self.layout_routers = QVBoxLayout(self.tab_routers)
        self.table_routers = QTableWidget()
        self.table_routers.setColumnCount(5)
        self.table_routers.setHorizontalHeaderLabels(["ID", "IP", "Port", "Clé (Extrait)", "Statut"])
        self.table_routers.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.layout_routers.addWidget(self.table_routers)
        self.tabs.addTab(self.tab_routers, "Routeurs Inscrits")
        
        # Onglet Logs
        self.tab_logs = QWidget()
        self.layout_logs = QVBoxLayout(self.tab_logs)
        self.table_logs = QTableWidget()
        self.table_logs.setColumnCount(4)
        self.table_logs.setHorizontalHeaderLabels(["Date/Heure", "Événement", "Source", "Détails"])
        self.table_logs.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.layout_logs.addWidget(self.table_logs)
        self.tabs.addTab(self.tab_logs, "Logs / Événements")
        
        layout.addWidget(self.tabs)
        
        # --- Timer de rafraîchissement ---
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(2000) # Rafraîchir toutes les 2 secondes

    def start_server(self):
        try:
            self.master = Master(self.ip, self.port)
            self.master.demarrer_ecoute()
            
            self.lbl_status.setText("Statut : EN LIGNE")
            self.lbl_status.setStyleSheet("color: green; font-weight: bold;")
            self.btn_start.setEnabled(False)
            self.btn_stop.setEnabled(True)
            self.statusBar().showMessage(f"Serveur démarré sur {self.ip}:{self.port}")
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de démarrer le serveur:\n{e}\nVérifiez que le port n'est pas déjà utilisé.")

    def stop_server(self):
        # 1. Nettoyage de la BDD
        try:
            conn = mysql.connector.connect(
                host=DB_HOST, user=DB_USER, password=DB_PASS, database="sae_routage_oignon_lh"
            )
            cursor = conn.cursor()
            cursor.execute("TRUNCATE TABLE routeurs")
            cursor.execute("TRUNCATE TABLE logs")
            conn.commit()
            conn.close()
            print(">> Tables routeurs et logs vidées.")
        except Exception as e:
            print(f"Erreur lors du vidage des tables : {e}")

        # 2. Arrêt du Master
        if self.master:
            self.master.running = False
            # On force la fermeture du socket pour débloquer le accept() du thread
            if self.master.master_socket_ecoute:
                try:
                    # Bonne pratique : shutdown avant close pour forcer le réveil immédiat
                    self.master.master_socket_ecoute.shutdown(socket.SHUT_RDWR)
                except Exception:
                    # Peut échouer si le socket n'est pas connecté ou déjà fermé
                    pass
                
                try:
                    self.master.master_socket_ecoute.close()
                except:
                    pass
            
            # On attend un peu que le thread se termine (optionnel mais propre)
            if hasattr(self.master, 'thread_ecoute') and self.master.thread_ecoute.is_alive():
                 self.master.thread_ecoute.join(timeout=2.0)

            self.master = None
            
        self.lbl_status.setText("Statut : ARRÊTÉ")
        self.lbl_status.setStyleSheet("color: red; font-weight: bold;")
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.statusBar().showMessage("Serveur arrêté et BDD nettoyée")
        
        # On rafraîchit immédiatement l'affichage pour montrer que c'est vide
        self.refresh_data()

    def refresh_data(self):
        """Interroge la BDD pour mettre à jour les tableaux"""
        try:
            conn = mysql.connector.connect(
                host=DB_HOST, user=DB_USER, password=DB_PASS, database="sae_routage_oignon_lh"
            )
            cursor = conn.cursor()
            
            # --- Mise à jour Routeurs ---
            cursor.execute("SELECT id, ip, port, cle, statut FROM routeurs ORDER BY id DESC")
            rows = cursor.fetchall()
            self.table_routers.setRowCount(0)
            for row in rows:
                row_idx = self.table_routers.rowCount()
                self.table_routers.insertRow(row_idx)
                # ID
                self.table_routers.setItem(row_idx, 0, QTableWidgetItem(str(row[0])))
                # IP
                self.table_routers.setItem(row_idx, 1, QTableWidgetItem(str(row[1])))
                # Port
                self.table_routers.setItem(row_idx, 2, QTableWidgetItem(str(row[2])))
                # Clé (tronquée)
                cle_courte = str(row[3])[:10] + "..." if row[3] else ""
                self.table_routers.setItem(row_idx, 3, QTableWidgetItem(cle_courte))
                
                # Statut
                statut_str = str(row[4]) if row[4] else "INCONNU"
                item_statut = QTableWidgetItem(statut_str)
                item_statut.setFont(self.font()) # Keep font consistent, can bold if wanted
                
                # Gestion de la couleur en fonction du statut (Vert=OK, Rouge=HS)
                if statut_str == "ACTIVE":
                    item_statut.setForeground(QColor("green"))
                elif statut_str == "DOWN":
                    item_statut.setForeground(QColor("red"))
                
                self.table_routers.setItem(row_idx, 4, item_statut)
                
            # --- Mise à jour Logs ---
            # On affiche les 50 derniers logs
            cursor.execute("SELECT moment, evenement, ip_source, details FROM logs ORDER BY id DESC LIMIT 50")
            log_rows = cursor.fetchall()
            self.table_logs.setRowCount(0)
            for l_row in log_rows:
                l_idx = self.table_logs.rowCount()
                self.table_logs.insertRow(l_idx)
                # Timestamp
                self.table_logs.setItem(l_idx, 0, QTableWidgetItem(str(l_row[0])))
                # Event
                self.table_logs.setItem(l_idx, 1, QTableWidgetItem(str(l_row[1])))
                # Source
                self.table_logs.setItem(l_idx, 2, QTableWidgetItem(str(l_row[2])))
                # Details
                self.table_logs.setItem(l_idx, 3, QTableWidgetItem(str(l_row[3])))
                
            conn.close()
            
        except mysql.connector.Error:
            # Si la BDD n'est pas encore dispo ou erreur de connexion, on ignore silencieusement
            # pour ne pas spammer d'erreurs graphiques (au pire les tables restent vides)
            pass
        except Exception as e:
            print(f"Erreur refresh GUI: {e}")

if __name__ == "__main__":
    # Test autonome de l'interface
    app = QApplication(sys.argv)
    window = MasterGUI("127.0.0.1", 9016)
    window.show()
    sys.exit(app.exec())
