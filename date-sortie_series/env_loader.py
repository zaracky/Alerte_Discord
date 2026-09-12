"""
Lit un fichier .env tout simple (KEY=VALUE, une ligne par variable,
lignes commençant par # ignorées) et place les valeurs dans os.environ.
Sur GitHub Actions, ce fichier n'existe pas : les variables sont déjà
présentes via les "Secrets" injectés dans l'environnement d'exécution,
donc cette fonction ne fait alors simplement rien.
"""
import os


def load_env(path=".env"):
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())
