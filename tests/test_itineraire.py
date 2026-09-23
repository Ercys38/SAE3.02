"""Verifie le calcul d'itineraire : Dijkstra sur le plan de la ville."""

import unittest

from simulation import ville
from simulation import itineraire


def toutes_les_distances():
    """Floyd-Warshall : reference independante pour controler Dijkstra."""
    noms = list(ville.CARREFOURS)
    dist = {(a, b): (0.0 if a == b else float("inf")) for a in noms for b in noms}
    for depart, arrivee, _nom, _cat in ville.RUES:
        d = ville.longueur(depart, arrivee)
        dist[depart, arrivee] = min(dist[depart, arrivee], d)
        dist[arrivee, depart] = min(dist[arrivee, depart], d)
    for k in noms:
        for i in noms:
            for j in noms:
                if dist[i, k] + dist[k, j] < dist[i, j]:
                    dist[i, j] = dist[i, k] + dist[k, j]
    return dist


class TestItineraire(unittest.TestCase):

    def test_meme_carrefour(self):
        chemin, total = itineraire.plus_court_chemin("E", "E")
        self.assertEqual(chemin, ["E"])
        self.assertEqual(total, 0)

    def test_carrefours_voisins(self):
        chemin, total = itineraire.plus_court_chemin("A", "AB")
        self.assertEqual(chemin, ["A", "AB"])
        self.assertAlmostEqual(total, 350)

    def test_coin_a_coin(self):
        """De A a I, il faut au moins 1400 m a l'est et 1400 m au sud."""
        chemin, total = itineraire.plus_court_chemin("A", "I")
        self.assertAlmostEqual(total, 2800)
        self.assertEqual(chemin[0], "A")
        self.assertEqual(chemin[-1], "I")

    def test_egal_a_la_reference_pour_toutes_les_paires(self):
        reference = toutes_les_distances()
        for depart in ville.CARREFOURS:
            for arrivee in ville.CARREFOURS:
                chemin, total = itineraire.plus_court_chemin(depart, arrivee)
                self.assertAlmostEqual(total, reference[depart, arrivee])
                self.assertAlmostEqual(itineraire.longueur_chemin(chemin), total)

    def test_le_chemin_suit_des_rues_existantes(self):
        chemin, _total = itineraire.plus_court_chemin("G", "C")
        for a, b in zip(chemin, chemin[1:]):
            self.assertIn(b, ville.voisins(a))

    def test_un_cout_personnalise_change_le_trajet(self):
        """Une rue rendue tres chere (bouchon) est contournee."""
        direct, _ = itineraire.plus_court_chemin("A", "B")
        self.assertEqual(direct, ["A", "AB", "B"])

        def cout(depuis, vers):
            if {depuis, vers} == {"AB", "B"}:
                return 10_000
            return ville.longueur(depuis, vers)

        detour, total = itineraire.plus_court_chemin("A", "B", cout)
        self.assertNotIn(("AB", "B"), list(zip(detour, detour[1:])))
        self.assertLess(total, 10_000)

    def test_carrefour_inconnu(self):
        with self.assertRaises(ValueError):
            itineraire.plus_court_chemin("A", "Z")

    def test_cout_negatif_refuse(self):
        with self.assertRaises(ValueError):
            itineraire.plus_court_chemin("A", "I", lambda a, b: -1)

    def test_description_regroupe_les_troncons(self):
        chemin = ["A", "AB", "B", "BC", "C"]
        self.assertEqual(itineraire.description(chemin), ["Avenue de Bale"])


if __name__ == "__main__":
    unittest.main()
