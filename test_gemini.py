import os, json
import requests
from dotenv import load_dotenv

load_dotenv()
CLE = {"x-goog-api-key": os.environ["GEMINI_API_KEY"]}
BASE = "https://generativelanguage.googleapis.com/v1beta"

# 1. Quels modèles « flash » sont disponibles pour cette clé ?
r = requests.get(f"{BASE}/models", headers=CLE, params={"pageSize": 200}, timeout=30)
print("Connexion :", r.status_code)
r.raise_for_status()
EXCLUS = ("preview", "exp", "tts", "image", "live", "audio", "embedding", "thinking")
flash = [m["name"] for m in r.json().get("models", [])
         if "flash" in m["name"] and "generateContent" in m.get("supportedGenerationMethods", [])
         and not any(x in m["name"] for x in EXCLUS)]
print("Modèles flash stables :", flash)
MODELE = "models/gemini-flash-latest" if "models/gemini-flash-latest" in flash else flash[-1]
print("Modèle choisi :", MODELE)

# 2. Test de jugement sur des titres piégeux
TITRES = [
    "Monteur Réseaux Electriques en contrat d'alternance H/F",
    "Administrateur(trice) réseau et systèmes junior - Alternance (H/F)",
    "Technicien réseau datacenter CDI (H/F)",
    "Alternance - Chargé de Développement RH H/F",
    "Alternance Développement Cloud / IA / DevOps (H/F)",
    "Alternance - Chargé de Projet Digital H/F",
]
consigne = (
    "Tu tries des offres d'emploi pour un étudiant ingénieur qui cherche une ALTERNANCE "
    "(apprentissage ou contrat de professionnalisation) dans l'INFORMATIQUE au sens large : "
    "développement, DevOps, cloud, data, cybersécurité, systèmes et réseaux informatiques, support IT, "
    "gestion de projet informatique. Pour chaque titre, réponds :\n"
    "- \"oui\" : alternance clairement dans l'informatique ;\n"
    "- \"non\" : autre métier (BTP, électricité, RH, vente…) OU contrat qui n'est pas une alternance (CDI, CDD, stage, intérim) ;\n"
    "- \"doute\" : impossible de trancher avec le seul titre.\n"
    "Réponds uniquement en JSON : une liste d'objets {\"i\": numéro, \"verdict\": \"oui|non|doute\", \"raison\": \"courte\"}.\n\n"
    + "\n".join(f"{i}. {t}" for i, t in enumerate(TITRES))
)
import time

def appeler(consigne):
    for modele in ["models/gemini-flash-latest", "models/gemini-flash-lite-latest"]:
        for attente in (0, 10, 30):
            time.sleep(attente)
            r = requests.post(f"{BASE}/{modele}:generateContent", headers=CLE, timeout=60, json={
                "contents": [{"parts": [{"text": consigne}]}],
                "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
            })
            print(f"Appel {modele} : {r.status_code}")
            if r.ok:
                return r
            if r.status_code not in (429, 500, 503):   # erreur non temporaire : inutile d'insister
                print(r.text[:300])
                break
    raise SystemExit("Gemini indisponible : les offres seraient rejugées au prochain passage.")

r = appeler(consigne)
for v in json.loads(r.json()["candidates"][0]["content"]["parts"][0]["text"]):
    print(f"{v['verdict']:6} | {TITRES[v['i']][:60]:60} | {v['raison']}")