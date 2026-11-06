import os
import time
import unittest

from simulation import messages
from simulation.feux import Feu
from simulation.journal import Journal
from simulation.superviseur import Superviseur
from simulation.reseau import (Serveur, ClientSuperviseur,
                               Annonceur, trouver_le_superviseur)

PORT = 9321
PORT_ANNONCE = 9322
BASE = "essai_tests.db"


def attendre(condition, limite=2.0):
    debut = time.time()
    while time.time() - debut < limite:
        if condition():
            return True
        time.sleep(0.02)
    return False


class TestMessages(unittest.TestCase):

    def test_un_message_contient_les_quatre_champs(self):
        message = messages.accord_priorite("C3", "vertical")
        for champ in ("type", "emetteur", "heure", "contenu"):
            self.assertIn(champ, message)

    def test_encoder_puis_decoder_redonne_le_message(self):
        message = messages.alerte_proximite("C2", "horizontal", 120.0)
        self.assertEqual(messages.decoder(messages.encoder(message)), message)

    def test_un_type_inconnu_est_refuse(self):
        with self.assertRaises(ValueError):
            messages.creer("bidon", "7")

    def test_un_message_incomplet_est_refuse(self):
        with self.assertRaises(ValueError):
            messages.decoder('{"type": "position"}')


class TestJournal(unittest.TestCase):

    def setUp(self):
        if os.path.exists(BASE):
            os.remove(BASE)
        self.journal = Journal(BASE)

    def tearDown(self):
        self.journal.fermer()
        if os.path.exists(BASE):
            os.remove(BASE)

    def test_une_intervention_est_enregistree(self):
        self.journal.enregistrer(60, "samu", "S2", "N3", 40.0, 55.0)
        self.assertEqual(self.journal.nombre_d_interventions(), 1)

    def test_les_temps_peuvent_etre_completes_apres_coup(self):
        identifiant = self.journal.enregistrer(60, "pompiers", "N1", "N4")
        self.journal.completer(identifiant, temps_avec=41.2)
        self.journal.completer(identifiant, temps_sans=58.9)
        ligne = self.journal.dernieres(1)[0]
        self.assertEqual(ligne[6], 41.2)
        self.assertEqual(ligne[7], 58.9)

    def test_le_gain_moyen_est_la_moyenne_des_ecarts(self):
        self.journal.enregistrer(60, "samu", "S2", "N3", 40.0, 50.0)
        self.journal.enregistrer(60, "samu", "S2", "N3", 30.0, 50.0)
        self.assertEqual(self.journal.gain_moyen(), 15.0)


class TestSuperviseur(unittest.TestCase):

    def setUp(self):
        self.feux = {"C3": Feu(axe_passant="horizontal")}
        self.superviseur = Superviseur(self.feux)

    def position(self, emetteur, distance):
        return messages.creer(messages.POSITION, emetteur,
                              {"service": "samu", "carrefour": "C3",
                               "distance": distance, "axe": "vertical"})

    def test_un_secours_trop_loin_n_obtient_rien(self):
        self.superviseur.traiter(self.position("7", 800.0))
        self.assertIsNone(self.feux["C3"].priorite)

    def test_un_secours_a_moins_de_500_m_declenche_une_alerte(self):
        self.superviseur.traiter(self.position("7", 420.0))
        self.assertIsNone(self.feux["C3"].priorite)
        types = []
        for message in self.superviseur.messages_en_attente():
            types.append(message["type"])
        self.assertIn(messages.ALERTE_PROXIMITE, types)

    def test_un_secours_proche_obtient_le_vert(self):
        self.superviseur.traiter(self.position("7", 120.0))
        self.assertEqual(self.feux["C3"].priorite, "vertical")

    def test_le_carrefour_n_est_pas_donne_a_deux_vehicules(self):
        self.superviseur.traiter(self.position("7", 120.0))
        self.superviseur.traiter(
            messages.creer(messages.DEMANDE_PRIORITE, "8",
                           {"carrefour": "C3", "axe": "horizontal"}))
        self.assertEqual(self.feux["C3"].priorite, "vertical")

    def test_la_liberation_rend_le_carrefour(self):
        self.superviseur.traiter(self.position("7", 120.0))
        self.superviseur.traiter(
            messages.creer(messages.LIBERATION, "7", {"carrefour": "C3"}))
        self.assertIsNone(self.feux["C3"].priorite)

    def test_un_autre_vehicule_ne_peut_pas_liberer(self):
        self.superviseur.traiter(self.position("7", 120.0))
        self.superviseur.traiter(
            messages.creer(messages.LIBERATION, "8", {"carrefour": "C3"}))
        self.assertEqual(self.feux["C3"].priorite, "vertical")

    def test_un_carrefour_sans_feux_est_ignore(self):
        self.superviseur.accorder("7", "C9", "vertical")
        self.assertEqual(self.superviseur.priorites, {})


class TestReseau(unittest.TestCase):

    def setUp(self):
        self.feux = {"C3": Feu(axe_passant="horizontal")}
        self.superviseur = Superviseur()
        self.serveur = Serveur(self.superviseur, port=PORT)
        self.superviseur.demarrer()
        self.serveur.demarrer()
        time.sleep(0.2)
        self.client = ClientSuperviseur("127.0.0.1", PORT, self.feux)

    def tearDown(self):
        self.client.arreter()
        self.serveur.arreter()
        self.superviseur.arreter()

    def test_le_serveur_recoit_ce_que_le_client_envoie(self):
        self.client.envoyer(messages.creer(messages.POSITION, "7",
                            {"service": "samu", "carrefour": "C3",
                             "distance": 120.0, "axe": "vertical"}))
        self.assertTrue(attendre(lambda: self.superviseur.recus >= 1))

    def test_le_client_recoit_l_accord_de_priorite(self):
        self.client.envoyer(messages.creer(messages.POSITION, "7",
                            {"service": "samu", "carrefour": "C3",
                             "distance": 120.0, "axe": "vertical"}))

        recus = []

        def arrive():
            for message in self.client.messages_en_attente():
                recus.append(message["type"])
            return messages.ACCORD_PRIORITE in recus

        self.assertTrue(attendre(arrive))

    def test_le_superviseur_distant_tient_ses_priorites(self):
        self.client.envoyer(messages.creer(messages.POSITION, "7",
                            {"service": "samu", "carrefour": "C3",
                             "distance": 120.0, "axe": "vertical"}))
        self.assertTrue(attendre(
            lambda: "C3" in self.superviseur.priorites))


class TestDecouverte(unittest.TestCase):

    def setUp(self):
        self.annonceur = Annonceur(port_du_serveur=PORT, port=PORT_ANNONCE)
        self.annonceur.demarrer()
        time.sleep(0.2)

    def tearDown(self):
        self.annonceur.arreter()

    def test_le_superviseur_est_trouve_sans_adresse(self):
        adresse = trouver_le_superviseur(delai=2.0, port=PORT_ANNONCE)
        self.assertIsNotNone(adresse)
        self.assertEqual(adresse[1], PORT)

    def test_rien_n_est_trouve_quand_personne_n_annonce(self):
        self.annonceur.arreter()
        adresse = trouver_le_superviseur(delai=1.0, port=PORT_ANNONCE)
        self.assertIsNone(adresse)
