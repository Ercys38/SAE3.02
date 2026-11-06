import sys
import threading

from simulation.simulation import Simulation
from simulation.superviseur import Superviseur
from simulation.reseau import (ClientSuperviseur, PORT,
                               trouver_le_superviseur)
from simulation.moteur import Moteur
from simulation.journal import Journal
from simulation.affichage import Fenetre


def superviseur_local(simulation, verrou):
    journal = Journal()
    print("superviseur local, base :", journal.nom)
    superviseur = Superviseur(simulation.feux, verrou, journal)
    superviseur.demarrer()
    return superviseur, journal


def adresse_du_superviseur(argument):
    if argument is not None:
        return (argument, PORT)

    print("recherche du superviseur sur le reseau local...")
    return trouver_le_superviseur()


def choisir_le_superviseur(simulation, verrou, argument):
    if argument == "local":
        return superviseur_local(simulation, verrou)

    adresse = adresse_du_superviseur(argument)
    if adresse is None:
        print("aucun superviseur sur le reseau, on reste en local")
        return superviseur_local(simulation, verrou)

    hote, port = adresse
    print("superviseur trouve :", hote, "port", port)
    client = ClientSuperviseur(hote, port, simulation.feux, verrou)
    return client, None


def main():
    argument = None
    if len(sys.argv) > 1:
        argument = sys.argv[1]

    verrou = threading.Lock()

    simulation = Simulation()
    superviseur, journal = choisir_le_superviseur(simulation, verrou,
                                                  argument)
    moteur = Moteur(simulation, superviseur, verrou)

    moteur.demarrer()

    fenetre = Fenetre(simulation, moteur, verrou)
    try:
        fenetre.lancer()
    finally:
        moteur.arreter()
        superviseur.arreter()
        if journal is not None:
            journal.fermer()


if __name__ == "__main__":
    main()
