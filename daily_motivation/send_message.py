#!/usr/bin/env python3
"""
Envoie un message d'encouragement quotidien (1 jour sur 2) sur un webhook Discord.

Logique :
- Le workflow GitHub Actions se déclenche TOUS les jours à 8h UTC.
- Ce script décide lui-même si "aujourd'hui" est un jour d'envoi (parité par
  rapport à START_DATE), pour éviter la complexité d'un cron "tous les 2 jours".
- Tirage sans remise dans messages.json : jamais de répétition avant d'avoir
  épuisé tout le pool (donc au moins 115 jours d'écart garanti avec 115 messages).
- Au jour END_DATE, envoie un message de clôture unique puis s'arrête.
"""

import json
import os
import random
import sys
from datetime import date, datetime, timezone

START_DATE = date(2026, 8, 4)   # premier envoi
END_DATE = date(2027, 11, 7)    # dernier envoi (message de clôture)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MESSAGES_FILE = os.path.join(BASE_DIR, "messages.json")
STATE_FILE = os.path.join(BASE_DIR, "state.json")
FINAL_MESSAGE_FILE = os.path.join(BASE_DIR, "data", "final_message.txt")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def send_to_discord(webhook_url, content, dry_run=False):
    if dry_run:
        print(f"[DRY RUN] Message qui aurait été envoyé :\n{content}")
        return
    import requests
    response = requests.post(webhook_url, json={"content": content}, timeout=15)
    response.raise_for_status()
    print(f"Message envoyé (status {response.status_code}).")


def pick_next_message(messages, state):
    """Tirage sans remise. Reshuffle le sac une fois vide (nouveau cycle)."""
    if not state["remaining_indices"]:
        indices = list(range(len(messages)))
        random.shuffle(indices)
        state["remaining_indices"] = indices
        state["cycle_number"] += 1
        print(f"Sac vide : nouveau cycle #{state['cycle_number']} démarré.")

    index = state["remaining_indices"].pop(0)
    return messages[index]


def main():
    force = "--force" in sys.argv
    dry_run = "--dry-run" in sys.argv

    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url and not dry_run:
        print("ERREUR : la variable d'environnement DISCORD_WEBHOOK_URL est manquante.")
        sys.exit(1)

    today = datetime.now(timezone.utc).date()
    print(f"Date du jour (UTC) : {today}")

    state = load_json(STATE_FILE)

    # Projet terminé, plus rien à envoyer
    if today > END_DATE:
        print("Le projet est terminé (après END_DATE). Rien à envoyer.")
        return

    # Jour de clôture : message spécial, une seule fois
    if today == END_DATE:
        if state.get("final_message_sent"):
            print("Le message de clôture a déjà été envoyé. Rien à faire.")
            return
        with open(FINAL_MESSAGE_FILE, "r", encoding="utf-8") as f:
            final_message = f.read().strip()
        send_to_discord(webhook_url, final_message, dry_run=dry_run)
        state["final_message_sent"] = True
        state["last_sent_date"] = today.isoformat()
        if not dry_run:
            save_json(STATE_FILE, state)
        return

    # Avant le début du projet : rien à faire (sauf --force, pour pouvoir tester en amont)
    if today < START_DATE and not force:
        print(f"Le projet démarre le {START_DATE}. Rien à envoyer aujourd'hui.")
        return

    # Vérifie la parité (1 jour sur 2), sauf si --force (utile pour tester)
    days_since_start = (today - START_DATE).days
    if days_since_start % 2 != 0 and not force:
        print("Aujourd'hui n'est pas un jour d'envoi (rythme 1 jour sur 2). Rien à faire.")
        return

    messages = load_json(MESSAGES_FILE)
    message = pick_next_message(messages, state)

    send_to_discord(webhook_url, message, dry_run=dry_run)

    state["last_sent_date"] = today.isoformat()
    if not dry_run:
        save_json(STATE_FILE, state)


if __name__ == "__main__":
    main()
