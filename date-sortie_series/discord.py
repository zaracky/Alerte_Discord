"""Envoie un message dans le salon Discord défini, via webhook (urllib uniquement)."""
import json
import os
import urllib.request
import urllib.error


def send_discord_message(content):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("DISCORD_WEBHOOK_URL manquante : message non envoyé.")
        return False

    payload = json.dumps({"content": content}).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            # Sans en-tête User-Agent explicite, Cloudflare (qui protège Discord)
            # bloque souvent la requête par défaut de Python (erreur 1010).
            "User-Agent": "Mozilla/5.0 (compatible; series-weekly-alert/1.0)",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            response.read()
            return True
    except urllib.error.HTTPError as e:
        print(f"Erreur envoi Discord ({e.code}) : {e.read().decode('utf-8', errors='ignore')}")
        return False
    except urllib.error.URLError as e:
        print(f"Erreur envoi Discord : {e.reason}")
        return False
