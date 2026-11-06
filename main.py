import sys
import threading

from simulation.simulation import Simulation
from simulation.superviseur import Superviseur
from simulation.reseau import ClientSuperviseur, PORT
from simulation.moteur import Moteur
from simulation.journal import Journal
from simulation.affichage import Fenetre


def choisir_le_superviseur(simulation, verrou, journal, hote):
    if hote is None:
        superviseur = Superviseur(simulation.feux, verrou, journal)
        superviseur.demarrer()
        return superviseur

    print("connexion au superviseur", hote, "port", PORT)
    return ClientSuperviseur(hote, PORT, simulation.feux, verrou, journal)


def main():
    hote = None
    if len(sys.argv) > 1:
        hote = sys.argv[1]

    verrou = threading.Lock()

    simulation = Simulation()
    journal = Journal()
    superviseur = choisir_le_superviseur(simulation, verrou, journal, hote)
    moteur = Moteur(simulation, superviseur, verrou)

    moteur.demarrer()

    fenetre = Fenetre(simulation, moteur, verrou)
    try:
        fenetre.lancer()
    finally:
        moteur.arreter()
        superviseur.arreter()
        journal.fermer()


if __name__ == "__main__":
    main()
