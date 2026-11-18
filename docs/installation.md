# Installation et lancement

## Préparer les machines virtuelles

Dans VirtualBox, menu Fichier puis Outils puis Gestionnaire de réseau hôte :
vérifier qu'un réseau `vboxnet0` existe en 192.168.56.1 avec son serveur
DHCP activé. Sans lui, la seconde carte des VM n'obtiendra pas d'adresse et
les deux machines ne se verront pas.

Pour chaque VM, dans Configuration puis Réseau :

| Adaptateur | Mode | À quoi il sert |
|---|---|---|
| 1 | NAT | accès à Internet, pour `apt` et `git clone` |
| 2 | Réseau privé hôte | liaison entre les deux VM |

Le NAT seul ne suffit pas : il isole les VM l'une de l'autre. Le réseau privé
hôte seul ne suffit pas non plus : il n'a pas d'accès à Internet.

Pendant l'installation de Debian, laisser le mot de passe root **vide**.
L'installateur met alors l'utilisateur créé dans le groupe sudo, ce qui évite
d'avoir à le faire après coup.

## Sur une machine neuve

Installer git et tkinter. Sous Debian ou Ubuntu :

```bash
sudo apt update
sudo apt install -y git python3-tk
```

Si `sudo` répond que l'utilisateur n'est pas dans le fichier sudoers, passer
par root une seule fois :

```bash
su -
apt update
apt install -y git python3-tk
usermod -aG sudo toto
exit
```

puis se déconnecter et se reconnecter.

Récupérer le projet :

```bash
git clone https://github.com/Ercys38/SAE3.02.git
cd SAE3.02
```

Vérifier que tout est en place :

```bash
python3 --version
python3 -c "import tkinter; print('tkinter disponible')"
```

Il faut Python 3.10 ou plus récent.

## Lancer sur une seule machine

```bash
cd ~/SAE3.02
python3 main.py local
```

La fenêtre s'ouvre avec le plan, les trois curseurs et les boutons d'appel.
Tout tourne dans le même programme, superviseur compris, et la base
`historique.db` se crée toute seule à la racine.

## Lancer sur deux machines

La VM1 tient le poste central, la VM2 fait tourner la simulation et la
fenêtre.

### Le réseau, sur les deux

Les deux adaptateurs sont déjà configurés, voir plus haut. Sur chaque VM,
relever l'adresse privée :

```bash
ip -4 addr show | grep 192.168.56
```

Les deux doivent répondre une adresse en 192.168.56.x. Si une carte reste
sans adresse :

```bash
nmcli device status
nmcli device connect enp0s8
```

Vérifier depuis la VM2 que la VM1 répond :

```bash
ping -c 3 <adresse de la VM1>
```

### VM1 — le superviseur

```bash
cd ~/SAE3.02
rm -f historique.db
python3 serveur.py
```

Elle affiche son port, puis un état chaque seconde : nombre de clients,
messages reçus, interventions enregistrées, carrefours sous priorité. Laisser
ce terminal ouvert et visible, c'est lui qui montre que les deux machines
travaillent ensemble.

### VM2 — la simulation

```bash
cd ~/SAE3.02
python3 main.py
```

Aucune adresse à saisir. La simulation diffuse une question en UDP sur le
réseau local, la VM1 répond, et la connexion se fait seule. La ligne
« superviseur trouvé » s'affiche et le compteur de clients de la VM1 passe
à 1.

Si personne ne répond au bout de trois secondes, la simulation démarre son
propre superviseur et continue en local. Dans ce cas, donner l'adresse de la
VM1 à la main :

```bash
python3 main.py 192.168.56.11
```

## Relire les résultats

Sur la machine du superviseur :

```bash
python3 -m outils.historique
```

Reproduire les mesures de gain, huit trajets par densité :

```bash
python3 -m outils.mesures
```

Vérifier que tout fonctionne, environ cinq minutes :

```bash
python3 -m unittest discover -s tests
```

## Problèmes courants

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

La simulation ne trouve pas le superviseur : vérifier que `serveur.py` tourne
toujours, que le `ping` passe entre les deux machines, et qu'aucun pare-feu
ne bloque le port 9009 en TCP ni le 9010 en UDP. En dernier recours, donner
l'adresse en argument.

`Address already in use` : une instance précédente du serveur tourne encore,
la fermer avec Ctrl+C.
