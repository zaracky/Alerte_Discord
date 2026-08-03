# Veille d'offres d'emploi — Configuration

## 1. Installer les dépendances Python (une seule fois)

Ouvrez le Terminal et lancez :

```
pip3 install requests beautifulsoup4
```

## 2. Créer le webhook Discord

1. Dans l'app Discord, cliquez sur le **+** en bas à gauche → **Créer un serveur** → **Pour moi et mes amis**. Donnez-lui le nom que vous voulez (ex : "Alertes perso").
2. Dans ce serveur, faites un clic droit sur le salon `#général` (ou créez-en un dédié, ex : `#alertes-emploi`) → **Modifier le salon** → **Intégrations** → **Webhooks** → **Nouveau Webhook**.
3. Cliquez sur **Copier l'URL du Webhook**.
4. Ouvrez `veille_emploi.py`, repérez la ligne :
   ```python
   DISCORD_WEBHOOK_URL = "COLLEZ_VOTRE_URL_DE_WEBHOOK_ICI"
   ```
   et remplacez le texte entre guillemets par l'URL copiée.

## 3. Tester manuellement avant d'automatiser

Dans le Terminal, placez-vous dans le dossier puis lancez :

```
cd ~/Documents/veille-emploi
python3 veille_emploi.py
```

- Au premier lancement, c'est normal qu'**aucune alerte ne soit envoyée** : le script enregistre simplement l'état actuel comme référence (fichier `state.json` créé automatiquement).
- Relancez la commande une seconde fois : vous devriez voir `rien de nouveau` dans le terminal pour les deux sites, et toujours aucune alerte (puisque rien n'a changé).
- Si une erreur apparaît, c'est probablement que le site a légèrement changé sa structure HTML — dites-le moi, j'ajusterai le script.

## 4. Automatiser avec launchd (exécution quotidienne)

1. Déplacez le dossier `veille-emploi` (contenant le script, le `.plist`, et bientôt `state.json`) à l'endroit de votre choix, par exemple `~/Documents/veille-emploi`.
2. Ouvrez `com.veille.emploi.plist` avec un éditeur de texte et remplacez les **deux occurrences** de `/Users/VOTRE_NOM/veille-emploi/` par le vrai chemin complet vers votre dossier (vous pouvez l'obtenir en tapant `pwd` dans le Terminal une fois dans le dossier).
3. Copiez ce fichier au bon endroit et activez-le :

```
cp com.veille.emploi.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.veille.emploi.plist
```

C'est tout : le script se lancera automatiquement chaque jour à 9h00 (modifiable dans le `.plist`, valeurs `Hour`/`Minute`), même si le Mac était endormi à ce moment — il rattrapera au réveil.

### Commandes utiles

- **Vérifier que la tâche est bien chargée** : `launchctl list | grep veille`
- **Désactiver temporairement** : `launchctl unload ~/Library/LaunchAgents/com.veille.emploi.plist`
- **Réactiver** : `launchctl load ~/Library/LaunchAgents/com.veille.emploi.plist`
- **Forcer un test immédiat** (sans attendre 9h) : `launchctl start com.veille.emploi`
- **Consulter les logs** : fichiers `log.txt` et `log-erreur.txt` dans le dossier du script

## 5. Désactiver la surveillance d'un site plus tard

Ouvrez `veille_emploi.py`, et passez l'interrupteur correspondant à `False` :

```python
CHECK_OPENCLASSROOMS = True      # -> False pour désactiver
CHECK_AMAZON_TOULOUSE = True     # -> False pour désactiver
```

Aucune autre modification nécessaire.
