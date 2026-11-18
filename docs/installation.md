# Installation et lancement

Deux machines virtuelles Debian. La **VM1** tient le poste central, la **VM2**
fait tourner la simulation et la fenêtre. Les deux parties ci-dessous sont
indépendantes : chacune se suit du début à la fin sur sa machine.

## Préparer VirtualBox, avant de créer les VM

Pour chacune des deux VM, dans Configuration puis Réseau :

| Adaptateur | Mode | Nom | À quoi il sert |
|---|---|---|---|
| 1 | Accès par pont | la carte de l'hôte | accès à Internet, pour `apt` et `git clone` |
| 2 | Réseau interne | `sae` | liaison entre la VM1 et la VM2 |

Pour l'adaptateur 1, choisir dans la liste la carte réseau réellement
utilisée par la machine hôte, filaire ou Wi-Fi. Pour l'adaptateur 2, taper le
nom `sae` à l'identique sur les deux VM, c'est lui qui les relie.

L'accès par pont donne Internet et, le plus souvent, une liaison directe
entre les deux VM. Mais sur un réseau d'école il arrive que les machines
soient isolées les unes des autres, et l'adresse change d'un jour à l'autre.
Le second adaptateur en réseau interne règle les deux problèmes : il ne
dépend d'aucun service extérieur, ni DHCP ni routeur, et ses adresses sont
fixées à la main une fois pour toutes, à l'étape 3 de chaque partie.

Une fois le projet cloné, Internet ne sert plus à rien : la démonstration
entière passe par le réseau interne.

**Ordre de création conseillé.** Créer la VM avec le seul adaptateur 1
activé, installer Debian, et n'ajouter l'adaptateur 2 qu'ensuite.
L'installateur ne configure que les cartes présentes au moment de
l'installation.

Pendant l'installation de Debian, laisser le mot de passe root **vide** :
l'installateur met alors l'utilisateur créé dans le groupe sudo, et on évite
les problèmes de droits ensuite.

## L'utilisateur et les droits

Vérifier d'abord où on en est :

```bash
id toto
```

Si `27(sudo)` apparaît dans la liste des groupes, `sudo` fonctionne et il n'y
a rien à faire. Sinon, avec le mot de passe root :

```bash
su -
usermod -aG sudo toto
exit
```

**Redémarrer ensuite la VM.** C'est le seul moyen fiable : le groupe n'est
pris en compte qu'à l'ouverture d'une nouvelle session, et un terminal déjà
ouvert continuera de répondre « toto n'est pas dans le fichier sudoers »,
même après `newgrp`. Tant que la VM n'a pas redémarré, lancer les commandes
d'administration en root plutôt qu'avec `sudo` :

```bash
su -
<les commandes>
exit
```

C'est la méthode indiquée entre parenthèses à chaque étape qui en a besoin.

## Si une carte reste « déconnectée »

Une carte ajoutée après l'installation de Debian n'a pas de profil : elle
reste « déconnectée » au démarrage, sans adresse ni route. Si c'est la carte
en pont, `apt` échoue avec « Erreur temporaire de résolution de
deb.debian.org ».

```bash
nmcli device status
sudo nmcli device connect enp0s3
nmcli connection show
sudo nmcli connection modify "Wired connection 2" connection.autoconnect yes
```

La première ligne montre quelle carte est déconnectée. La deuxième la monte
immédiatement et lui crée un profil. La troisième affiche le nom exact de ce
profil, souvent « Wired connection 2 ». La quatrième dit à ce profil de se
monter tout seul aux prochains démarrages, sans quoi il faudrait refaire
l'opération à chaque allumage.

Remplacer `enp0s3` et `Wired connection 2` par ce que montrent les deux
commandes d'affichage.

# VM1 — le superviseur

## 1. Installer les paquets

```bash
sudo systemctl stop packagekit
sudo apt update
sudo apt install -y git python3-tk
```

`systemctl stop packagekit` évite l'erreur « Impossible d'obtenir le verrou
/var/lib/apt/lists/lock », causée par le service de mise à jour de GNOME.

En root si `sudo` refuse :

```bash
su -
systemctl stop packagekit
apt update
apt install -y git python3-tk
exit
```

## 2. Récupérer le projet

```bash
cd ~
git clone https://github.com/Ercys38/SAE3.02.git
cd SAE3.02
```

## 3. Fixer l'adresse du réseau interne

Repérer le nom de la seconde carte, en général `enp0s8` :

```bash
nmcli device status
```

Elle apparaît souvent « déconnecté », c'est normal : une carte ajoutée après
l'installation de Debian n'a pas de profil. La commande suivante en crée un
et l'active, avec l'adresse **10.0.50.1** fixée une fois pour toutes :

```bash
sudo nmcli connection add type ethernet ifname enp0s8 con-name sae \
  ipv4.method manual ipv4.addresses 10.0.50.1/24 ipv4.never-default yes
sudo nmcli connection up sae
ip -4 addr show enp0s8
```

En root si `sudo` refuse :

```bash
su -
nmcli connection add type ethernet ifname enp0s8 con-name sae \
  ipv4.method manual ipv4.addresses 10.0.50.1/24 ipv4.never-default yes
nmcli connection up sae
ip -4 addr show enp0s8
exit
```

`ipv4.never-default yes` empêche cette carte de prendre la route par défaut,
qui doit rester sur la carte en pont. La configuration est enregistrée : elle revient
toute seule à chaque démarrage.

Si la carte en pont ne s'active pas et qu'`apt` ne résout plus les noms :

```bash
sudo nmcli device connect enp0s3
ip route
cat /etc/resolv.conf
```

Il doit y avoir une ligne `default via ...` et au moins un `nameserver`.

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

En root si `sudo` refuse :

```bash
su -
systemctl stop packagekit
apt update
apt install -y git python3-tk
exit
```

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

## 4. Fixer l'adresse et vérifier la liaison

Même opération que sur la VM1, avec l'adresse **10.0.50.2** :

```bash
nmcli device status
sudo nmcli connection add type ethernet ifname enp0s8 con-name sae \
  ipv4.method manual ipv4.addresses 10.0.50.2/24 ipv4.never-default yes
sudo nmcli connection up sae
ip -4 addr show enp0s8
```

En root si `sudo` refuse :

```bash
su -
nmcli connection add type ethernet ifname enp0s8 con-name sae \
  ipv4.method manual ipv4.addresses 10.0.50.2/24 ipv4.never-default yes
nmcli connection up sae
ip -4 addr show enp0s8
exit
```

Puis vérifier que la VM1 répond :

```bash
ping -c 3 10.0.50.1
```

Si le ping ne passe pas, inutile d'aller plus loin : vérifier que les deux
adaptateurs 2 sont bien en Réseau interne avec le même nom `sae`, et que les
deux adresses sont bien 10.0.50.1 et 10.0.50.2.

## 5. Lancer la simulation

Le superviseur doit déjà tourner sur la VM1.

```bash
cd ~/SAE3.02
python3 main.py
```

L'affichage attendu :

```
recherche du superviseur sur le reseau local...
superviseur trouve : 10.0.50.1 port 9009
```

Aucune adresse n'est saisie : la simulation diffuse une question en UDP sur
le réseau local et la VM1 répond. Le compteur `clients` de la VM1 passe à 1.

Si au bout de trois secondes elle affiche « aucun superviseur sur le reseau,
on reste en local », donner l'adresse de la VM1 à la main :

```bash
python3 main.py 10.0.50.1
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

`Erreur temporaire de résolution de deb.debian.org` : la carte en pont n'est
pas montée, donc ni route ni DNS. `nmcli device status` la montre
« déconnecté » ; `sudo nmcli device connect enp0s3` la relève, et `ip route`
doit ensuite afficher une ligne `default via`.

`toto n'est pas dans le fichier sudoers` alors que `id toto` montre bien
`27(sudo)` : la session date d'avant la modification. Redémarrer la VM, ou
lancer la commande en root avec `su -`.

`Address already in use` au lancement du serveur : une instance précédente
tourne encore, la fermer avec Ctrl+C.

La VM2 ne trouve pas le superviseur : vérifier que `serveur.py` tourne
toujours sur la VM1, que le `ping` passe entre les deux machines, et qu'aucun
pare-feu ne bloque le port 9009 en TCP ni le 9010 en UDP. En dernier recours,
donner l'adresse en argument.
