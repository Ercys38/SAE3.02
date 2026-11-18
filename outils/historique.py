import sys

from simulation.journal import Journal

NOMS = {"pompiers": "Pompiers", "samu": "SAMU", "police": "Police"}


def texte(valeur, largeur):
    if valeur is None:
        mot = "-"
    elif isinstance(valeur, float):
        mot = str(round(valeur, 1)) + " s"
    else:
        mot = str(valeur)
    return mot.ljust(largeur)


def ligne_de_tableau(ligne):
    identifiant, date, densite, service, depart, arrivee, avec, sans = ligne

    if avec is not None and sans is not None:
        gain = texte(sans - avec, 9)
    else:
        gain = texte(None, 9)

    return (texte(identifiant, 4) + texte(str(date), 21)
            + texte(str(densite) + " %", 8)
            + texte(NOMS.get(service, service), 10)
            + texte(depart + " vers " + arrivee, 14)
            + texte(avec, 10) + texte(sans, 10) + gain)


def main():
    nombre = 20
    if len(sys.argv) > 1:
        nombre = int(sys.argv[1])

    journal = Journal()
    print("Historique des interventions -", journal.nom)
    print("")
    print("id  date                 densite service   trajet        "
          "avec      sans      gain")
    print("-" * 94)

    lignes = journal.dernieres(nombre)
    for ligne in reversed(lignes):
        print(ligne_de_tableau(ligne))

    print("-" * 94)
    print(str(journal.nombre_d_interventions()) + " interventions"
          + "   |   gain moyen " + str(journal.gain_moyen()) + " s")
    journal.fermer()


if __name__ == "__main__":
    main()
