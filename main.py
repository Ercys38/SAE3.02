"""
Point d'entree du projet.

Lancement :   python3 main.py
"""

from simulation.simulation import Simulation
from simulation.affichage import Fenetre


def main():
    simulation = Simulation()
    fenetre = Fenetre(simulation)
    fenetre.lancer()


if __name__ == "__main__":
    main()
