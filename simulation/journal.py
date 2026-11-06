import sqlite3
from datetime import datetime
from pathlib import Path

FICHIER = Path(__file__).resolve().parent.parent / "historique.db"

CREATION = """
CREATE TABLE IF NOT EXISTS interventions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    densite INTEGER NOT NULL,
    service TEXT NOT NULL,
    depart TEXT NOT NULL,
    arrivee TEXT NOT NULL,
    temps_avec REAL,
    temps_sans REAL
)
"""


class Journal:

    def __init__(self, fichier=FICHIER):
        self.nom = str(fichier)
        self.connexion = sqlite3.connect(self.nom, check_same_thread=False)
        self.connexion.execute(CREATION)
        self.connexion.commit()

    def enregistrer(self, densite, service, depart, arrivee,
                    temps_avec=None, temps_sans=None):
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        curseur = self.connexion.execute(
            "INSERT INTO interventions (date, densite, service, depart,"
            " arrivee, temps_avec, temps_sans) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (date, int(densite), service, depart, arrivee,
             temps_avec, temps_sans))
        self.connexion.commit()
        return curseur.lastrowid

    def completer(self, identifiant, temps_avec=None, temps_sans=None):
        if temps_avec is not None:
            self.connexion.execute(
                "UPDATE interventions SET temps_avec = ? WHERE id = ?",
                (temps_avec, identifiant))

        if temps_sans is not None:
            self.connexion.execute(
                "UPDATE interventions SET temps_sans = ? WHERE id = ?",
                (temps_sans, identifiant))

        self.connexion.commit()

    def dernieres(self, nombre=10):
        curseur = self.connexion.execute(
            "SELECT id, date, densite, service, depart, arrivee,"
            " temps_avec, temps_sans FROM interventions"
            " ORDER BY id DESC LIMIT ?", (nombre,))

        lignes = []
        for ligne in curseur.fetchall():
            lignes.append(ligne)
        return lignes

    def gain_moyen(self):
        curseur = self.connexion.execute(
            "SELECT AVG(temps_sans - temps_avec) FROM interventions"
            " WHERE temps_avec IS NOT NULL AND temps_sans IS NOT NULL")

        valeur = curseur.fetchone()[0]
        if valeur is None:
            return 0.0
        return round(valeur, 1)

    def nombre_d_interventions(self):
        curseur = self.connexion.execute(
            "SELECT COUNT(*) FROM interventions")
        return curseur.fetchone()[0]

    def fermer(self):
        self.connexion.close()
