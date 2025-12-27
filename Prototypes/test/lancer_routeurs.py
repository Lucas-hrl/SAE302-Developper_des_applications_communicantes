"""
Script utilitaire pour lancer plusieurs routeurs d'un coup.
Permet de simuler un réseau sur une seule machine ou VM.
"""

import sys
import time
# On importe la classe et les fonctions depuis notre fichier routeur_crypt
from routeur_crypt import Routeur, get_ip, s_inscrire_au_master
from crypt import CryptoSym

def lancer_un_routeur(ip_routeur, port_routeur, ip_master, port_master):
    """Instancie, configure et démarre un routeur"""
    r = Routeur(ip_routeur, port_routeur)
    r.set_master_info(ip_master, port_master)

    # On génère une clé unique pour ce routeur
    r.crypto = CryptoSym()
    cle = r.crypto.get_cle()

    # Lancement du thread d'écoute
    r.demarrer_ecoute()
    # Inscription immédiate au Master
    succes = False
    if s_inscrire_au_master(ip_master, port_master, port_routeur, cle):
        print(f"Routeur démarré sur {ip_routeur}:{port_routeur} (Clé: {cle[:10]}...) - INSCRIT AU MASTER")
        succes = True
    else:
        print(f"Routeur démarré sur {ip_routeur}:{port_routeur} mais ECHEC inscription Master")

    return r, succes

def arreter_routeurs(routeurs):
    """Ferme proprement les sockets de tous les routeurs"""
    print("\nArrêt des routeurs en cours...")
    for r in routeurs:
        r.running = False
        if r.router_socket_ecoute:
            try:
                r.router_socket_ecoute.close()
            except:
                pass
    print("Tous les routeurs sont arrêtés.")

if __name__ == "__main__":
    # Vérification des arguments
    if len(sys.argv) < 4:
        print("Usage : python lancer_routeurs.py <IP_MASTER> <PORT_MASTER> <NB_ROUTEURS> [PORT_DEPART]")
        print("Exemple : python lancer_routeurs.py 192.168.1.10 9016 5 8000")
        sys.exit(1)

    ip_master = sys.argv[1]
    port_master = int(sys.argv[2])
    nb_routeurs = int(sys.argv[3])
    # Port de départ optionnel, sinon 8000
    port_depart = int(sys.argv[4]) if len(sys.argv) >= 5 else 8000

    ip_locale = get_ip()
    routeurs_list = []

    print(f"--- Lancement de {nb_routeurs} routeur(s) sur {ip_locale} ---")
    print(f"--- Cible Master : {ip_master}:{port_master} ---\n")

    # Boucle de création
    nb_inscrits = 0
    for i in range(nb_routeurs):
        port = port_depart + i
        r, succes = lancer_un_routeur(ip_locale, port, ip_master, port_master)
        routeurs_list.append(r)
        if succes:
            nb_inscrits += 1
        # Petite pause pour ne pas spammer le Master
        time.sleep(0.2)

    print(f"\n>> {nb_routeurs} routeurs démarrés.")
    if nb_inscrits == nb_routeurs:
        print(f">> TOUS les routeurs sont inscrits au Master ({nb_inscrits}/{nb_routeurs}).")
    elif nb_inscrits == 0:
        print(f">> AUCUN routeur n'a pu s'inscrire au Master (0/{nb_routeurs}). Vérifiez qu'il est lancé !")
    else:
        print(f">> ATTENTION : Seuls {nb_inscrits}/{nb_routeurs} routeurs sont inscrits.")
    print(">> Appuyez sur Ctrl+C pour tout arrêter.\n")

    # Boucle infinie pour maintenir le script en vie
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # Interception du CTRL+C pour fermer proprement
        arreter_routeurs(routeurs_list)