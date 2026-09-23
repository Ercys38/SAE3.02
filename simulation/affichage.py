"""
La fenetre : le plan, les feux, les panneaux et les voitures.

On utilise tkinter, qui fait partie de la bibliotheque standard de Python.
Il n'y a donc rien a installer : sur une machine neuve, un git clone et un
python3 main.py suffisent.

La fenetre ne calcule rien : elle lit l'etat de la Simulation et le
dessine. C'est important de garder cette separation (calcul d'un cote,
affichage de l'autre) : c'est ce qui permettra plus tard de faire tourner
le calcul dans un thread separe, ou sur une autre machine.
"""

import math
import tkinter as tk

from . import ville
from .feux import VERT, ORANGE, ROUGE
from .vehicule import LONGUEUR_VOITURE

# --- Reglages de l'affichage ---------------------------------------------
ECHELLE = 0.42            # pixels par metre
MARGE = 70                # pixels de bord
PERIODE = 33              # millisecondes entre deux images, soit 30 par seconde

FOND = "#eeeee8"
BITUME = "#787a80"
BITUME_PETIT = "#9a9ea4"
BANDE = "#f4f4f0"
CARREFOUR = "#606268"
CROISEMENT = "#9a9ea4"
TEXTE = "#46464b"
TEXTE_PETIT = "#7d7d82"

# Les civils sont bleus, plus sombres a l'arret : c'est la meme teinte,
# donc on lit tout de suite qu'il s'agit du meme type de vehicule.
# Le rouge est reserve aux vehicules de secours, et a rien d'autre.
CIVIL = "#3e609e"
CIVIL_ARRETE = "#263a66"
SECOURS = "#ce3732"

COULEURS_FEU = {VERT: "#2eae5c", ORANGE: "#e8a328", ROUGE: "#ce3f3c"}

ROUGE_PANNEAU = "#c8372f"
BLANC = "#fafafa"


def en_pixels(position_m):
    x, y = position_m
    return (x * ECHELLE + MARGE, y * ECHELLE + MARGE)


class Fenetre:
    def __init__(self, simulation):
        self.simulation = simulation

        largeur_m, hauteur_m = ville.taille_ville()
        self.largeur = int(largeur_m * ECHELLE) + 2 * MARGE
        self.hauteur = int(hauteur_m * ECHELLE) + 2 * MARGE

        self.racine = tk.Tk()
        self.racine.title("SAE R3.02 - Saint-Louis - le trafic civil")
        self.racine.resizable(False, False)

        self.toile = tk.Canvas(self.racine, width=self.largeur,
                               height=self.hauteur, background=FOND,
                               highlightthickness=0)
        self.toile.pack()

        self.construire_les_commandes()

        # Le decor ne bouge jamais : on le dessine une seule fois.
        self.dessiner_les_rues()
        self.dessiner_les_noms()
        self.dessiner_les_carrefours()
        self.dessiner_les_panneaux()

        # Ce qui bouge est cree une fois puis deplace, jamais redessine :
        # effacer et recreer cent formes trente fois par seconde ferait
        # ramer la fenetre.
        self.formes_feux = self.creer_les_feux()
        self.formes_vehicules = []
        self.etiquette_bas = self.toile.create_text(
            MARGE - 10, self.hauteur - 14, anchor="w", fill=TEXTE,
            font=("TkDefaultFont", 8), text="")

        self.toile.create_text(MARGE - 10, 24, anchor="w", fill=TEXTE,
                               font=("TkDefaultFont", 9),
                               text="Saint-Louis (68300) - plan simplifie")

    # --- construction ------------------------------------------------------
    def construire_les_commandes(self):
        barre = tk.Frame(self.racine)
        barre.pack(fill="x", padx=MARGE - 10, pady=(0, 8))

        tk.Label(barre, text="Densite de circulation").pack(side="left")
        self.curseur = tk.Scale(barre, from_=0, to=100, orient="horizontal",
                                length=360, showvalue=False,
                                command=self.changer_densite)
        self.curseur.set(self.simulation.densite)
        self.curseur.pack(side="left", padx=10)

        self.etiquette_densite = tk.Label(barre, text="", width=6, anchor="w")
        self.etiquette_densite.pack(side="left")
        self.changer_densite(self.simulation.densite)

    def changer_densite(self, valeur):
        self.simulation.densite = int(valeur)
        self.etiquette_densite.configure(text="%d %%" % int(valeur))

    # --- le decor ----------------------------------------------------------
    def dessiner_les_rues(self):
        # Les petites rues d'abord, les grandes voies par-dessus : les
        # jonctions sont ainsi masquees par l'avenue, comme dans la realite.
        for categorie, couleur in (("rue", BITUME_PETIT), ("avenue", BITUME)):
            epaisseur = ville.LARGEUR_VOIE * ECHELLE * (4 if categorie == "avenue" else 2)
            for depart, arrivee, _nom, cat in ville.RUES:
                if cat != categorie:
                    continue
                x1, y1 = en_pixels(ville.position(depart))
                x2, y2 = en_pixels(ville.position(arrivee))
                self.toile.create_line(x1, y1, x2, y2, fill=couleur,
                                       width=epaisseur, capstyle="round")

        # le marquage au sol
        for depart, arrivee, _nom, cat in ville.RUES:
            x1, y1 = en_pixels(ville.position(depart))
            x2, y2 = en_pixels(ville.position(arrivee))
            self.toile.create_line(x1, y1, x2, y2, fill=BANDE, width=1.4)
            if cat != "avenue":
                continue
            dx, dy = x2 - x1, y2 - y1
            d = max((dx * dx + dy * dy) ** 0.5, 1)
            nx, ny = -dy / d, dx / d
            for cote in (-1, 1):
                e = ville.LARGEUR_VOIE * ECHELLE * cote
                self.toile.create_line(x1 + nx * e, y1 + ny * e,
                                       x2 + nx * e, y2 + ny * e,
                                       fill=BANDE, width=1.1, dash=(5, 6))

    def dessiner_les_noms(self):
        """Le nom de chaque rue, ecrit une seule fois."""
        deja_ecrits = set()
        for depart, arrivee, nom, cat in ville.RUES:
            if nom in deja_ecrits:
                continue
            deja_ecrits.add(nom)

            x1, y1 = en_pixels(ville.position(depart))
            x2, y2 = en_pixels(ville.position(arrivee))
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2

            if cat == "avenue":
                couleur, taille, ecart = TEXTE, 7, 17
            else:
                couleur, taille, ecart = TEXTE_PETIT, 6, 12

            horizontal = ville.axe(depart, arrivee) == "horizontal"
            self.toile.create_text(
                mx if horizontal else mx - ecart,
                my - ecart if horizontal else my,
                text=nom, fill=couleur, font=("TkDefaultFont", taille),
                angle=0 if horizontal else 90)

    def dessiner_les_carrefours(self):
        for nom, infos in ville.CARREFOURS.items():
            x, y = en_pixels(infos["pos"])
            if infos["principal"]:
                c = 10
                self.toile.create_rectangle(x - c, y - c, x + c, y + c,
                                            fill=CARREFOUR, outline="")
                self.toile.create_text(x + 15, y - 9, text=nom, fill=TEXTE,
                                       font=("TkDefaultFont", 8, "bold"))
            else:
                c = 5
                self.toile.create_rectangle(x - c, y - c, x + c, y + c,
                                            fill=CROISEMENT, outline="")

    def dessiner_les_panneaux(self):
        """Un cedez-le-passage ou un stop sur chaque branche concernee."""
        for carrefour in ville.CARREFOURS:
            cx, cy = en_pixels(ville.position(carrefour))
            for voisin in ville.voisins(carrefour):
                panneau = ville.panneau(carrefour, voisin)
                if panneau is None:
                    continue

                tx, ty = en_pixels(ville.position(voisin))
                dx, dy = tx - cx, ty - cy
                d = max((dx * dx + dy * dy) ** 0.5, 1)
                # on decale le panneau sur le bord droit de la chaussee
                x = cx + dx / d * 21 - dy / d * 9
                y = cy + dy / d * 21 + dx / d * 9

                if panneau == "cedez":
                    self.toile.create_polygon(x - 5, y - 4, x + 5, y - 4, x, y + 5,
                                              fill=BLANC, outline=ROUGE_PANNEAU, width=1.6)
                else:
                    points = []
                    for i in range(8):
                        a = math.radians(22.5 + 45 * i)
                        points += [x + 5 * math.cos(a), y + 5 * math.sin(a)]
                    self.toile.create_polygon(points, fill=ROUGE_PANNEAU,
                                              outline=BLANC, width=1.2)

    def creer_les_feux(self):
        """Un point par branche de carrefour equipe ; on ne changera que la couleur."""
        formes = {}
        for nom in self.simulation.feux:
            cx, cy = en_pixels(ville.position(nom))
            for voisin in ville.voisins(nom):
                tx, ty = en_pixels(ville.position(voisin))
                dx, dy = tx - cx, ty - cy
                d = max((dx * dx + dy * dy) ** 0.5, 1)
                x = cx + dx / d * 21
                y = cy + dy / d * 21
                formes[(nom, voisin)] = self.toile.create_oval(
                    x - 4.6, y - 4.6, x + 4.6, y + 4.6,
                    fill=COULEURS_FEU[ROUGE], outline="#282828")
        return formes

    # --- rafraichissement --------------------------------------------------
    def rafraichir(self):
        for (carrefour, voisin), forme in self.formes_feux.items():
            feu = self.simulation.feux[carrefour]
            couleur = COULEURS_FEU[feu.couleur(ville.axe(carrefour, voisin))]
            self.toile.itemconfigure(forme, fill=couleur)

        self.rafraichir_les_vehicules()

        self.toile.itemconfigure(
            self.etiquette_bas,
            text="%d voitures civiles   |   avenues a 2x2 voies   |   temps ecoule : %d s"
                 % (len(self.simulation.vehicules), self.simulation.temps))

    def rafraichir_les_vehicules(self):
        vehicules = self.simulation.vehicules

        # on cree les formes qui manquent, on cache celles qui sont en trop
        while len(self.formes_vehicules) < len(vehicules):
            self.formes_vehicules.append(
                self.toile.create_polygon(0, 0, 0, 0, 0, 0, 0, 0, fill=CIVIL))
        for forme in self.formes_vehicules[len(vehicules):]:
            self.toile.itemconfigure(forme, state="hidden")

        demi_l = LONGUEUR_VOITURE * ECHELLE / 2
        demi_e = 1.3

        for vehicule, forme in zip(vehicules, self.formes_vehicules):
            # position() place deja le vehicule au milieu de sa file
            x, y = en_pixels(vehicule.position())
            dx, dy = vehicule.direction()
            px, py = -dy, dx

            self.toile.coords(
                forme,
                x + dx * demi_l + px * demi_e, y + dy * demi_l + py * demi_e,
                x + dx * demi_l - px * demi_e, y + dy * demi_l - py * demi_e,
                x - dx * demi_l - px * demi_e, y - dy * demi_l - py * demi_e,
                x - dx * demi_l + px * demi_e, y - dy * demi_l + py * demi_e)

            if vehicule.prioritaire:
                couleur = SECOURS
            elif vehicule.vitesse < 0.3:
                couleur = CIVIL_ARRETE
            else:
                couleur = CIVIL
            self.toile.itemconfigure(forme, fill=couleur, state="normal")

    # --- horloge -----------------------------------------------------------
    def battement(self):
        self.simulation.avancer(PERIODE / 1000)
        self.rafraichir()
        self.racine.after(PERIODE, self.battement)

    def lancer(self):
        self.battement()
        self.racine.mainloop()
