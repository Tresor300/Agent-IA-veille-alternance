import os
from collections import Counter
import requests
from dotenv import load_dotenv

load_dotenv()
URL = "https://api.apprentissage.beta.gouv.fr/api/job/v1/search"
CLES = {"Authorization": f"Bearer {os.environ['LBA_API_KEY']}"}

def lire(d, chemin):
    for cle in chemin.split("."):
        d = d.get(cle) if isinstance(d, dict) else None
    return d

def chercher(params):
    r = requests.get(URL, params=params, headers=CLES, timeout=30)
    return r.json().get("jobs", []) if r.ok else []

for dep in ["59", "62", "75", "974"]:
    sans = chercher({"departements": dep})
    union, encore_plafonne = {}, []
    for j in sans:
        union[lire(j, "identifier.id") or lire(j, "apply.url")] = j
    for niveau in ["3", "4", "5", "6", "7"]:
        jobs = chercher({"departements": dep, "target_diploma_level": niveau})
        for s, n in Counter(lire(j, "identifier.partner_label") for j in jobs).items():
            if n >= 150:
                encore_plafonne.append(f"niv{niveau}/{s}")
        for j in jobs:
            union[lire(j, "identifier.id") or lire(j, "apply.url")] = j
    print(f"{dep} : sans découpage {len(sans)} → avec découpage {len(union)} | encore plafonné : {encore_plafonne or 'non'}")