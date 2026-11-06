import os
import sqlite3
from datetime import datetime
from pathlib import Path

FICHIER = Path(__file__).resolve().parent.parent / "historique.db"

HOTE = os.environ.get("SAE_DB_HOTE", "127.0.0.1")
UTILISATEUR = os.environ.get("SAE_DB_UTILISATEUR", "sae")
MOT_DE_PASSE = os.environ.get("SAE_DB_MOT_DE_PASSE", "sae")
NOM_DE_LA_BASE = os.environ.get("SAE_DB_NOM", "sae302")

COLONNES = ("id", "date", "densite", "service", "depart", "arrivee",
            "temps_avec", "temps_sans")

CREATION_SQLITE = """
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

CREATION_MARIADB = """
CREATE TABLE IF NOT EXISTS interventions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATETIME NOT NULL,
    densite INT NOT NULL,
    service VARCHAR(20) NOT NULL,
    depart VARCHAR(10) NOT NULL,
    arrivee VARCHAR(10) NOT NULL,
    temps_avec DOUBLE,
    temps_sans DOUBLE
)
"""

INSERTION = ("INSERT INTO interventions (date, densite, service, depart,"
             " arrivee, temps_avec, temps_sans)"
             " VALUES ({0}, {0}, {0}, {0}, {0}, {0}, {0})")

LECTURE = ("SELECT id, date, densite, service, depart, arrivee,"
           " temps_avec, temps_sans FROM interventions"
           " ORDER BY id DESC LIMIT {0}")

MOYENNE = ("SELECT AVG(temps_sans - temps_avec) FROM interventions"
           " WHERE temps_avec IS NOT NULL AND temps_sans IS NOT NULL")


class Journal:

    marque = "?"
    creation = CREATION_SQLITE

    def __init__(self, fichier=FICHIER):
        self.nom = str(fichier)
        self.connexion = sqlite3.connect(self.nom, check_same_thread=False)
        self.preparer()

    def preparer(self):
        curseur = self.connexion.cursor()
        curseur.execute(self.creation)
        self.connexion.commit()
        curseur.close()

    def executer(self, requete, valeurs=()):
        curseur = self.connexion.cursor()
        curseur.execute(requete, valeurs)
        return curseur

    def enregistrer(self, densite, service, depart, arrivee,
                    temps_avec=None, temps_sans=None):
        curseur = self.executer(
            INSERTION.format(self.marque),
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), int(densite),
             service, depart, arrivee, temps_avec, temps_sans))
        self.connexion.commit()
        identifiant = curseur.lastrowid
        curseur.close()
        return identifiant

    def completer(self, identifiant, temps_avec=None, temps_sans=None):
        for colonne, valeur in (("temps_avec", temps_avec),
                                ("temps_sans", temps_sans)):
            if valeur is None:
                continue
            requete = ("UPDATE interventions SET " + colonne + " = " +
                       self.marque + " WHERE id = " + self.marque)
            self.executer(requete, (valeur, identifiant)).close()
        self.connexion.commit()

    def dernieres(self, nombre=10):
        curseur = self.executer(LECTURE.format(self.marque), (nombre,))
        lignes = curseur.fetchall()
        curseur.close()

        resultat = []
        for ligne in lignes:
            resultat.append(tuple(ligne))
        return resultat

    def gain_moyen(self):
        curseur = self.executer(MOYENNE)
        valeur = curseur.fetchone()[0]
        curseur.close()
        if valeur is None:
            return 0.0
        return round(float(valeur), 1)

    def nombre_d_interventions(self):
        curseur = self.executer("SELECT COUNT(*) FROM interventions")
        nombre = curseur.fetchone()[0]
        curseur.close()
        return nombre

    def fermer(self):
        self.connexion.close()


class JournalMariaDB(Journal):

    marque = "%s"
    creation = CREATION_MARIADB

    def __init__(self, hote=HOTE, utilisateur=UTILISATEUR,
                 mot_de_passe=MOT_DE_PASSE, base=NOM_DE_LA_BASE):
        import pymysql

        self.nom = utilisateur + "@" + hote + "/" + base
        self.connexion = pymysql.connect(host=hote, user=utilisateur,
                                         password=mot_de_passe, database=base,
                                         autocommit=False, charset="utf8mb4")
        self.preparer()


def ouvrir_un_journal(prefere_mariadb=True):
    if prefere_mariadb:
        try:
            return JournalMariaDB()
        except Exception as erreur:
            print("MariaDB indisponible (" + str(erreur) + ")")
            print("la base SQLite locale prend le relais")

    return Journal()
