import sys
import time

from simulation.journal import Journal
from simulation.reseau import Serveur, PORT
from simulation.superviseur import Superviseur


def main():
    port = PORT
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    journal = Journal()
    superviseur = Superviseur(journal=journal)
    serveur = Serveur(superviseur, port=port)

    superviseur.demarrer()
    serveur.demarrer()
    print("superviseur en ecoute sur le port", port)

    try:
        while True:
            time.sleep(1)
            print("clients :", serveur.clients,
                  "| messages recus :", superviseur.recus,
                  "| carrefours prioritaires :", sorted(superviseur.priorites))
    except KeyboardInterrupt:
        print()
    finally:
        serveur.arreter()
        superviseur.arreter()
        journal.fermer()


if __name__ == "__main__":
    main()
