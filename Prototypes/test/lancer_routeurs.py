import sys
import time
from routeur_crypt import Routeur, get_ip, sinscrireaumaster
from crypt import CryptoSym


def lancer_un_routeur(ip_routeur, port_routeur, ip_master, port_master):
    """Lance un routeur sur le port spécifié et l'inscrit au master."""
    r = Routeur(ip_routeur, port_routeur)

    # Générer la clé symétrique
    r.crypto = CryptoSym()
    cle = r.crypto.get_cle()

    # Démarrer l'écoute
    r.demarrer_ecoute()
    print(f"Routeur démarré sur {ip_routeur}:{port_routeur} (clé: {cle[:8]}...)")

    # S'inscrire au master
    sinscrireaumaster(ip_master, port_master, port_routeur, cle)

    return r


def arreter_routeurs(routeurs):
    """Arrête proprement tous les routeurs."""
    for r in routeurs:
        r.running = False
        # Fermer le socket pour débloquer l'accept()
        if r.router_socket_ecoute:
            try:
                r.router_socket_ecoute.close()
            except:
                pass
    print("Routeurs arrêtés.")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage : python lancer_routeurs.py <ip_master> <port_master> <nb_routeurs> [port_depart]")
        print("Exemple : python lancer_routeurs.py 192.168.1.10 9016 3 8000")
        sys.exit(1)

    ip_master = sys.argv[1]
    port_master = int(sys.argv[2])
    nb_routeurs = int(sys.argv[3])
    port_depart = int(sys.argv[4]) if len(sys.argv) >= 5 else 8000

    ip_locale = get_ip()
    routeurs = []

    print(f"Lancement de {nb_routeurs} routeur(s) sur {ip_locale}")
    print(f"Inscription au Master {ip_master}:{port_master}\n")

    # Lancer chaque routeur sur un port différent
    for i in range(nb_routeurs):
        port = port_depart + i
        r = lancer_un_routeur(ip_locale, port, ip_master, port_master)
        routeurs.append(r)
        time.sleep(0.5)

    print(f"\n{nb_routeurs} routeur(s) lancé(s) et inscrit(s) au Master.")
    print("Appuyez sur Ctrl+C pour arrêter tous les routeurs.\n")

    # Garder le programme en vie
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nArrêt des routeurs...")
        arreter_routeurs(routeurs)
