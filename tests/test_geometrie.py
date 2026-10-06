import random
import unittest

from simulation.simulation import Simulation
from simulation.vehicule import LONGUEUR_VOITURE, LARGEUR_VOITURE

ECHELLE = 2.0
LONGUEUR = LONGUEUR_VOITURE * ECHELLE
LARGEUR = LARGEUR_VOITURE * ECHELLE

PAS = 0.033
DUREE = 90


def boite(vehicule):
    x, y = vehicule.position()
    dx, dy = vehicule.direction()
    centre = (x * ECHELLE, y * ECHELLE)
    avant = (dx, dy)
    cote = (-dy, dx)
    return (centre, avant, cote)


def projeter(centre, avant, cote, axe):
    milieu = centre[0] * axe[0] + centre[1] * axe[1]
    part_avant = abs(avant[0] * axe[0] + avant[1] * axe[1]) * LONGUEUR / 2
    part_cote = abs(cote[0] * axe[0] + cote[1] * axe[1]) * LARGEUR / 2
    rayon = part_avant + part_cote
    return (milieu - rayon, milieu + rayon)


def se_chevauchent(a, b):
    centre_a, avant_a, cote_a = a
    centre_b, avant_b, cote_b = b

    for axe in (avant_a, cote_a, avant_b, cote_b):
        a_min, a_max = projeter(centre_a, avant_a, cote_a, axe)
        b_min, b_max = projeter(centre_b, avant_b, cote_b, axe)
        if a_max <= b_min or b_max <= a_min:
            return False
    return True


def compter_les_chevauchements(densite, duree=DUREE, graine=3, secours=False):
    random.seed(graine)
    simulation = Simulation()
    simulation.densite = densite

    if secours:
        for i in range(int(20 / PAS)):
            simulation.avancer(PAS)
        appele = None
        while appele is None:
            simulation.avancer(PAS)
            appele = simulation.lancer_un_secours()

    total = 0
    portee = LONGUEUR + LARGEUR

    for pas in range(int(duree / PAS)):
        simulation.avancer(PAS)

        boites = []
        for v in simulation.vehicules:
            boites.append(boite(v))

        for i in range(len(boites)):
            for j in range(i + 1, len(boites)):
                dx = boites[i][0][0] - boites[j][0][0]
                dy = boites[i][0][1] - boites[j][0][1]
                if dx * dx + dy * dy > portee * portee:
                    continue
                if se_chevauchent(boites[i], boites[j]):
                    total = total + 1

    return total


class TestGeometrie(unittest.TestCase):

    def test_aucun_chevauchement(self):
        for densite in (40, 70, 100):
            with self.subTest(densite=densite):
                self.assertEqual(compter_les_chevauchements(densite), 0)

    def test_aucun_chevauchement_avec_un_secours(self):
        for densite in (40, 100):
            for graine in (1, 2, 3):
                with self.subTest(densite=densite, graine=graine):
                    total = compter_les_chevauchements(densite, duree=70,
                                                       graine=graine,
                                                       secours=True)
                    self.assertEqual(total, 0)


if __name__ == "__main__":
    unittest.main()
