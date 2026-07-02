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

# Mode test : envoie un message Discord de test puis s'arrête (ne vérifie aucun site).
# Repassez à False une fois que vous avez confirmé que le message arrive bien.
TEST_DISCORD_WEBHOOK = False

# URL du webhook Discord à coller ici une fois créé (voir README.md)
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1518361141242368070/n7WkFLHzjk6wKAjbUuJJXO18A9oWla274uMd3BNkvz4RnAkjHFhl1e-SOShALOqS2u42"

# Fichier où l'état précédent est conservé (créé automatiquement au 1er lancement)
STATE_FILE = Path(__file__).parent / "state.json"

OPENCLASSROOMS_URL = "https://mentors.openclassrooms.com/jobs"
AMAZON_URL = "https://www.amazon.jobs/content/fr/teams/fulfillment-and-operations/france"

# Nom exact de la ville Amazon à surveiller (doit correspondre au début du nom
# affiché sur la page, ex: "Toulouse" pour "Toulouse (Haute-Garonne)").
# Ne capture pas les autres communes du département (ex: Villeneuve-lès-Bouloc).
AMAZON_CITY_NAME = "Toulouse"

# Le site se fait parfois bloquer les requêtes sans en-tête "navigateur" -> on s'identifie comme un navigateur classique
# Accept-Encoding limité à gzip/deflate : évite un bug connu de décompression zstd
# dans certaines versions de requests/urllib3 (ex: distributions Anaconda).
# OpenClassrooms /jobs retourne toujours un flux RSS (SPA côté client) -> on accepte XML explicitement.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Encoding": "gzip, deflate",
    "Accept": "application/rss+xml, application/xml, text/xml, */*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
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


def fetch_text(url: str) -> str:
    """
    Récupère le contenu HTML d'une page sous forme de texte.

    On gère ici nous-mêmes la décompression (zstd/gzip/deflate) plutôt que de
    laisser requests/urllib3 le faire automatiquement : certaines versions de
    ces bibliothèques contiennent un bug connu qui fait planter le décodage
    du format "zstd" utilisé par certains sites (dont Amazon).
    """
    resp = requests.get(url, headers=HEADERS, timeout=15, stream=True)
    resp.raise_for_status()

    raw = resp.raw.read(decode_content=False)
    encoding = resp.headers.get("Content-Encoding", "").lower()

    if "zstd" in encoding:
        import zstandard
        raw = zstandard.ZstdDecompressor().decompress(raw, max_output_size=50 * 1024 * 1024)
    elif "gzip" in encoding:
        import gzip
        raw = gzip.decompress(raw)
    elif "deflate" in encoding:
        import zlib
        raw = zlib.decompress(raw)

    return raw.decode("utf-8", errors="replace")


def parse_html(html: str) -> BeautifulSoup:
    """
    Transforme le HTML brut en objet exploitable, en retirant au passage les
    balises <script> et <style> : elles contiennent parfois du texte technique
    (JSON de données internes au site) qui peut fausser la détection si on le
    laisse dans le texte analysé.
    """
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return soup


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ============================================================
# VERIFICATION OPENCLASSROOMS
# ============================================================

def check_openclassrooms(state: dict) -> None:
    try:
        raw = fetch_text(OPENCLASSROOMS_URL)
    except Exception as e:
        print(f"[ERREUR] OpenClassrooms inaccessible : {e}")
        return

    # BeautifulSoup avec html.parser est tolérant aux caractères spéciaux mal
    # encodés qui font planter le parseur XML strict (xml.etree). On cherche
    # les balises <item> et leur contenu <title> directement dans le flux RSS.
    soup = BeautifulSoup(raw, "html.parser")
    items = soup.find_all("item")
    titles = sorted(item.find("title").get_text(strip=True) for item in items if item.find("title"))

    if titles:
        current_signature = hash_text("\n".join(titles))
        is_empty = False
        print(f"[DEBUG] OpenClassrooms : {len(titles)} offre(s) -> {titles}")
    else:
        current_signature = "EMPTY"
        is_empty = True

    previous_signature = state.get("openclassrooms")

    if previous_signature is None:
        print("[INFO] OpenClassrooms : première exécution, état enregistré (pas d'alerte).")
    elif current_signature != previous_signature:
        if is_empty:
            msg = "📋 **OpenClassrooms Mentors** : les offres ont disparu (flux vide)."
        else:
            listing = "\n".join(f"• {t}" for t in titles)
            msg = f"🎉 **OpenClassrooms Mentors** : changement détecté ({len(titles)} offre(s)) !\n{listing}\n{OPENCLASSROOMS_URL}"
        print(f"[ALERTE] {msg}")
        send_discord_alert(msg)
    else:
        print("[INFO] OpenClassrooms : rien de nouveau.")

    state["openclassrooms"] = current_signature


# ============================================================
# VERIFICATION AMAZON (zone Toulouse / Haute-Garonne)
# ============================================================

def get_city_blocks(soup: BeautifulSoup, city_name_prefix: str) -> dict:
    """
    Repère dans la page Amazon le bloc correspondant à une ville précise
    (ex: "Toulouse"). Ne retient que les villes dont le nom commence
    exactement par ce préfixe, pour éviter de capturer par erreur une autre
    commune du même département (ex: "Villeneuve-lès-Bouloc (Toulouse,
    Haute-Garonne)" contient aussi le mot "Toulouse" mais n'est pas la ville
    recherchée).
    """
    blocks = {}
    headers = soup.find_all(string=lambda s: isinstance(s, str) and "Haute-Garonne" in s)

    for header_text in headers:
        city_name = header_text.strip()
        if city_name.split(" (")[0].strip() != city_name_prefix:
            continue

        block_text = city_name
        # On remonte les parents successifs : tant que le texte du conteneur
        # reste court (un bloc "ville" est court), on le garde. Dès qu'il
        # devient long, c'est qu'on a remonté trop haut dans la page.
        for ancestor in header_text.parents:
            text = ancestor.get_text(separator=" ", strip=True)
            if len(text) <= 400:
                block_text = text
            else:
                break
        blocks[city_name] = block_text

    return blocks


def check_amazon(state: dict) -> None:
    try:
        html = fetch_text(AMAZON_URL)
    except Exception as e:
        print(f"[ERREUR] Amazon Jobs inaccessible : {e}")
        return

    soup = parse_html(html)
    blocks = get_city_blocks(soup, AMAZON_CITY_NAME)

    if not blocks:
        print(f"[ATTENTION] Aucune ville correspondant à '{AMAZON_CITY_NAME}' trouvée sur la page (structure du site modifiée ?).")
        return

    city_name, content = next(iter(blocks.items()))
    # On isole le contenu utile (offre ou "ne recrute pas") en retirant le nom
    # de la ville répété en tête du texte capturé.
    offer_text = content[len(city_name):].strip() if content.startswith(city_name) else content

    previous_content = state.get("amazon_toulouse")

    if previous_content is None:
        print("[INFO] Amazon Toulouse : première exécution, état enregistré (pas d'alerte).")
        print(f"[DEBUG] {city_name} -> {offer_text}")
    elif content != previous_content:
        msg = f"📦 **Amazon Jobs - {city_name}** : {offer_text}\n{AMAZON_URL}"
        print(f"[ALERTE] {msg}")
        send_discord_alert(msg)
    else:
        print("[INFO] Amazon Toulouse : rien de nouveau.")

    state["amazon_toulouse"] = content


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    print(f"=== Vérification du {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")

    if TEST_DISCORD_WEBHOOK:
        print("[TEST] Envoi d'un message de test sur Discord...")
        send_discord_alert("✅ Test réussi : le script de veille d'offres d'emploi est bien connecté à ce salon.")
        print("[TEST] Message envoyé (vérifiez votre salon Discord). N'oubliez pas de repasser TEST_DISCORD_WEBHOOK à False.")
        return

    state = load_state()

    if CHECK_OPENCLASSROOMS:
        check_openclassrooms(state)

    if CHECK_AMAZON_TOULOUSE:
        check_amazon(state)

    save_state(state)
    print("=== Terminé ===")


if __name__ == "__main__":
    main()
