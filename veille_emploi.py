#!/usr/bin/env python3
"""
Veille d'offres d'emploi - OpenClassrooms Mentors + Amazon Jobs (zone Toulouse / Haute-Garonne)

Fonctionnement :
- Récupère le contenu des pages surveillées
- Compare avec ce qui a été vu lors de la dernière exécution (fichier state.json)
- Si un changement est détecté -> envoie une alerte Discord (webhook)
- Rien de nouveau -> ne fait rien (pas de notification, pas de bruit)

Configuration à adapter : section CONFIG ci-dessous.
"""

import json
import hashlib
import re
from pathlib import Path
from datetime import datetime

import requests
from bs4 import BeautifulSoup

# ============================================================
# CONFIG - à adapter avant la première utilisation
# ============================================================

# Interrupteurs : passez à False pour désactiver la surveillance d'un site
# (pratique si un site n'est plus utile, sans toucher au reste du code)
CHECK_OPENCLASSROOMS = True
CHECK_AMAZON_TOULOUSE = True

# URL du webhook Discord à coller ici une fois créé (voir README.md)
DISCORD_WEBHOOK_URL = "COLLEZ_VOTRE_URL_DE_WEBHOOK_ICI"

# Fichier où l'état précédent est conservé (créé automatiquement au 1er lancement)
STATE_FILE = Path(__file__).parent / "state.json"

OPENCLASSROOMS_URL = "https://mentors.openclassrooms.com/jobs"
AMAZON_URL = "https://www.amazon.jobs/content/fr/teams/fulfillment-and-operations/france"

# Le site se fait parfois bloquer les requêtes sans en-tête "navigateur" -> on s'identifie comme un navigateur classique
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

# ============================================================
# OUTILS
# ============================================================

def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def send_discord_alert(message: str) -> None:
    if "COLLEZ_VOTRE_URL" in DISCORD_WEBHOOK_URL:
        print("[ATTENTION] Le webhook Discord n'est pas configuré, alerte non envoyée.")
        return
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": message}, timeout=10)
    except Exception as e:
        print(f"[ERREUR] Envoi de l'alerte Discord impossible : {e}")


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ============================================================
# VERIFICATION OPENCLASSROOMS
# ============================================================

def check_openclassrooms(state: dict) -> None:
    try:
        resp = requests.get(OPENCLASSROOMS_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"[ERREUR] OpenClassrooms inaccessible : {e}")
        return

    soup = BeautifulSoup(resp.text, "html.parser")
    page_text = soup.get_text(separator="\n")

    is_empty = "Aucune offre pour le moment" in page_text

    if is_empty:
        current_signature = "EMPTY"
    else:
        # Une ou plusieurs offres sont présentes : on capture le bloc principal
        # pour détecter toute évolution (offre ajoutée, retirée, modifiée...)
        match = re.search(r"Missions disponibles(.*?)(?:Connexion employé|$)", page_text, re.S)
        block = match.group(1) if match else page_text
        current_signature = hash_text(block.strip())

    previous_signature = state.get("openclassrooms")

    if previous_signature is None:
        print("[INFO] OpenClassrooms : première exécution, état enregistré (pas d'alerte).")
    elif current_signature != previous_signature:
        if is_empty:
            msg = "📋 **OpenClassrooms Mentors** : les offres ont disparu (page redevenue vide)."
        else:
            msg = f"🎉 **OpenClassrooms Mentors** : changement détecté sur la page des missions !\n{OPENCLASSROOMS_URL}"
        print(f"[ALERTE] {msg}")
        send_discord_alert(msg)
    else:
        print("[INFO] OpenClassrooms : rien de nouveau.")

    state["openclassrooms"] = current_signature


# ============================================================
# VERIFICATION AMAZON (zone Toulouse / Haute-Garonne)
# ============================================================

def check_amazon(state: dict) -> None:
    try:
        resp = requests.get(AMAZON_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"[ERREUR] Amazon Jobs inaccessible : {e}")
        return

    soup = BeautifulSoup(resp.text, "html.parser")
    page_text = soup.get_text(separator="\n")

    lines = [l.strip() for l in page_text.split("\n") if l.strip()]

    # Chaque ville est annoncée par une ligne du type "Toulouse (Haute-Garonne)" ou
    # "Villeneuve-lès-Bouloc (Toulouse, Haute-Garonne)", suivie d'une ou plusieurs lignes
    # listant soit les offres, soit la mention "Nous ne recrutons pas actuellement."
    # On capture toutes les lignes jusqu'à la prochaine ville (ligne commençant une nouvelle zone).
    zone_lines = []
    capture = False
    for line in lines:
        is_city_header = "Haute-Garonne" in line and ("(" in line)
        if is_city_header:
            capture = "Toulouse" in line  # ne capture que les villes liées à Toulouse
            if capture:
                zone_lines.append(line)
            continue
        if capture:
            zone_lines.append(line)

    current_signature = hash_text("\n".join(zone_lines))
    previous_signature = state.get("amazon_toulouse")

    if previous_signature is None:
        print("[INFO] Amazon Toulouse : première exécution, état enregistré (pas d'alerte).")
        print(f"[DEBUG] Contenu capturé : {zone_lines}")
    elif current_signature != previous_signature:
        msg = f"📦 **Amazon Jobs** : changement détecté sur la zone Toulouse / Haute-Garonne !\n{AMAZON_URL}"
        print(f"[ALERTE] {msg}")
        send_discord_alert(msg)
    else:
        print("[INFO] Amazon Toulouse : rien de nouveau.")

    state["amazon_toulouse"] = current_signature


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    print(f"=== Vérification du {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")
    state = load_state()

    if CHECK_OPENCLASSROOMS:
        check_openclassrooms(state)

    if CHECK_AMAZON_TOULOUSE:
        check_amazon(state)

    save_state(state)
    print("=== Terminé ===")


if __name__ == "__main__":
    main()
