import random

from simulation.simulation import Simulation

PAS = 0.033
CHAUFFE = 30
LIMITE = 450
ESSAIS = 8
ITINERAIRE = ["O", "C1", "C2", "C3", "C4", "C5", "C6", "E"]


def un_trajet(priorite_active, densite, graine):
    random.seed(graine)
    simulation = Simulation()
    simulation.densite = densite
    simulation.priorite_active = priorite_active

    for i in range(int(CHAUFFE / PAS)):
        simulation.avancer(PAS)

    secours = None
    while secours is None:
        simulation.avancer(PAS)
        secours = simulation.lancer_un_secours(itineraire=ITINERAIRE)

    for i in range(int(LIMITE / PAS)):
        simulation.avancer(PAS)
        if secours.sorti:
            break

    return secours.temps_de_trajet


def moyenne(valeurs):
    return sum(valeurs) / len(valeurs)


def mesurer(densite):
    sans = []
    avec = []
    for graine in range(1, ESSAIS + 1):
        sans.append(un_trajet(False, densite, graine))
        avec.append(un_trajet(True, densite, graine))

    moyenne_sans = moyenne(sans)
    moyenne_avec = moyenne(avec)
    gain = (moyenne_sans - moyenne_avec) / moyenne_sans * 100
    return moyenne_sans, moyenne_avec, gain


def main():
    print("Temps de traversee du vehicule de secours")
    print("Moyenne sur " + str(ESSAIS) + " trajets, O vers E (1,1 km, 6 carrefours)")
    print("")
    print("densite   sans priorite   avec priorite   gain")

    for densite in (20, 60, 100):
        sans, avec, gain = mesurer(densite)
        print(str(densite).rjust(5) + " %"
              + str(round(sans, 1)).rjust(14) + " s"
              + str(round(avec, 1)).rjust(14) + " s"
              + str(round(gain, 1)).rjust(8) + " %")


if __name__ == "__main__":
    main()
