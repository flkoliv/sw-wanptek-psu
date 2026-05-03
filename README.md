# Wanptek PSU Controller

Application desktop pour piloter une alimentation Wanptek via USB / port serie.
Compatible Windows, macOS et Linux.

Le programme permet de :

- visualiser la tension, le courant et la puissance
- modifier les consignes de tension et de courant
- activer ou desactiver la sortie
- activer ou desactiver l'OCP
- afficher l'historique des mesures dans une fenetre de graphe

## Captures et comportement

L'application repose sur une interface `customtkinter` avec :

- un affichage principal type LCD
- deux molettes de reglage
- une barre de boutons pour le menu, le graphe, le verrouillage, l'OCP et la sortie

## Prerequis communs

- Python 3.10 ou superieur avec `tkinter` disponible
- Une alimentation Wanptek compatible
- Un adaptateur USB / serie reconnu par le systeme

---

## Installation — Windows

### 1. Installer Python

Installer Python 3.10 depuis l'installateur officiel Windows.

Point important :

- verifier que `tcl/tk and IDLE` est bien installe

### 2. Cloner ou copier le projet

```text
C:\projets\Wanptek
```

### 3. Creer l'environnement virtuel

Dans PowerShell, depuis le dossier du projet :

```powershell
py -3.10 -m venv .venv
```

### 4. Activer l'environnement virtuel

Si PowerShell bloque les scripts :

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Puis activer l'environnement :

```powershell
.\.venv\Scripts\Activate.ps1
```

### 5. Installer les dependances

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---

## Installation — macOS

### 1. Installer Python

```bash
brew install python@3.10
```

Verifier que `tkinter` est present :

```bash
python3.10 -c "import tkinter"
```

Si absent, installer :

```bash
brew install python-tk@3.10
```

### 2. Cloner ou copier le projet

```bash
git clone <url-du-depot> ~/projets/Wanptek
cd ~/projets/Wanptek
```

### 3. Creer et activer l'environnement virtuel

```bash
python3.10 -m venv .venv
source .venv/bin/activate
```

### 4. Installer les dependances

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Installation — Linux

### 1. Installer Python et tkinter

Sur Debian / Ubuntu :

```bash
sudo apt update
sudo apt install python3.10 python3.10-venv python3-tk
```

Sur Fedora :

```bash
sudo dnf install python3.10 python3-tkinter
```

### 2. Autoriser l'acces au port serie

Ajouter votre utilisateur au groupe `dialout` :

```bash
sudo usermod -aG dialout $USER
```

Se deconnecter puis se reconnecter pour que le changement soit pris en compte.

### 3. Cloner ou copier le projet

```bash
git clone <url-du-depot> ~/projets/Wanptek
cd ~/projets/Wanptek
```

### 4. Creer et activer l'environnement virtuel

```bash
python3.10 -m venv .venv
source .venv/bin/activate
```

### 5. Installer les dependances

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Lancement

### Depuis le terminal (toutes plateformes)

```bash
python main.py
```

### Via le lanceur graphique

**Windows** (sans console) :

```powershell
pythonw run.pyw
```

**macOS / Linux** :

```bash
python run.pyw
```

`run.pyw` detecte automatiquement le systeme et utilise le Python du dossier `.venv`.
Si l'environnement virtuel n'existe pas, un message d'erreur s'affiche.

---

## Premiere configuration

Au premier lancement :

1. cliquer sur `Menu`
2. choisir le port serie correspondant a l'alimentation
   - Windows : `COM3`, `COM4`, ...
   - Linux : `/dev/ttyUSB0`, `/dev/ttyACM0`, ...
   - macOS : `/dev/cu.usbserial-XXXX`, `/dev/cu.SLAB_USBtoUART`, ...
3. choisir l'adresse Modbus de l'appareil
4. choisir la vitesse serie
5. cliquer sur `Save`

Le programme tentera ensuite de se connecter automatiquement.

Les parametres sont sauvegardes dans un fichier local `param`.

---

## Utilisation

### Affichage principal

L'ecran principal affiche :

- la tension
- le courant
- la puissance
- l'etat OCP
- l'etat de sortie

### Boutons

- `Menu` : ouvre la fenetre de configuration serie
- `Graph` : ouvre la fenetre d'historique des mesures
- `Lock` : active ou desactive le pilotage logiciel des consignes
- `OCP` : active ou desactive la protection sur courant
- `OUT` : active ou coupe la sortie de l'alimentation

### Reglage tension / courant

Quand le mode `Lock` est actif :

- les molettes deviennent modifiables
- les nouvelles valeurs sont envoyees a l'alimentation

Quand `Lock` est inactif :

- les molettes affichent simplement les consignes courantes

### Graphe

La fenetre `Graph` affiche l'historique recent de :

- la tension
- le courant
- la puissance

Le programme conserve environ 10 minutes de mesures.

---

## Architecture du projet

- `main.py` : point d'entree principal
- `run.pyw` : lanceur sans console (Windows) / lanceur graphique (macOS, Linux)
- `PSUModel.py` : etat de l'application et configuration sauvegardee
- `PSUController.py` : communication Modbus et logique de controle
- `PSUView.py` : interface graphique

---

## Depannage

### `ModuleNotFoundError: No module named 'tkinter'`

La distribution Python installee ne contient pas Tk.

- **Windows** : reinstaller Python 3.10 avec `tcl/tk and IDLE`
- **macOS** : `brew install python-tk@3.10`
- **Linux** : `sudo apt install python3-tk` (ou equivalent)

### PowerShell refuse `Activate.ps1` (Windows)

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Permission refusee sur le port serie (Linux)

```bash
sudo usermod -aG dialout $USER
```

Se deconnecter puis se reconnecter.

### L'application ne se connecte pas

Verifier :

- que le bon port serie est selectionne
- que l'adresse Modbus est correcte
- que l'alimentation est allumee
- que le cable USB / serie fonctionne
- que le pilote serie est bien installe

### Le graphe ne s'ouvre pas

Le graphe ne s'ouvre que si au moins une mesure a deja ete recue.

---

## Notes

- Le projet a ete valide avec Python 3.10.
- Compatible Windows, macOS et Linux.
- Le fichier `requirements.txt` contient les dependances Python du projet.

## Licence

Voir le fichier `LICENSE`.
