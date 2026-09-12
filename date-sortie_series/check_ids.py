"""
Vérifie que chaque tmdb_id du fichier series.json existe bien sur TMDB,
et que le nom renvoyé par TMDB ressemble à celui que tu as écrit.
En local : python3 check_ids.py
Sur GitHub : se lance via l'onglet "Actions" → workflow "check-ids" → "Run workflow".
"""
import json
import os
import re
import unicodedata
from datetime import datetime

from env_loader import load_env
from tmdb import get_series_details

SERIES_PATH = os.path.join(os.path.dirname(__file__), "series.json")
LOG_PATH = os.path.join(os.path.dirname(__file__), "check-ids.log")


def normalize(text):
    """Comparaison tolérante : ignore casse, accents et ponctuation."""
    if not text:
        return ""
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^a-z0-9]", "", text)
    return text


def main():
    load_env()

    with open(SERIES_PATH, "r", encoding="utf-8") as f:
        series_list = json.load(f)

    lines = [f"=== Vérification du {datetime.now().isoformat(timespec='seconds')} ==="]

    for s in series_list:
        nom = s.get("nom")
        tmdb_id = s.get("tmdb_id")

        if not tmdb_id:
            lines.append(f"❌ {nom} → aucun tmdb_id renseigné")
            continue

        result = get_series_details(tmdb_id)

        if not result["ok"]:
            lines.append(f"❌ {nom} ({tmdb_id}) → ID introuvable sur TMDB (code {result['status']})")
            continue

        if normalize(result["name"]) == normalize(nom):
            lines.append(f"✅ {nom} ({tmdb_id}) → confirmé : \"{result['name']}\"")
        else:
            lines.append(f"⚠️  {nom} ({tmdb_id}) → attention, TMDB renvoie \"{result['name']}\" — vérifie l'ID")

    output = "\n".join(lines) + "\n\n"

    # Sur GitHub Actions, le système de fichiers du job est jeté après exécution :
    # ce fichier de log n'est utile qu'en local. Le résultat s'affiche de toute
    # façon dans les logs de l'exécution, consultables depuis l'onglet Actions.
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(output)

    print(output)
    print(f"Résultat également enregistré dans : {LOG_PATH}")


if __name__ == "__main__":
    main()
