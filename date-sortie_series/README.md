# Alerte hebdomadaire de séries — version GitHub Actions

Même logique que la version locale (Python, bibliothèque standard uniquement),
mais exécutée automatiquement dans le cloud via GitHub Actions, sans dépendre
de ton Mac allumé.

## Arborescence

```
.
├── .github/
│   └── workflows/
│       ├── weekly-digest.yml      (exécution auto le dimanche + déclenchement manuel)
│       └── check-ids.yml          (vérification des IDs, déclenchement manuel uniquement)
├── env_loader.py
├── tmdb.py
├── discord.py
├── weekly_digest.py
├── check_ids.py
├── series.json
├── .gitignore
├── .env.example
└── README.md
```

## Mise en place

1. **Crée un repository GitHub** (public ou privé, peu importe) et pousse tous ces fichiers dedans.

2. **Ajoute les deux secrets** nécessaires :
   - Va dans le repository → **Settings** → **Secrets and variables** → **Actions**.
   - Clique **"New repository secret"**, crée :
     - `TMDB_API_KEY` → ta clé API TMDB
     - `DISCORD_WEBHOOK_URL` → l'URL de ton webhook Discord

3. **Vérifie que les Actions sont bien activées** sur le repository (normalement activé par défaut) : onglet **Actions** en haut du repository.

4. **Teste manuellement avant d'attendre dimanche** :
   - Onglet **Actions** → sélectionne le workflow **"Digest hebdomadaire des séries"** → bouton **"Run workflow"** → confirme.
   - Regarde les logs de l'exécution pour vérifier que tout se déroule bien (le message généré est affiché dans les logs, comme en local).

## Fonctionnement automatique

Le digest se déclenche chaque **dimanche à 17h00 UTC** (~18h00 heure de Paris en
hiver, ~19h00 en été — GitHub ne gère pas le changement d'heure automatiquement).
Pas d'impact réel pour un digest hebdomadaire, mais bon à savoir.

## Ajouter une série

1. Cherche la série sur https://www.themoviedb.org, récupère l'ID dans l'URL (après `/tv/`).
2. Édite `series.json` **directement sur GitHub** (icône crayon sur le fichier) ou depuis ton Mac puis `git push`.
3. Lance manuellement le workflow **"Vérifier les IDs TMDB"** (onglet Actions → Run workflow) pour confirmer que l'ajout est correct.

## Tester en local (optionnel)

Toujours possible avec les mêmes commandes qu'avant, à condition de dupliquer
`.env.example` en `.env` et de le remplir :
```bash
python3 check_ids.py
python3 weekly_digest.py
```
