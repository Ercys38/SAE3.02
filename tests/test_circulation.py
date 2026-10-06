import random
import unittest

from simulation import ville
from simulation import code_route
from simulation.simulation import Simulation
from simulation.vehicule import LONGUEUR_VOITURE

PAS = 0.033
DUREE = 180


def faire_tourner(densite, duree=DUREE, graine=42):
    random.seed(graine)
    simulation = Simulation()
    simulation.densite = densite

    anomalies = {"collision": 0, "feu_grille": 0, "conflit": 0, "sorties": 0}
    reservation_precedente = {}

    total_pas = int(duree / PAS)
    debut_comptage = total_pas // 2

    for pas in range(total_pas):
        avant = []
        for v in simulation.vehicules:
            avant.append(v.id)

        simulation.avancer(PAS)

        apres = []
        for v in simulation.vehicules:
            apres.append(v.id)

        if pas >= debut_comptage:
            for identifiant in avant:
                if identifiant not in apres:
                    anomalies["sorties"] = anomalies["sorties"] + 1

        for v in simulation.vehicules:
            ancienne = reservation_precedente.get(v.id)
            vient_de_reserver = v.reservation is not None and ancienne is None
            if vient_de_reserver and v.bloque_depuis <= 6.0:
                feu = simulation.feux.get(v.reservation)
                if feu is not None:
                    axe = ville.axe(v.depuis, v.vers)
                    if not feu.passage_autorise(axe):
                        anomalies["feu_grille"] = anomalies["feu_grille"] + 1
            reservation_precedente[v.id] = v.reservation

        for carrefour in simulation.mouvements:
            cles = list(simulation.mouvements[carrefour])
            for i in range(len(cles)):
                for j in range(i + 1, len(cles)):
                    premier = code_route.trajet_dans_le_carrefour(carrefour,
                                                                  cles[i])
                    second = code_route.trajet_dans_le_carrefour(carrefour,
                                                                 cles[j])
                    if code_route.se_croisent(premier, second):
                        anomalies["conflit"] = anomalies["conflit"] + 1

        par_file = {}
        for v in simulation.vehicules:
            cle = (v.depuis, v.vers, v.voie)
            if cle not in par_file:
                par_file[cle] = []
            par_file[cle].append(v.avance)

        for cle in par_file:
            positions = par_file[cle]
            positions.sort()
            for i in range(len(positions) - 1):
                if positions[i + 1] - positions[i] < LONGUEUR_VOITURE * 0.8:
                    anomalies["collision"] = anomalies["collision"] + 1

    return simulation, anomalies


class TestCirculation(unittest.TestCase):

    def test_aucune_collision_dans_une_file(self):
        for densite in (20, 60, 100):
            with self.subTest(densite=densite):
                simulation, anomalies = faire_tourner(densite)
                self.assertEqual(anomalies["collision"], 0)

    def test_aucun_feu_grille(self):
        for densite in (20, 60, 100):
            with self.subTest(densite=densite):
                simulation, anomalies = faire_tourner(densite)
                self.assertEqual(anomalies["feu_grille"], 0)

    def test_aucune_trajectoire_ne_se_croise_dans_le_carrefour(self):
        for densite in (20, 60, 100):
            with self.subTest(densite=densite):
                simulation, anomalies = faire_tourner(densite)
                self.assertEqual(anomalies["conflit"], 0)

    def test_le_carrefour_ecoule_le_trafic(self):
        for densite in (20, 60, 100):
            with self.subTest(densite=densite):
                simulation, anomalies = faire_tourner(densite)
                par_minute = anomalies["sorties"] / (DUREE / 2 / 60)
                self.assertGreater(par_minute, 5)

    def test_le_curseur_de_densite_est_suivi(self):
        simulation, anomalies = faire_tourner(40, duree=60)
        ecart = abs(len(simulation.vehicules) - simulation.nombre_vise())
        self.assertLessEqual(ecart, 2)


if __name__ == "__main__":
    unittest.main()
