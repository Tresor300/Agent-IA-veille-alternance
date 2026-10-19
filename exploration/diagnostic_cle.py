import os, json
import requests
from dotenv import load_dotenv

load_dotenv()
URL = "https://api.apprentissage.beta.gouv.fr/api/job/v1/search"
CLES = {"Authorization": f"Bearer {os.environ['LBA_API_KEY']}"}

def lire(d, chemin):
    for cle in chemin.split("."):
        d = d.get(cle) if isinstance(d, dict) else None
    return d

jobs = requests.get(URL, params={"departements": "974"}, headers=CLES, timeout=30).json()["jobs"]
ft = [j for j in jobs if lire(j, "identifier.partner_label") == "France Travail"]

print("=== 1. Champs 'identifier' et 'apply' de 2 offres France Travail ===")
for j in ft[:2]:
    print(json.dumps({"identifier": j.get("identifier"), "apply": j.get("apply")}, ensure_ascii=False, indent=1))

print("\n=== 2. Nombre de valeurs uniques par champ candidat ===")
print("Offres reçues :", len(jobs))
for chemin in ["identifier.id", "identifier.partner_job_id", "apply.url", "offer.title"]:
    valeurs = [str(lire(j, chemin)) for j in jobs]
    print(f"{chemin:28} → {len(set(valeurs))} uniques | vides : {valeurs.count('None')}")

print("\n=== 3. France Travail ignore-t-il le niveau ? ===")
def ids(niveau):
    r = requests.get(URL, params={"departements": "974", "target_diploma_level": niveau}, headers=CLES, timeout=30)
    return {json.dumps(j.get("identifier"), sort_keys=True) for j in r.json()["jobs"]
            if lire(j, "identifier.partner_label") == "France Travail"}
n3, n7 = ids("3"), ids("7")
print(f"Niveau 3 : {len(n3)} | Niveau 7 : {len(n7)} | Communes aux deux : {len(n3 & n7)}")