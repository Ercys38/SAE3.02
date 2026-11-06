import sys
import time

from simulation.journal import Journal
from simulation.reseau import Serveur, Annonceur, PORT
from simulation.superviseur import Superviseur


def main():
    port = PORT
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    journal = Journal()
    superviseur = Superviseur(journal=journal)
    serveur = Serveur(superviseur, port=port)
    annonceur = Annonceur(port_du_serveur=port)

    superviseur.demarrer()
    serveur.demarrer()
    annonceur.demarrer()
    print("base :", journal.nom)
    print("superviseur en ecoute sur le port", port)
    print("annonce sur le reseau local, les clients le trouveront seuls")

    try:
        while True:
            time.sleep(1)
            print("clients :", serveur.clients,
                  "| messages recus :", superviseur.recus,
                  "| interventions en base :",
                  journal.nombre_d_interventions(),
                  "| carrefours prioritaires :",
                  sorted(superviseur.priorites))
    except KeyboardInterrupt:
        print()
    finally:
        annonceur.arreter()
        serveur.arreter()
        superviseur.arreter()
        journal.fermer()


if __name__ == "__main__":
    main()
