"""Verifie le plan de la ville : graphe, distances, voies, panneaux."""

import unittest

from simulation import ville


class TestVille(unittest.TestCase):

    def test_toutes_les_rues_relient_des_carrefours_connus(self):
        for depart, arrivee, nom, categorie in ville.RUES:
            self.assertIn(depart, ville.CARREFOURS)
            self.assertIn(arrivee, ville.CARREFOURS)
            self.assertIn(categorie, ("avenue", "rue"))
            self.assertTrue(nom)

    def test_le_graphe_est_connexe(self):
        """Tout carrefour doit etre atteignable, sinon un trajet peut echouer."""
        depart = next(iter(ville.CARREFOURS))
        vus, a_voir = {depart}, [depart]
        while a_voir:
            courant = a_voir.pop()
            for voisin in ville.voisins(courant):
                if voisin not in vus:
                    vus.add(voisin)
                    a_voir.append(voisin)
        self.assertEqual(len(vus), len(ville.CARREFOURS))

    def test_aucune_rue_de_longueur_nulle(self):
        for depart, arrivee, _nom, _cat in ville.RUES:
            self.assertGreater(ville.longueur(depart, arrivee), 0)

    def test_les_avenues_ont_deux_files_les_rues_une(self):
        for depart, arrivee, _nom, categorie in ville.RUES:
            attendu = 2 if categorie == "avenue" else 1
            self.assertEqual(ville.voies(depart, arrivee), attendu)

    def test_les_files_ne_se_chevauchent_pas(self):
        """Deux files voisines sont separees d'une largeur de file entiere."""
        for depart, arrivee, _nom, categorie in ville.RUES:
            nombre = ville.voies(depart, arrivee)
            ecarts = [ville.decalage_voie(depart, arrivee, v) for v in range(nombre)]
            for a, b in zip(ecarts, ecarts[1:]):
                self.assertAlmostEqual(abs(a - b), ville.LARGEUR_VOIE)

    def test_une_petite_rue_qui_debouche_sur_une_avenue_a_un_panneau(self):
        for carrefour, infos in ville.CARREFOURS.items():
            if infos["feux"]:
                continue
            categories = [ville.categorie(carrefour, v) for v in ville.voisins(carrefour)]
            if "avenue" not in categories:
                continue
            for voisin in ville.voisins(carrefour):
                if ville.categorie(carrefour, voisin) == "rue":
                    self.assertIn(ville.panneau(carrefour, voisin), ("cedez", "stop"))

    def test_un_carrefour_a_feux_n_a_pas_de_panneau(self):
        """Ce sont les feux qui commandent : un panneau serait contradictoire."""
        for carrefour, infos in ville.CARREFOURS.items():
            if not infos["feux"]:
                continue
            for voisin in ville.voisins(carrefour):
                self.assertIsNone(ville.panneau(carrefour, voisin))


if __name__ == "__main__":
    unittest.main()
