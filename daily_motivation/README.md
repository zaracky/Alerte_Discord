# daily-motivation

Envoi automatique d'un message d'encouragement sur Discord, 1 jour sur 2, du 4 août 2026 au 7 novembre 2027.

## Arborescence

```
daily-motivation/
├── messages.json              # les 115 messages, tirage sans remise
├── state.json                 # état du tirage (ne pas éditer à la main)
├── data/
│   └── final_message.txt      # message de clôture du 7 novembre 2027
├── send_message.py            # logique : date, tirage, envoi webhook
├── requirements.txt
├── .github/
│   └── workflows/
│       └── daily.yml          # déclenchement quotidien via GitHub Actions
└── README.md
```

## Mise en place (une seule fois)

1. **Créer le repo GitHub en privé**
   - New repository → nom `daily-motivation` → **Private** → créer.

2. **Récupérer un webhook Discord**
   - Dans le salon Discord cible : Paramètres du salon → Intégrations → Webhooks → Nouveau webhook → copier l'URL.

3. **Ajouter le secret dans GitHub**
   - Sur le repo : Settings → Secrets and variables → Actions → New repository secret
   - Nom : `DISCORD_WEBHOOK_URL`
   - Valeur : l'URL copiée à l'étape 2

4. **Pousser le code**
   ```bash
   cd daily-motivation
   git init
   git add .
   git commit -m "init: daily-motivation"
   git branch -M main
   git remote add origin git@github.com:<ton-user>/daily-motivation.git
   git push -u origin main
   ```

C'est tout. Le workflow se déclenche ensuite tout seul, tous les jours à 8h UTC.

## Tester que ça fonctionne

### Test 1 — en local, sans rien envoyer (dry-run)

```bash
pip install -r requirements.txt
python send_message.py --force --dry-run
```

Ça doit afficher un message choisi dans `messages.json`, sans toucher à Discord ni à `state.json`. Vérifie juste que ça tourne sans erreur.

### Test 2 — en local, envoi réel sur Discord

```bash
export DISCORD_WEBHOOK_URL="ton_url_ici"
python send_message.py --force
```

Vérifie que :
- Le message apparaît bien dans le salon Discord
- `state.json` a été mis à jour (`remaining_indices` a un élément de moins, `last_sent_date` renseigné)

Tu peux relancer plusieurs fois avec `--force` pour vérifier que les messages ne se répètent pas tant que le sac n'est pas vide.

### Test 3 — via GitHub Actions (le vrai circuit de production)

1. Sur le repo GitHub → onglet **Actions** → workflow **Daily motivation** → **Run workflow**
2. Coche `force` (et éventuellement `dry_run` pour un premier essai sans réel envoi)
3. Lance, regarde les logs de l'étape "Run script"
4. Si `dry_run` n'était pas coché : vérifie le message dans Discord
5. Vérifie qu'un commit automatique `chore: update state.json` apparaît dans l'historique du repo

Si ces 3 tests passent, le système est validé de bout en bout : cron → script → Discord → sauvegarde d'état.

## Premier envoi automatique réel

`START_DATE` est fixé au **4 août 2026** dans `send_message.py` —  Le premier déclenchement automatique aura lieu à 8h UTC (soit 10h heure de Paris en août, heure d'été).

## Le 7 novembre 2027

Le script bascule automatiquement sur le contenu de `data/final_message.txt` (personnalisable à part) pour l'envoi de clôture, puis s'arrête de lui-même les jours suivants — inutile de désactiver quoi que ce soit manuellement.
