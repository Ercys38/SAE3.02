# Installation et lancement

Deux machines virtuelles Debian. La **VM1** tient le poste central, la **VM2**
fait tourner la simulation et la fenêtre. Les deux parties ci-dessous sont
indépendantes : chacune se suit du début à la fin sur sa machine.

## Préparer VirtualBox, avant de créer les VM

Menu Fichier, puis Outils, puis Gestionnaire de réseau hôte. Vérifier qu'un
réseau `vboxnet0` existe en 192.168.56.1 avec son serveur DHCP activé. Sans
lui, les VM n'obtiendront pas d'adresse sur le réseau privé et ne se verront
pas.

Pour chacune des deux VM, dans Configuration puis Réseau :

| Adaptateur | Mode | À quoi il sert |
|---|---|---|
| 1 | NAT | accès à Internet, pour `apt` et `git clone` |
| 2 | Réseau privé hôte | liaison entre la VM1 et la VM2 |

Le NAT seul ne suffit pas, il isole les VM l'une de l'autre. Le réseau privé
hôte seul ne suffit pas non plus, il n'a pas d'accès à Internet. Il faut les
deux.

Pendant l'installation de Debian, laisser le mot de passe root **vide** :
l'installateur met alors l'utilisateur créé dans le groupe sudo, et on évite
les problèmes de droits ensuite.

---

# VM1 — le superviseur

## 1. Installer les paquets

```bash
sudo systemctl stop packagekit
sudo apt update
sudo apt install -y git python3-tk
```

`systemctl stop packagekit` évite l'erreur « Impossible d'obtenir le verrou
/var/lib/apt/lists/lock », causée par le service de mise à jour de GNOME.

Si `sudo` répond que l'utilisateur n'est pas dans le fichier sudoers :

```bash
su -
systemctl stop packagekit
apt update
apt install -y git python3-tk
usermod -aG sudo toto
exit
```

puis se déconnecter et se reconnecter.

## 2. Récupérer le projet

```bash
cd ~
git clone https://github.com/Ercys38/SAE3.02.git
cd SAE3.02
```

## 3. Vérifier l'adresse réseau

```bash
ip -4 addr show | grep 192.168.56
```

La commande doit renvoyer une adresse en 192.168.56.x. **Noter cette
adresse**, la VM2 en aura besoin en cas de problème. Si rien ne s'affiche :

```bash
nmcli device status
nmcli device connect enp0s8
ip -4 addr show | grep 192.168.56
```

## 4. Lancer le superviseur

```bash
cd ~/SAE3.02
rm -f historique.db
python3 serveur.py
```

L'affichage attendu :

```
base : /home/toto/SAE3.02/historique.db
superviseur en ecoute sur le port 9009
annonce sur le reseau local, les clients le trouveront seuls
clients : 0 | messages recus : 0 | interventions en base : 0 | ...
```

Laisser ce terminal ouvert et visible pendant toute la démonstration : c'est
lui qui montre que les deux machines travaillent ensemble.

## 5. Relire les résultats, après la démonstration

Dans un second terminal de la VM1 :

```bash
cd ~/SAE3.02
python3 -m outils.historique
```

Chaque trajet s'affiche avec sa densité, son service, son parcours, le temps
avec le dispositif, le temps sans, et le gain.

---

# VM2 — la simulation

## 1. Installer les paquets

```bash
sudo systemctl stop packagekit
sudo apt update
sudo apt install -y git python3-tk
```

Même remarque que pour la VM1 si `sudo` refuse.

## 2. Récupérer le projet

```bash
cd ~
git clone https://github.com/Ercys38/SAE3.02.git
cd SAE3.02
```

## 3. Vérifier que tkinter est là

```bash
python3 --version
python3 -c "import tkinter; print('tkinter disponible')"
```

Il faut Python 3.10 ou plus récent. La VM2 est la seule qui ouvre une
fenêtre, c'est donc la seule où tkinter est indispensable.

## 4. Vérifier la liaison avec la VM1

```bash
ip -4 addr show | grep 192.168.56
ping -c 3 <adresse de la VM1>
```

Les deux adresses doivent être en 192.168.56.x et le ping doit passer. Si
ce n'est pas le cas, inutile d'aller plus loin : reprendre la configuration
des adaptateurs.

## 5. Lancer la simulation

Le superviseur doit déjà tourner sur la VM1.

```bash
cd ~/SAE3.02
python3 main.py
```

L'affichage attendu :

```
recherche du superviseur sur le reseau local...
superviseur trouve : 192.168.56.11 port 9009
```

Aucune adresse n'est saisie : la simulation diffuse une question en UDP sur
le réseau local et la VM1 répond. Le compteur `clients` de la VM1 passe à 1.

Si au bout de trois secondes elle affiche « aucun superviseur sur le reseau,
on reste en local », donner l'adresse de la VM1 à la main :

```bash
python3 main.py 192.168.56.11
```

## 6. Utiliser la fenêtre

Trois curseurs : densité de circulation de 0 à 100 %, vitesse de la
simulation de x1 à x5, vitesse autorisée de 30 à 90 km/h.

Trois boutons appellent un service. Le véhicule part de son bâtiment vers un
lieu d'intervention entouré en orange, et son chronomètre s'affiche à côté de
la légende.

La case « Priorité aux feux » coupe le dispositif : c'est la comparaison. Avec
la case cochée, les feux passent au vert devant le véhicule ; sans elle, il
attend au rouge comme tout le monde et le trajet dure deux à trois fois plus
longtemps.

---

# Lancer sur une seule machine

Si une seule VM est disponible, tout peut tourner dans un même programme,
superviseur compris :

```bash
cd ~/SAE3.02
python3 main.py local
```

# Problèmes courants

`no display name and no $DISPLAY` : le terminal n'est pas dans la session
graphique, ou la commande est lancée en root. En ouvrir un sur le bureau.

`ModuleNotFoundError: No module named 'tkinter'` : le paquet `python3-tk`
n'est pas installé.

`Impossible d'obtenir le verrou /var/lib/apt/lists/lock` : le service de mise
à jour de GNOME tient le verrou, `sudo systemctl stop packagekit` puis
reprendre.

`Erreur temporaire de résolution de deb.debian.org` : pas de DNS. Vérifier
`ip route` pour une route par défaut, et `cat /etc/resolv.conf` pour un
serveur de noms.

`Address already in use` au lancement du serveur : une instance précédente
tourne encore, la fermer avec Ctrl+C.

La VM2 ne trouve pas le superviseur : vérifier que `serveur.py` tourne
toujours sur la VM1, que le `ping` passe entre les deux machines, et qu'aucun
pare-feu ne bloque le port 9009 en TCP ni le 9010 en UDP. En dernier recours,
donner l'adresse en argument.
