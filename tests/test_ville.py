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
        depart = list(ville.CARREFOURS)[0]
        vus = [depart]
        a_voir = [depart]
        while a_voir:
            courant = a_voir.pop()
            for voisin in ville.voisins(courant):
                if voisin not in vus:
                    vus.append(voisin)
                    a_voir.append(voisin)
        self.assertEqual(len(vus), len(ville.CARREFOURS))

    def test_aucune_rue_de_longueur_nulle(self):
        for depart, arrivee, nom, categorie in ville.RUES:
            self.assertGreater(ville.longueur(depart, arrivee), 0)

    def test_les_avenues_ont_deux_files_les_rues_une(self):
        for depart, arrivee, nom, categorie in ville.RUES:
            if categorie == "avenue":
                attendu = 2
            else:
                attendu = 1
            self.assertEqual(ville.voies(depart, arrivee), attendu)

    def test_les_files_ne_se_chevauchent_pas(self):
        for depart, arrivee, nom, categorie in ville.RUES:
            nombre = ville.voies(depart, arrivee)
            for voie in range(nombre - 1):
                premier = ville.decalage_voie(depart, arrivee, voie)
                second = ville.decalage_voie(depart, arrivee, voie + 1)
                self.assertAlmostEqual(abs(premier - second), ville.LARGEUR_VOIE)

    def test_une_petite_rue_qui_debouche_sur_une_avenue_a_un_panneau(self):
        for carrefour in ville.CARREFOURS:
            if ville.CARREFOURS[carrefour]["feux"]:
                continue

            il_y_a_une_avenue = False
            for voisin in ville.voisins(carrefour):
                if ville.categorie(carrefour, voisin) == "avenue":
                    il_y_a_une_avenue = True
            if not il_y_a_une_avenue:
                continue

            for voisin in ville.voisins(carrefour):
                if ville.categorie(carrefour, voisin) == "rue":
                    panneau = ville.panneau(carrefour, voisin)
                    self.assertIn(panneau, ("cedez", "stop"))

    def test_un_carrefour_a_feux_n_a_pas_de_panneau(self):
        for carrefour in ville.CARREFOURS:
            if not ville.CARREFOURS[carrefour]["feux"]:
                continue
            for voisin in ville.voisins(carrefour):
                self.assertIsNone(ville.panneau(carrefour, voisin))


if __name__ == "__main__":
    unittest.main()
