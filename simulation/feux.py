"""
Les feux tricolores d'un carrefour.

Principe : a un carrefour, les deux axes ne peuvent pas etre verts en meme
temps. On alterne donc entre l'axe horizontal et l'axe vertical.

Cycle d'un axe :  VERT (12 s) -> ORANGE (3 s) -> ROUGE (pendant que l'autre
axe passe) -> VERT ...
"""

VERT = "vert"
ORANGE = "orange"
ROUGE = "rouge"

DUREE_VERT = 12.0    # secondes
DUREE_ORANGE = 3.0   # secondes


class Feu:
    """Les feux d'un seul carrefour."""

    def __init__(self, axe_passant="horizontal", decalage=0.0):
        # L'axe qui a le droit de passer en ce moment.
        self.axe_passant = axe_passant
        # L'etat de cet axe : vert ou orange.
        self.etat = VERT
        # Temps ecoule depuis le dernier changement, en secondes.
        self.temps = decalage
        # Quand un secours demande la priorite, on note son axe ici.
        # (utilise a partir de l'etape 4 ; None = fonctionnement normal)
        self.priorite = None

    def avancer(self, dt):
        """Fait avancer le cycle de dt secondes."""
        # Priorite secours : le feu reste vert sur l'axe demande, on ne
        # deroule pas le cycle normal.
        if self.priorite is not None:
            self.axe_passant = self.priorite
            self.etat = VERT
            self.temps = 0.0
            return

        self.temps += dt

        if self.etat == VERT and self.temps >= DUREE_VERT:
            self.etat = ORANGE
            self.temps = 0.0

        elif self.etat == ORANGE and self.temps >= DUREE_ORANGE:
            self.etat = VERT
            self.temps = 0.0
            # On donne la main a l'autre axe.
            if self.axe_passant == "horizontal":
                self.axe_passant = "vertical"
            else:
                self.axe_passant = "horizontal"

    def couleur(self, axe):
        """Couleur vue par un vehicule qui arrive par cet axe."""
        if axe == self.axe_passant:
            return self.etat
        return ROUGE

    def passage_autorise(self, axe):
        """Un vehicule venant de cet axe a-t-il le droit de s'engager ?"""
        return self.couleur(axe) == VERT
