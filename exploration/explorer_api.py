import os
from collections import Counter
import requests
from dotenv import load_dotenv

load_dotenv()
plan = requests.get("https://api.apprentissage.beta.gouv.fr/api/documentation/json", timeout=15).json()
BASE = plan.get("servers", [{"url": "https://api.apprentissage.beta.gouv.fr/api"}])[0]["url"]
ROMES = "M1801,M1802,M1803,M1804,M1805,M1806,M1810"   # métiers de l'informatique

r = requests.get(f"{BASE}/job/v1/search", params={"romes": ROMES},
                 headers={"Authorization": f"Bearer {os.environ['LBA_API_KEY']}"}, timeout=30)
print("Adresse :", r.url, "\nStatut :", r.status_code)
if not r.ok:
    print(r.text[:500])
    raise SystemExit

def lire(d, chemin):
    """Lit une valeur imbriquée, ex. lire(offre, 'workplace.name')."""
    for cle in chemin.split("."):
        d = d.get(cle) if isinstance(d, dict) else None
    return d

jobs = r.json().get("jobs", [])
print(f"\n{len(jobs)} offres reçues")
if jobs:
    print("Champs d'une offre :", list(jobs[0].keys()))
    print("Par source :", Counter(lire(j, "identifier.partner_label") for j in jobs))
    print("\n10 premières :")
    for j in jobs[:10]:
        print(" -", lire(j, "offer.title"), "|", lire(j, "workplace.name"), "|",
              lire(j, "workplace.location.address"), "|", lire(j, "offer.publication.creation"))
        
print("\n=== Test : la recherche nationale est-elle complète ? ===")
tests = {
    "France entière": {},
    "Loire-Atlantique (44)": {"departements": "44"},
    "Paris (75)": {"departements": "75"},
    "Nantes, rayon 100 km": {"latitude": 47.218, "longitude": -1.553, "radius": 100},
}
for nom, zone in tests.items():
    rep = requests.get(f"{BASE}/job/v1/search", params={"romes": ROMES, **zone},
                       headers={"Authorization": f"Bearer {os.environ['LBA_API_KEY']}"}, timeout=30)
    nb = len(rep.json().get("jobs", [])) if rep.ok else f"erreur {rep.status_code}"
    print(f"{nom:<25} → {nb} offres")
    print("\n=== Diagnostic des codes métier ===")
nantes = {"latitude": 47.218, "longitude": -1.553, "radius": 50}
cles = {"Authorization": f"Bearer {os.environ['LBA_API_KEY']}"}

# 1) Combien d'alternances autour de Nantes, tous métiers confondus ?
rep = requests.get(f"{BASE}/job/v1/search", params=nantes, headers=cles, timeout=30)
offres = rep.json().get("jobs", []) if rep.ok else []
print(f"Nantes 50 km, TOUS métiers : {len(offres)} offres")

# 2) Quels codes ROME portent les offres qui parlent d'informatique ?
mots = ("informati", "développ", "developp", "devops", "data", "réseau", "cyber", "système", "logiciel")
codes = Counter()
for j in offres:
    titre = (lire(j, "offer.title") or "").lower()
    if any(m in titre for m in mots):
        codes.update(lire(j, "offer.rome_codes") or ["(aucun code)"])
        print("  -", lire(j, "offer.title")[:70], "|", lire(j, "offer.rome_codes"))
print("\nCodes ROME des offres informatiques :", codes.most_common(10))