import socket
import threading
import os

host = '127.0.0.1'
port = 10000

def reception(sock):
    while True:
        try:
            msg = sock.recv(1024).decode()
            print(f"\n{msg}")
            if msg == "arret": os._exit(0) # Le serveur a tout coupé
        except: break

# --- Programme Principal ---
sock = socket.socket()
sock.connect((host, port))

# On lance l'écoute en arrière-plan
threading.Thread(target=reception, args=(sock,)).start()

# On envoie les messages
while True:
    msg = input() # Bloquant
    sock.send(msg.encode())
    if msg == "arret": break

sock.close()