"""
Regarde, pour chaque série suivie, les épisodes qui sortent la semaine suivante
(du lundi au dimanche qui suit le jour d'exécution), et envoie un résumé groupé sur Discord.
En local : python3 weekly_digest.py
Sur GitHub : se lance automatiquement chaque dimanche (voir .github/workflows/weekly-digest.yml),
ou manuellement via l'onglet "Actions" → "Run workflow".
"""
import json
import os
import traceback
from datetime import date, timedelta

from env_loader import load_env
from tmdb import get_series_details, get_season_episodes
from discord import send_discord_message

SERIES_PATH = os.path.join(os.path.dirname(__file__), "series.json")

JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
        "août", "septembre", "octobre", "novembre", "décembre"]


def next_monday(from_date):
    """Lundi qui suit strictement la date donnée (si on est déjà lundi, saute à la semaine suivante)."""
    days_ahead = (7 - from_date.weekday()) % 7  # weekday(): lundi=0 ... dimanche=6
    if days_ahead == 0:
        days_ahead = 7
    return from_date + timedelta(days=days_ahead)


def format_long(d):
    return f"{d.day} {MOIS[d.month - 1]}"


def build_weekly_digest():
    with open(SERIES_PATH, "r", encoding="utf-8") as f:
        series_list = json.load(f)

    range_start = next_monday(date.today())
    range_end = range_start + timedelta(days=6)

    episodes_by_date = {}  # { date_iso: [ {series_name, season_number, episode_number}, ... ] }
    failed_series = []  # séries qu'on n'a pas réussi à interroger, malgré les tentatives

    for s in series_list:
        tmdb_id = s.get("tmdb_id")
        if not tmdb_id:
            continue

        try:
            details = get_series_details(tmdb_id)
            if not details["ok"]:
                failed_series.append(s["nom"])
                continue
            if not details["seasons"]:
                continue

            # Hypothèse simplificatrice : on ne regarde que la saison la plus récente,
            # ce qui couvre l'immense majorité des cas pour une série en cours de diffusion.
            last_season = details["seasons"][-1]
            episodes = get_season_episodes(tmdb_id, last_season["season_number"])

            for ep in episodes:
                air_date = ep.get("air_date")
                if not air_date:
                    continue
                ep_date = date.fromisoformat(air_date)
                if range_start <= ep_date <= range_end:
                    episodes_by_date.setdefault(air_date, []).append({
                        "series_name": s["nom"],
                        "season_number": ep["season_number"],
                        "episode_number": ep["episode_number"],
                    })
        except Exception as e:
            # Une série qui échoue (réseau, données inattendues...) ne doit pas
            # empêcher le digest de se construire pour toutes les autres.
            print(f"  ⚠️  Erreur sur la série '{s.get('nom')}' : {e}")
            failed_series.append(s["nom"])
            continue

    header = f"📅 **Planning du {format_long(range_start)} au {format_long(range_end)}**"

    sorted_dates = sorted(episodes_by_date.keys())
    if not sorted_dates:
        body = f"{header}\nRien de prévu cette semaine."
    else:
        blocks = [header]
        for date_iso in sorted_dates:
            d = date.fromisoformat(date_iso)
            jour_label = JOURS[d.weekday()].capitalize()
            blocks.append(f"\n**{jour_label} {format_long(d)}**")
            for ep in episodes_by_date[date_iso]:
                code = f"S{ep['season_number']:02d}E{ep['episode_number']:02d}"
                blocks.append(f"• {ep['series_name']} — {code}")
        body = "\n".join(blocks)

    if failed_series:
        body += f"\n\n⚠️ _Non vérifiées cette semaine (erreur technique) : {', '.join(failed_series)}_"

    return body


def main():
    load_env()
    try:
        message = build_weekly_digest()
        print("--- Message qui va être envoyé ---")
        print(message)
        print("-----------------------------------")
        success = send_discord_message(message)
        if success:
            print("Message envoyé sur Discord.")
        else:
            print("⚠️  L'envoi a échoué — voir l'erreur ci-dessus.")
    except Exception:
        # Filet de sécurité : si le script plante avant même de pouvoir construire
        # le message (erreur de fichier, bug inattendu...), on essaie quand même
        # de t'en informer sur Discord plutôt que de rester silencieux.
        error_details = traceback.format_exc()
        print(error_details)
        send_discord_message(
            "⚠️ Le script hebdomadaire de suivi de séries a rencontré une erreur "
            "et n'a pas pu générer le planning cette semaine. Vérifie les logs "
            "dans l'onglet Actions du repository."
        )


if __name__ == "__main__":
    main()
