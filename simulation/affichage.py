import math
import tkinter as tk

from . import ville
from .feux import VERT, ORANGE, ROUGE
from .vehicule import LONGUEUR_VOITURE, LARGEUR_VOITURE

ECHELLE = 2.0
MARGE = 30
TAILLE_FENETRE = 620
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
SECOURS = "#ce3732"

COULEURS_FEU = {VERT: "#2eae5c", ORANGE: "#e8a328", ROUGE: "#ce3f3c"}

ROUGE_PANNEAU = "#c8372f"
BLANC = "#fafafa"


def carrefour_principal():
    for nom in ville.CARREFOURS:
        if ville.CARREFOURS[nom]["principal"]:
            return nom
    return list(ville.CARREFOURS)[0]


CENTRE = ville.position(carrefour_principal())


def en_pixels(position):
    x, y = position
    return ((x - CENTRE[0]) * ECHELLE + TAILLE_FENETRE / 2,
            (y - CENTRE[1]) * ECHELLE + TAILLE_FENETRE / 2)


class Fenetre:
    def __init__(self, simulation):
        self.simulation = simulation
        self.facteur = 1
        self.secours = None
        self.appel_en_attente = False

        self.largeur = TAILLE_FENETRE
        self.hauteur = TAILLE_FENETRE

        self.racine = tk.Tk()
        self.racine.title("SAE R3.02 - carrefour connecte")
        self.racine.resizable(False, False)

        self.construire_les_commandes()

        self.toile = tk.Canvas(self.racine, width=self.largeur,
                               height=self.hauteur, background=FOND,
                               highlightthickness=0)
        self.toile.pack()

        self.dessiner_les_rues()
        self.dessiner_les_fleches()
        self.dessiner_les_noms()
        self.dessiner_les_carrefours()
        self.dessiner_les_panneaux()

        self.formes_feux = self.creer_les_feux()
        self.formes_vehicules = []

        self.etiquette_bas = self.toile.create_text(
            MARGE - 10, self.hauteur - 14, anchor="w", fill=TEXTE,
            font=("TkDefaultFont", 8), text="")

        self.toile.create_text(
            MARGE - 10, 24, anchor="w", fill=TEXTE,
            font=("TkDefaultFont", 9),
            text="Avenue de Bale / Rue du Moulin")

    def construire_les_commandes(self):
        barre = tk.Frame(self.racine)
        barre.pack(fill="x", padx=MARGE - 10, pady=(0, 2))

        titre = tk.Label(barre, text="Densite de circulation", width=20,
                         anchor="w")
        titre.pack(side="left")

        self.curseur_densite = tk.Scale(barre, from_=0, to=100,
                                        orient="horizontal", length=300,
                                        showvalue=False,
                                        command=self.changer_densite)
        self.curseur_densite.set(self.simulation.densite)
        self.curseur_densite.pack(side="left", padx=10)

        self.etiquette_densite = tk.Label(barre, text="", width=8, anchor="w")
        self.etiquette_densite.pack(side="left")

        barre2 = tk.Frame(self.racine)
        barre2.pack(fill="x", padx=MARGE - 10, pady=(0, 2))

        titre2 = tk.Label(barre2, text="Vitesse de la simulation", width=20,
                          anchor="w")
        titre2.pack(side="left")

        self.curseur_vitesse = tk.Scale(barre2, from_=1, to=VITESSE_MAX,
                                        orient="horizontal", length=300,
                                        showvalue=False,
                                        command=self.changer_vitesse)
        self.curseur_vitesse.set(1)
        self.curseur_vitesse.pack(side="left", padx=10)

        self.etiquette_vitesse = tk.Label(barre2, text="", width=8, anchor="w")
        self.etiquette_vitesse.pack(side="left")

        barre3 = tk.Frame(self.racine)
        barre3.pack(fill="x", padx=MARGE - 10, pady=(0, 8))

        titre3 = tk.Label(barre3, text="Vitesse autorisee", width=20,
                          anchor="w")
        titre3.pack(side="left")

        self.curseur_limite = tk.Scale(barre3, from_=30, to=90, resolution=10,
                                       orient="horizontal", length=300,
                                       showvalue=False,
                                       command=self.changer_limite)
        self.curseur_limite.set(50)
        self.curseur_limite.pack(side="left", padx=10)

        self.etiquette_limite = tk.Label(barre3, text="", width=8, anchor="w")
        self.etiquette_limite.pack(side="left")

        barre4 = tk.Frame(self.racine)
        barre4.pack(fill="x", padx=MARGE - 10, pady=(0, 8))

        self.bouton_secours = tk.Button(barre4,
                                        text="Appeler un vehicule de secours",
                                        command=self.appeler_les_secours)
        self.bouton_secours.pack(side="left")

        self.case_priorite = tk.IntVar(value=1)
        case = tk.Checkbutton(barre4, text="Priorite aux feux",
                              variable=self.case_priorite,
                              command=self.changer_priorite)
        case.pack(side="left", padx=10)

        self.etiquette_secours = tk.Label(barre4, text="", anchor="w")
        self.etiquette_secours.pack(side="left", padx=10)

        self.changer_densite(self.simulation.densite)
        self.changer_vitesse(1)
        self.changer_limite(50)

    def changer_densite(self, valeur):
        self.simulation.densite = int(valeur)
        self.etiquette_densite.configure(text=str(int(valeur)) + " %")

    def changer_vitesse(self, valeur):
        self.facteur = int(valeur)
        self.etiquette_vitesse.configure(text="x " + str(int(valeur)))

    def changer_limite(self, valeur):
        self.simulation.regler_la_vitesse(int(valeur))
        self.etiquette_limite.configure(text=str(int(valeur)) + " km/h")

    def changer_priorite(self):
        self.simulation.priorite_active = self.case_priorite.get() == 1

    def appeler_les_secours(self):
        self.appel_en_attente = True

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
                x1, y1 = en_pixels(ville.position(depart))
                x2, y2 = en_pixels(ville.position(arrivee))
                self.toile.create_line(x1, y1, x2, y2, fill=couleur,
                                       width=epaisseur, capstyle="round")

        for depart, arrivee, nom, cat in ville.RUES:
            x1, y1 = en_pixels(ville.position(depart))
            x2, y2 = en_pixels(ville.position(arrivee))
            self.toile.create_line(x1, y1, x2, y2, fill=BANDE, width=1.4)

            if cat != "avenue":
                continue

            dx = x2 - x1
            dy = y2 - y1
            d = (dx * dx + dy * dy) ** 0.5
            if d < 1:
                d = 1
            nx = -dy / d
            ny = dx / d

            for cote in (-1, 1):
                ecart = ville.LARGEUR_VOIE * ECHELLE * cote
                self.toile.create_line(x1 + nx * ecart, y1 + ny * ecart,
                                       x2 + nx * ecart, y2 + ny * ecart,
                                       fill=BANDE, width=1.1, dash=(5, 6))

    def dessiner_les_noms(self):
        centre = carrefour_principal()
        xc, yc = ville.position(centre)
        deja_ecrits = []

        for depart, arrivee, nom, cat in ville.RUES:
            if nom in deja_ecrits:
                continue
            deja_ecrits.append(nom)

            if depart == centre:
                bout = arrivee
            else:
                bout = depart

            xb, yb = ville.position(bout)
            d = ((xb - xc) ** 2 + (yb - yc) ** 2) ** 0.5
            if d < 1:
                d = 1
            ux = (xb - xc) / d
            uy = (yb - yc) / d

            x, y = en_pixels((xc + ux * 110, yc + uy * 110))

            if cat == "avenue":
                couleur = TEXTE
                taille = 9
            else:
                couleur = TEXTE_PETIT
                taille = 8

            if ville.axe(depart, arrivee) == "horizontal":
                self.toile.create_text(x, y - 34, text=nom, fill=couleur,
                                       font=("TkDefaultFont", taille))
            else:
                self.toile.create_text(x - 34, y, text=nom, fill=couleur,
                                       font=("TkDefaultFont", taille),
                                       angle=90)

    def dessiner_les_fleches(self):
        centre = carrefour_principal()
        xc, yc = ville.position(centre)

        for voisin in ville.voisins(centre):
            xv, yv = ville.position(voisin)
            d = ((xv - xc) ** 2 + (yv - yc) ** 2) ** 0.5
            if d < 1:
                d = 1
            ux = (xv - xc) / d
            uy = (yv - yc) / d
            droite_x = uy
            droite_y = -ux

            for voie in range(ville.voies(voisin, centre)):
                ecart = ville.decalage_voie(voisin, centre, voie)

                base = (xc + ux * 64 + droite_x * ecart,
                        yc + uy * 64 + droite_y * ecart)
                corps = (xc + ux * 44 + droite_x * ecart,
                         yc + uy * 44 + droite_y * ecart)
                pointe = (xc + ux * 34 + droite_x * ecart,
                          yc + uy * 34 + droite_y * ecart)
                gauche = (corps[0] + droite_x * 4.0, corps[1] + droite_y * 4.0)
                droite = (corps[0] - droite_x * 4.0, corps[1] - droite_y * 4.0)

                x1, y1 = en_pixels(base)
                x2, y2 = en_pixels(corps)
                self.toile.create_line(x1, y1, x2, y2, fill=BANDE, width=3)

                xp, yp = en_pixels(pointe)
                xg, yg = en_pixels(gauche)
                xd, yd = en_pixels(droite)
                self.toile.create_polygon(xp, yp, xg, yg, xd, yd, fill=BANDE)

    def dessiner_les_carrefours(self):
        for nom in ville.CARREFOURS:
            x, y = en_pixels(ville.position(nom))
            if ville.CARREFOURS[nom]["principal"]:
                c = ville.LARGEUR_VOIE * ECHELLE * 2
                self.toile.create_rectangle(x - c, y - c, x + c, y + c,
                                            fill=CARREFOUR, outline="")
                self.toile.create_text(x + c + 8, y - c, text=nom,
                                       fill=TEXTE,
                                       font=("TkDefaultFont", 8, "bold"))
            else:
                c = 5
                self.toile.create_rectangle(x - c, y - c, x + c, y + c,
                                            fill=CROISEMENT, outline="")

    def dessiner_les_panneaux(self):
        for carrefour in ville.CARREFOURS:
            cx, cy = en_pixels(ville.position(carrefour))
            for voisin in ville.voisins(carrefour):
                panneau = ville.panneau(carrefour, voisin)
                if panneau is None:
                    continue

                tx, ty = en_pixels(ville.position(voisin))
                dx = tx - cx
                dy = ty - cy
                d = (dx * dx + dy * dy) ** 0.5
                if d < 1:
                    d = 1

                x = cx + dx / d * 21 - dy / d * 9
                y = cy + dy / d * 21 + dx / d * 9

                if panneau == "cedez":
                    self.toile.create_polygon(x - 5, y - 4, x + 5, y - 4,
                                              x, y + 5, fill=BLANC,
                                              outline=ROUGE_PANNEAU, width=1.6)
                else:
                    points = []
                    for i in range(8):
                        angle = math.radians(22.5 + 45 * i)
                        points.append(x + 5 * math.cos(angle))
                        points.append(y + 5 * math.sin(angle))
                    self.toile.create_polygon(points, fill=ROUGE_PANNEAU,
                                              outline=BLANC, width=1.2)

    def creer_les_feux(self):
        formes = {}
        for nom in self.simulation.feux:
            cx, cy = en_pixels(ville.position(nom))
            for voisin in ville.voisins(nom):
                tx, ty = en_pixels(ville.position(voisin))
                dx = tx - cx
                dy = ty - cy
                d = (dx * dx + dy * dy) ** 0.5
                if d < 1:
                    d = 1

                x = cx + dx / d * 21
                y = cy + dy / d * 21
                formes[(nom, voisin)] = self.toile.create_oval(
                    x - 4.6, y - 4.6, x + 4.6, y + 4.6,
                    fill=COULEURS_FEU[ROUGE], outline="#282828")
        return formes

    def rafraichir(self):
        for cle in self.formes_feux:
            carrefour, voisin = cle
            feu = self.simulation.feux[carrefour]
            etat = feu.couleur(ville.axe(carrefour, voisin))
            self.toile.itemconfigure(self.formes_feux[cle],
                                     fill=COULEURS_FEU[etat])

        self.rafraichir_les_vehicules()

        texte = (str(len(self.simulation.vehicules)) + " voitures   |   "
                 + "temps ecoule : " + str(int(self.simulation.temps)) + " s")
        self.toile.itemconfigure(self.etiquette_bas, text=texte)

        if self.appel_en_attente:
            nouveau = self.simulation.lancer_un_secours()
            if nouveau is not None:
                self.secours = nouveau
                self.appel_en_attente = False

        if self.secours is None:
            self.etiquette_secours.configure(text="")
        elif self.secours.sorti:
            self.etiquette_secours.configure(
                text="trajet termine en "
                     + str(round(self.secours.temps_de_trajet, 1)) + " s")
        else:
            self.etiquette_secours.configure(
                text="secours en route : "
                     + str(round(self.secours.temps_de_trajet, 1)) + " s")

    def rafraichir_les_vehicules(self):
        vehicules = self.simulation.vehicules

        while len(self.formes_vehicules) < len(vehicules):
            forme = self.toile.create_polygon(0, 0, 0, 0, 0, 0, 0, 0,
                                              fill=CIVIL)
            self.formes_vehicules.append(forme)

        for i in range(len(vehicules), len(self.formes_vehicules)):
            self.toile.itemconfigure(self.formes_vehicules[i], state="hidden")

        demi_longueur = LONGUEUR_VOITURE * ECHELLE / 2
        demi_largeur = LARGEUR_VOITURE * ECHELLE / 2

        for i in range(len(vehicules)):
            vehicule = vehicules[i]
            forme = self.formes_vehicules[i]

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
                couleur = SECOURS
            elif vehicule.vitesse < 0.3:
                couleur = CIVIL_ARRETE
            else:
                couleur = CIVIL

            self.toile.itemconfigure(forme, fill=couleur, state="normal")

    def battement(self):
        for i in range(self.facteur):
            self.simulation.avancer(PERIODE / 1000)
        self.rafraichir()
        self.racine.after(PERIODE, self.battement)

    def lancer(self):
        self.battement()
        self.racine.mainloop()
