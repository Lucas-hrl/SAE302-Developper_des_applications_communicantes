import socket
import threading
import os

clients = []  # Liste simple des connectés


def ecriture_serveur():
    """Permet au serveur d'écrire à tout le monde"""
    while True:
        msg = input()
        if msg == "arret": os._exit(0)  # Arrêt brutal mais efficace
        for c in clients:  # On envoie à tout le monde
            try:
                c.send(f"Serveur: {msg}".encode())
            except:
                pass


def gestion_client(conn, addr):
    """Écoute un client"""
    clients.append(conn)  # On l'ajoute à la liste
    print(f"Nouveau : {addr}")
    while True:
        try:
            data = conn.recv(1024).decode()
            if data == "arret" or not data: break
            print(f"{addr} > {data}")  # On affiche juste côté serveur

            # Optionnel : renvoyer le message aux autres (Broadcast)
            # for c in clients:
            #     if c != conn: c.send(f"{addr}: {data}".encode())
        except:
            break
    conn.close()
    if conn in clients: clients.remove(conn)  # On le retire de la liste


# --- Programme Principal ---
server = socket.socket()
server.bind(('0.0.0.0', 10000))
server.listen(5)

# On active la possibilité pour le serveur d'écrire
threading.Thread(target=ecriture_serveur).start()

print("Serveur prêt...")
while True:
    conn, addr = server.accept()
    threading.Thread(target=gestion_client, args=(conn, addr)).start()