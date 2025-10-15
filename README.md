# ProofPal Desktop

ProofPal Desktop est une application Windows permettant de centraliser les reçus et preuves d'achat, suivre les échéances de retour et de garantie, et générer un dossier PDF pour le service après-vente.

## Installation

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Lancement en développement

```powershell
python app/main.py
```

## Build de l'exécutable Windows

```powershell
cd build
build.bat
```

L'exécutable est disponible sous `build\dist\ProofPal\ProofPal.exe`.
L'icône Windows est régénérée automatiquement à partir d'une représentation encodée afin d'éviter l'inclusion de fichiers binaires dans le dépôt.

## Données

- Base SQLite : `%LOCALAPPDATA%\ProofPal\proofpal.db`
- Pièces jointes : `%LOCALAPPDATA%\ProofPal\files\{item_id}`
- Exports PDF : `%USERPROFILE%\Documents\ProofPal\`

## Fonctionnalités

- Ajout et édition d'achats avec calcul automatique des dates de retour et de garantie
- Gestion des pièces jointes (images et PDF)
- Tableau filtrable et recherche en temps réel
- Tableau de bord avec indicateurs clés et journal d'activité
- Export "Dossier SAV" en PDF avec aperçu des pièces
- Notifications Windows pour les rappels de retour et de garantie
- Thème moderne basé sur Qt Fusion et feuille de style personnalisée

## Capture d'écran

*(Insérer ici vos captures d'écran lors des tests utilisateurs.)*

## Désinstallation

Supprimer le dossier `build\dist\ProofPal` ainsi que `%LOCALAPPDATA%\ProofPal` si vous souhaitez effacer les données locales.
