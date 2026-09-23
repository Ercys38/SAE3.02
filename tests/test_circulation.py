"""
Verifie que les voitures respectent le code de la route.

Ces controles font tourner la simulation sans interface et surveillent,
a chaque pas de temps, des invariants qui ne doivent jamais etre violes.
Ils sont plus utiles que des tests unitaires classiques : les defauts de
ce projet apparaissent dans l'interaction entre vehicules, pas dans une
fonction prise isolement.
"""

import random
import unittest

from simulation import ville
from simulation.simulation import Simulation
from simulation.vehicule import LONGUEUR_VOITURE

PAS = 0.033
DUREE = 90          # secondes simulees par controle


def faire_tourner(densite, duree=DUREE, graine=42):
    """Deroule la simulation et renvoie les anomalies rencontrees."""
    random.seed(graine)
    simulation = Simulation()
    simulation.densite = densite

    anomalies = {"collision": 0, "feu_grille": 0, "conflit": 0}
    reservation_precedente = {}

    for _ in range(int(duree / PAS)):
        simulation.avancer(PAS)

        # un vehicule qui vient d'obtenir un carrefour a feux l'a-t-il eu au vert ?
        for v in simulation.vehicules:
            vient_de_reserver = (v.reservation is not None
                                 and reservation_precedente.get(v.id) is None)
            if vient_de_reserver and v.bloque_depuis <= 6.0:
                feu = simulation.feux.get(v.reservation)
                if feu is not None:
                    axe = ville.axe(v.depuis, v.vers)
                    if not feu.passage_autorise(axe):
                        anomalies["feu_grille"] += 1
            reservation_precedente[v.id] = v.reservation

        # deux trajectoires qui se croisent dans le meme carrefour
        for actifs in simulation.mouvements.values():
            anomalies["conflit"] += max(0, len(actifs) - 1)

        # deux voitures au meme endroit dans une meme file
        par_file = {}
        for v in simulation.vehicules:
            par_file.setdefault((v.depuis, v.vers, v.voie), []).append(v.avance)
        for positions in par_file.values():
            positions.sort()
            for a, b in zip(positions, positions[1:]):
                if b - a < LONGUEUR_VOITURE * 0.8:
                    anomalies["collision"] += 1

    return simulation, anomalies


class TestCirculation(unittest.TestCase):

    def test_aucune_collision_dans_une_file(self):
        for densite in (20, 60, 100):
            with self.subTest(densite=densite):
                _, anomalies = faire_tourner(densite)
                self.assertEqual(anomalies["collision"], 0)

    def test_aucun_feu_grille(self):
        for densite in (20, 60, 100):
            with self.subTest(densite=densite):
                _, anomalies = faire_tourner(densite)
                self.assertEqual(anomalies["feu_grille"], 0)

    def test_un_seul_mouvement_par_carrefour(self):
        for densite in (20, 60, 100):
            with self.subTest(densite=densite):
                _, anomalies = faire_tourner(densite)
                self.assertEqual(anomalies["conflit"], 0)

    def test_le_trafic_ne_se_bloque_pas(self):
        """A densite moyenne, la plupart des voitures doivent rouler."""
        simulation, _ = faire_tourner(60)
        arretees = sum(1 for v in simulation.vehicules if v.vitesse < 0.3)
        self.assertLess(arretees, len(simulation.vehicules) * 0.4)

    def test_le_curseur_de_densite_est_suivi(self):
        simulation, _ = faire_tourner(40, duree=40)
        self.assertEqual(len(simulation.vehicules), simulation.nombre_vise())


if __name__ == "__main__":
    unittest.main()
