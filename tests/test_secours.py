import random
import unittest

from simulation import ville
from simulation.feux import Feu, VERT, ORANGE, DUREE_ORANGE
from simulation.secours import Secours, alerter_les_feux, DISTANCE_ALERTE
from simulation.simulation import Simulation

PAS = 0.033


def traverser(priorite, graine, densite):
    random.seed(graine)
    simulation = Simulation()
    simulation.densite = densite
    simulation.priorite_active = priorite

    for i in range(int(30 / PAS)):
        simulation.avancer(PAS)

    vehicule = None
    while vehicule is None:
        simulation.avancer(PAS)
        vehicule = simulation.lancer_un_secours("N")

    for i in range(int(300 / PAS)):
        simulation.avancer(PAS)
        if vehicule.sorti:
            break
    return vehicule.temps_de_trajet


class TestSecours(unittest.TestCase):

    def test_le_secours_roule_plus_vite_qu_un_civil(self):
        secours = Secours("O", "C")
        self.assertTrue(secours.prioritaire)
        self.assertGreater(secours.vitesse_max, 13.9)

    def test_le_secours_va_tout_droit(self):
        secours = Secours("O", "C")
        self.assertEqual(secours.suivant, "E")

    def test_l_alerte_ne_porte_pas_au_dela_de_500_m(self):
        feux = {"C": Feu()}
        secours = Secours("N", "C")
        secours.avance = 0.0

        alerter_les_feux([secours], feux)
        if secours.reste > DISTANCE_ALERTE:
            self.assertIsNone(feux["C"].priorite)

        secours.avance = secours.longueur_rue - 50.0
        alerter_les_feux([secours], feux)
        self.assertEqual(feux["C"].priorite, "vertical")

    def test_le_feu_passe_a_l_orange_avant_de_basculer(self):
        feu = Feu(axe_passant="horizontal")
        feu.priorite = "vertical"

        feu.avancer(PAS)
        self.assertEqual(feu.etat, ORANGE)
        self.assertEqual(feu.axe_passant, "horizontal")

        for i in range(int(DUREE_ORANGE / PAS) + 2):
            feu.avancer(PAS)
        self.assertEqual(feu.axe_passant, "vertical")
        self.assertEqual(feu.etat, VERT)

    def test_la_priorite_fait_gagner_du_temps(self):
        avec = []
        sans = []
        for graine in (1, 2, 3, 4, 5, 6):
            avec.append(traverser(True, graine, 60))
            sans.append(traverser(False, graine, 60))

        moyenne_avec = sum(avec) / len(avec)
        moyenne_sans = sum(sans) / len(sans)
        self.assertLess(moyenne_avec, moyenne_sans)

    def test_sans_trafic_le_secours_ne_s_arrete_pas(self):
        self.assertLess(traverser(True, 7, 0), traverser(False, 7, 0) + 0.1)


if __name__ == "__main__":
    unittest.main()
