import math
import tkinter as tk

from . import ville
from . import code_route
from .feux import VERT, ORANGE, ROUGE
from .vehicule import LONGUEUR_VOITURE, LARGEUR_VOITURE

ECHELLE = 0.7
MARGE = 30
PERIODE = 33
VITESSE_MAX = 5

FOND = "#eeeee8"
BITUME = "#787a80"
BITUME_PETIT = "#9a9ea4"
BANDE = "#f4f4f0"
CARREFOUR = "#606268"
CROISEMENT = "#9a9ea4"
TEXTE = "#46464b"
TEXTE_PETIT = "#7d7d82"

CIVIL = "#3e609e"
CIVIL_ARRETE = "#263a66"

SERVICES = ("pompiers", "samu", "police")

COULEURS_SECOURS = {
    "pompiers": "#d4342c",
    "samu": "#e9c93a",
    "police": "#23356e",
}

NOMS_SERVICE = {
    "pompiers": "Pompiers",
    "samu": "SAMU",
    "police": "Police",
}

BATIMENT_BORD = "#3b3b40"
ILOT = "#8ca877"
ILOT_BORD = "#f4f4f0"
INTERVENTION = "#e0562a"

COULEURS_FEU = {VERT: "#2eae5c", ORANGE: "#e8a328", ROUGE: "#ce3f3c"}

ROUGE_PANNEAU = "#c8372f"
BLANC = "#fafafa"


def carrefours_a_feux():
    liste = []
    for nom in ville.CARREFOURS:
        if ville.CARREFOURS[nom]["feux"]:
            liste.append(nom)
    return liste


def en_pixels(position):
    x, y = position
    return (x * ECHELLE + MARGE, y * ECHELLE + MARGE)


def points_de_la_rue(depart, arrivee, ecart):
    dx, dy = ville.tangente_rue(depart, arrivee, 0.0)

    points = []
    for part in (0.0, 1.0):
        x, y = ville.point_sur_rue(depart, arrivee, part)
        px, py = en_pixels((x - dy * ecart, y + dx * ecart))
        points.append(px)
        points.append(py)
    return points


class Fenetre:

    def __init__(self, simulation):
        self.simulation = simulation
        self.facteur = 1
        self.secours = None
        self.appel_en_attente = None

        largeur_m, hauteur_m = ville.taille_ville()
        self.largeur = int(largeur_m * ECHELLE) + 2 * MARGE
        self.hauteur = int(hauteur_m * ECHELLE) + 2 * MARGE

        self.racine = tk.Tk()
        self.racine.title("SAE R3.02 - Avenue de Bale")
        self.racine.resizable(False, False)

        self.construire_les_commandes()

        self.toile = tk.Canvas(self.racine, width=self.largeur,
                               height=self.hauteur, background=FOND,
                               highlightthickness=0)
        self.toile.pack()

        self.dessiner_les_rues()
        self.dessiner_les_ronds_points()
        self.dessiner_les_fleches()
        self.dessiner_les_noms()
        self.dessiner_les_carrefours()
        self.dessiner_les_panneaux()
        self.dessiner_les_batiments()

        self.marqueur = self.toile.create_oval(
            0, 0, 0, 0, outline=INTERVENTION, width=2.5, state="hidden")

        self.formes_feux = self.creer_les_feux()
        self.formes_vehicules = []

        self.etiquette_bas = self.toile.create_text(
            MARGE - 10, self.hauteur - 14, anchor="w", fill=TEXTE,
            font=("TkDefaultFont", 8), text="")

    def construire_les_commandes(self):
        self.ajouter_un_curseur("Densite de circulation", 0, 100, 1,
                                self.simulation.densite, self.changer_densite)
        self.ajouter_un_curseur("Vitesse de la simulation", 1, VITESSE_MAX, 1,
                                1, self.changer_vitesse)
        self.ajouter_un_curseur("Vitesse autorisee", 30, 90, 10,
                                50, self.changer_limite)
        self.construire_les_appels()
        self.construire_la_legende()

    def ajouter_un_curseur(self, titre, de, a, pas, valeur, action):
        barre = tk.Frame(self.racine)
        barre.pack(fill="x", padx=MARGE - 10, pady=(0, 2))

        tk.Label(barre, text=titre, width=20, anchor="w").pack(side="left")
        etiquette = tk.Label(barre, text="", width=8, anchor="w")

        def changer(position):
            etiquette.configure(text=action(int(float(position))))

        curseur = tk.Scale(barre, from_=de, to=a, resolution=pas,
                           orient="horizontal", length=300, showvalue=False,
                           command=changer)
        curseur.set(valeur)
        curseur.pack(side="left", padx=10)
        etiquette.pack(side="left")

    def construire_les_appels(self):
        barre = tk.Frame(self.racine)
        barre.pack(fill="x", padx=MARGE - 10, pady=(0, 2))

        tk.Label(barre, text="Appeler", width=20, anchor="w").pack(side="left")

        for service in SERVICES:
            tk.Button(barre, text=NOMS_SERVICE[service],
                      command=self.appel_du_service(service)
                      ).pack(side="left", padx=3)

        self.case_priorite = tk.IntVar(value=1)
        tk.Checkbutton(barre, text="Priorite aux feux",
                       variable=self.case_priorite,
                       command=self.changer_priorite).pack(side="left", padx=10)

    def construire_la_legende(self):
        barre = tk.Frame(self.racine)
        barre.pack(fill="x", padx=MARGE - 10, pady=(0, 8))

        tk.Label(barre, text="Legende", width=20, anchor="w").pack(side="left")

        for service in SERVICES:
            self.ajouter_une_pastille(barre, COULEURS_SECOURS[service],
                                      NOMS_SERVICE[service])
        self.ajouter_une_pastille(barre, CIVIL, "Civils")

        self.etiquette_secours = tk.Label(barre, text="", anchor="w")
        self.etiquette_secours.pack(side="left", padx=14)

    def ajouter_une_pastille(self, barre, couleur, texte):
        tk.Label(barre, text="   ", relief="solid", borderwidth=1,
                 background=couleur).pack(side="left", padx=(8, 3))
        tk.Label(barre, text=texte).pack(side="left")

    def changer_densite(self, valeur):
        self.simulation.densite = valeur
        return str(valeur) + " %"

    def changer_vitesse(self, valeur):
        self.facteur = valeur
        return "x " + str(valeur)

    def changer_limite(self, valeur):
        self.simulation.regler_la_vitesse(valeur)
        return str(valeur) + " km/h"

    def changer_priorite(self):
        self.simulation.priorite_active = self.case_priorite.get() == 1

    def appel_du_service(self, service):
        def appeler():
            self.appel_en_attente = service
        return appeler

    def dessiner_les_rues(self):
        for categorie in ("rue", "avenue"):
            if categorie == "avenue":
                couleur = BITUME
                epaisseur = ville.LARGEUR_VOIE * ECHELLE * 4
            else:
                couleur = BITUME_PETIT
                epaisseur = ville.LARGEUR_VOIE * ECHELLE * 2

            for depart, arrivee, nom, cat in ville.RUES:
                if cat != categorie:
                    continue
                self.toile.create_line(points_de_la_rue(depart, arrivee, 0),
                                       fill=couleur, width=epaisseur,
                                       capstyle="round", joinstyle="round")

        for depart, arrivee, nom, cat in ville.RUES:
            self.toile.create_line(points_de_la_rue(depart, arrivee, 0),
                                   fill=BANDE, width=1.4)

            if cat != "avenue":
                continue
            for cote in (-1, 1):
                ecart = ville.LARGEUR_VOIE * cote
                self.toile.create_line(
                    points_de_la_rue(depart, arrivee, ecart),
                    fill=BANDE, width=1.1, dash=(5, 6))

    def dessiner_les_ronds_points(self):
        for nom in ville.CARREFOURS:
            if not ville.est_un_rond_point(nom):
                continue

            x, y = en_pixels(ville.position(nom))
            rayon = code_route.RAYON_ROND_POINT * ECHELLE
            bord = ville.LARGEUR_VOIE * ECHELLE
            dehors = rayon + bord
            dedans = rayon - bord

            self.toile.create_oval(x - dehors, y - dehors,
                                   x + dehors, y + dehors,
                                   fill=BITUME, outline="")
            self.toile.create_oval(x - dedans, y - dedans,
                                   x + dedans, y + dedans,
                                   fill=ILOT, outline=ILOT_BORD, width=1.4)

    def dessiner_les_noms(self):
        deja_ecrits = []

        for depart, arrivee, nom, cat in ville.RUES:
            if nom in deja_ecrits:
                continue
            deja_ecrits.append(nom)

            x, y = en_pixels(ville.point_sur_rue(depart, arrivee, 0.5))

            if cat == "avenue":
                couleur = TEXTE
                taille = 8
                ecart = 26
            else:
                couleur = TEXTE_PETIT
                taille = 7
                ecart = 16

            if ville.axe(depart, arrivee) == "horizontal":
                self.toile.create_text(x, y - ecart, text=nom, fill=couleur,
                                       font=("TkDefaultFont", taille))
            else:
                self.toile.create_text(x - ecart, y, text=nom, fill=couleur,
                                       font=("TkDefaultFont", taille),
                                       angle=90)

    def dessiner_les_fleches(self):
        for centre in carrefours_a_feux():
            self.fleches_d_un_carrefour(centre)

    def fleches_d_un_carrefour(self, centre):
        for voisin in ville.voisins(centre):
            if ville.longueur(voisin, centre) < 80:
                continue

            for voie in range(ville.voies(voisin, centre)):
                ecart = ville.decalage_voie(voisin, centre, voie)
                base = self.point_de_voie(voisin, centre, 64, ecart)
                corps = self.point_de_voie(voisin, centre, 44, ecart)
                pointe = self.point_de_voie(voisin, centre, 34, ecart)
                gauche = self.point_de_voie(voisin, centre, 44, ecart + 4.0)
                droite = self.point_de_voie(voisin, centre, 44, ecart - 4.0)

                self.toile.create_line(base[0], base[1], corps[0], corps[1],
                                       fill=BANDE, width=3)
                self.toile.create_polygon(pointe[0], pointe[1],
                                          gauche[0], gauche[1],
                                          droite[0], droite[1], fill=BANDE)

    def point_de_voie(self, depart, arrivee, recul, ecart):
        longueur = max(ville.longueur(depart, arrivee), 1.0)
        part = max(1.0 - recul / longueur, 0.0)

        x, y = ville.point_sur_rue(depart, arrivee, part)
        dx, dy = ville.tangente_rue(depart, arrivee, part)
        return en_pixels((x - dy * ecart, y + dx * ecart))

    def dessiner_les_carrefours(self):
        for nom in ville.CARREFOURS:
            x, y = en_pixels(ville.position(nom))

            if ville.est_un_rond_point(nom):
                decalage = code_route.RAYON_ROND_POINT * ECHELLE + 14
                self.toile.create_text(x, y - decalage, text=nom, fill=TEXTE,
                                       font=("TkDefaultFont", 7, "bold"))
                continue

            if ville.CARREFOURS[nom]["feux"]:
                c = ville.LARGEUR_VOIE * ECHELLE * 2
                self.toile.create_rectangle(x - c, y - c, x + c, y + c,
                                            fill=CARREFOUR, outline="")
                self.toile.create_text(x, y - c - 9, text=nom, fill=TEXTE,
                                       font=("TkDefaultFont", 7, "bold"))
            else:
                self.toile.create_rectangle(x - 4, y - 4, x + 4, y + 4,
                                            fill=CROISEMENT, outline="")

    def dessiner_les_panneaux(self):
        for carrefour in ville.CARREFOURS:
            for voisin in ville.voisins(carrefour):
                panneau = ville.panneau(carrefour, voisin)
                if panneau is None:
                    continue

                x, y = self.point_de_voie(voisin, carrefour, 21, -9)
                if panneau == "cedez":
                    self.dessiner_un_cedez(x, y)
                else:
                    self.dessiner_un_stop(x, y)

    def dessiner_un_cedez(self, x, y):
        self.toile.create_polygon(x - 5, y - 4, x + 5, y - 4, x, y + 5,
                                  fill=BLANC, outline=ROUGE_PANNEAU,
                                  width=1.6)

    def dessiner_un_stop(self, x, y):
        points = []
        for i in range(8):
            angle = math.radians(22.5 + 45 * i)
            points.append(x + 5 * math.cos(angle))
            points.append(y + 5 * math.sin(angle))
        self.toile.create_polygon(points, fill=ROUGE_PANNEAU,
                                  outline=BLANC, width=1.2)

    def dessiner_les_batiments(self):
        for nom in ville.BATIMENTS:
            infos = ville.BATIMENTS[nom]
            x, y = en_pixels(infos["pos"])

            self.toile.create_rectangle(
                x - 11, y - 8, x + 11, y + 8,
                fill=COULEURS_SECOURS[infos["service"]],
                outline=BATIMENT_BORD)
            self.toile.create_text(x, y + 17, text=nom, fill=TEXTE_PETIT,
                                   font=("TkDefaultFont", 7))

    def creer_les_feux(self):
        formes = {}
        for nom in self.simulation.feux:
            for voisin in ville.voisins(nom):
                x, y = self.point_de_voie(voisin, nom, 21, 0)
                formes[(nom, voisin)] = self.toile.create_oval(
                    x - 5.2, y - 5.2, x + 5.2, y + 5.2,
                    fill=COULEURS_FEU[ROUGE], outline="#282828")
        return formes

    def battement(self):
        for i in range(self.facteur):
            self.simulation.avancer(PERIODE / 1000)
        self.rafraichir()
        self.racine.after(PERIODE, self.battement)

    def rafraichir(self):
        self.rafraichir_les_feux()
        self.rafraichir_les_vehicules()
        self.rafraichir_l_appel()
        self.rafraichir_l_intervention()

        self.toile.itemconfigure(
            self.etiquette_bas,
            text=str(len(self.simulation.vehicules)) + " voitures   |   "
                 + "temps ecoule : " + str(int(self.simulation.temps)) + " s")

    def rafraichir_les_feux(self):
        for carrefour, voisin in self.formes_feux:
            feu = self.simulation.feux[carrefour]
            etat = feu.couleur(ville.axe(voisin, carrefour))
            self.toile.itemconfigure(self.formes_feux[(carrefour, voisin)],
                                     fill=COULEURS_FEU[etat])

    def rafraichir_l_appel(self):
        if self.appel_en_attente is None:
            return

        nouveau = self.simulation.lancer_un_secours(self.appel_en_attente)
        if nouveau is not None:
            self.secours = nouveau
            self.appel_en_attente = None

    def rafraichir_l_intervention(self):
        if self.secours is None:
            self.etiquette_secours.configure(text="")
            self.toile.itemconfigure(self.marqueur, state="hidden")
            return

        nom = NOMS_SERVICE[self.secours.service]
        chrono = str(round(self.secours.temps_de_trajet, 1)) + " s"

        if self.secours.arrive:
            self.etiquette_secours.configure(text=nom + " arrive en " + chrono)
            self.toile.itemconfigure(self.marqueur, state="hidden")
            return

        self.etiquette_secours.configure(text=nom + " en route : " + chrono)

        if self.secours.destination is None:
            return

        x, y = en_pixels(ville.position(self.secours.destination))
        self.toile.coords(self.marqueur, x - 11, y - 11, x + 11, y + 11)
        self.toile.itemconfigure(self.marqueur, state="normal")

    def rafraichir_les_vehicules(self):
        vehicules = self.simulation.vehicules

        while len(self.formes_vehicules) < len(vehicules):
            self.formes_vehicules.append(
                self.toile.create_polygon(0, 0, 0, 0, 0, 0, 0, 0, fill=CIVIL))

        for i in range(len(vehicules), len(self.formes_vehicules)):
            self.toile.itemconfigure(self.formes_vehicules[i], state="hidden")

        for i in range(len(vehicules)):
            self.placer_un_vehicule(vehicules[i], self.formes_vehicules[i])

    def placer_un_vehicule(self, vehicule, forme):
        demi_longueur = LONGUEUR_VOITURE * ECHELLE / 2
        demi_largeur = LARGEUR_VOITURE * ECHELLE / 2

        x, y = en_pixels(vehicule.position())
        dx, dy = vehicule.direction()
        px = -dy
        py = dx

        self.toile.coords(
            forme,
            x + dx * demi_longueur + px * demi_largeur,
            y + dy * demi_longueur + py * demi_largeur,
            x + dx * demi_longueur - px * demi_largeur,
            y + dy * demi_longueur - py * demi_largeur,
            x - dx * demi_longueur - px * demi_largeur,
            y - dy * demi_longueur - py * demi_largeur,
            x - dx * demi_longueur + px * demi_largeur,
            y - dy * demi_longueur + py * demi_largeur)

        if vehicule.prioritaire:
            couleur = COULEURS_SECOURS[vehicule.service]
        elif vehicule.vitesse < 0.3:
            couleur = CIVIL_ARRETE
        else:
            couleur = CIVIL

        self.toile.itemconfigure(forme, fill=couleur, state="normal")

    def lancer(self):
        self.battement()
        self.racine.mainloop()
