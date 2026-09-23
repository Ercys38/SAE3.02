"""
Verifie qu'aucune voiture n'en chevauche une autre a l'ecran.

C'est le controle le plus severe du projet, et celui qui a trouve le plus
de defauts. Il ne raisonne pas en distances le long d'une rue mais en
rectangles orientes, exactement comme ce qui est dessine : une voiture
peut respecter toutes les distances de son propre axe et se retrouver
quand meme a cheval sur une autre, dans un virage ou en travers d'un
carrefour.

La comparaison utilise le theoreme des axes separateurs : deux rectangles
ne se touchent pas des qu'il existe une direction sur laquelle leurs
projections sont disjointes.
"""

import random
import unittest

from simulation.simulation import Simulation
from simulation.vehicule import LONGUEUR_VOITURE

# Memes valeurs que dans affichage.py : on controle ce qui est affiche.
ECHELLE = 0.42
LONGUEUR = LONGUEUR_VOITURE * ECHELLE
LARGEUR = 2.6

PAS = 0.033
DUREE = 90


def boite(vehicule):
    """Centre, axe avant et axe lateral du vehicule, en pixels."""
    x, y = vehicule.position()      # inclut deja le decalage de file
    dx, dy = vehicule.direction()
    return (x * ECHELLE, y * ECHELLE), (dx, dy), (-dy, dx)


def projeter(centre, avant, cote, axe):
    milieu = centre[0] * axe[0] + centre[1] * axe[1]
    rayon = (abs(avant[0] * axe[0] + avant[1] * axe[1]) * LONGUEUR / 2
             + abs(cote[0] * axe[0] + cote[1] * axe[1]) * LARGEUR / 2)
    return milieu - rayon, milieu + rayon


def se_chevauchent(a, b):
    centre_a, avant_a, cote_a = a
    centre_b, avant_b, cote_b = b
    for axe in (avant_a, cote_a, avant_b, cote_b):
        a_min, a_max = projeter(centre_a, avant_a, cote_a, axe)
        b_min, b_max = projeter(centre_b, avant_b, cote_b, axe)
        if a_max <= b_min or b_max <= a_min:
            return False            # un axe les separe
    return True


def compter_les_chevauchements(densite, duree=DUREE, graine=3):
    random.seed(graine)
    simulation = Simulation()
    simulation.densite = densite

    total = 0
    portee = LONGUEUR + LARGEUR     # au-dela, inutile de comparer

    for _ in range(int(duree / PAS)):
        simulation.avancer(PAS)
        boites = [boite(v) for v in simulation.vehicules]
        for i in range(len(boites)):
            for j in range(i + 1, len(boites)):
                dx = boites[i][0][0] - boites[j][0][0]
                dy = boites[i][0][1] - boites[j][0][1]
                if dx * dx + dy * dy > portee * portee:
                    continue
                if se_chevauchent(boites[i], boites[j]):
                    total += 1
    return total


class TestGeometrie(unittest.TestCase):

    def test_aucun_chevauchement(self):
        for densite in (40, 70, 100):
            with self.subTest(densite=densite):
                self.assertEqual(compter_les_chevauchements(densite), 0)


if __name__ == "__main__":
    unittest.main()
