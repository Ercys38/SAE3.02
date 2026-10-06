VERT = "vert"
ORANGE = "orange"
ROUGE = "rouge"

DUREE_VERT = 12.0
DUREE_ORANGE = 3.0


class Feu:

    def __init__(self, axe_passant="horizontal", decalage=0.0):
        self.axe_passant = axe_passant
        self.etat = VERT
        self.temps = decalage
        self.priorite = None

    def avancer(self, dt):
        if self.priorite is not None:
            self.axe_passant = self.priorite
            self.etat = VERT
            self.temps = 0.0
            return

        self.temps = self.temps + dt

        if self.etat == VERT and self.temps >= DUREE_VERT:
            self.etat = ORANGE
            self.temps = 0.0

        elif self.etat == ORANGE and self.temps >= DUREE_ORANGE:
            self.etat = VERT
            self.temps = 0.0
            if self.axe_passant == "horizontal":
                self.axe_passant = "vertical"
            else:
                self.axe_passant = "horizontal"

    def couleur(self, axe):
        if axe == self.axe_passant:
            return self.etat
        return ROUGE

    def passage_autorise(self, axe):
        return self.couleur(axe) == VERT
