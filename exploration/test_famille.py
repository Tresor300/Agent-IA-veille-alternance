import os
from collections import Counter
import requests
from dotenv import load_dotenv

load_dotenv()
URL = "https://api.apprentissage.beta.gouv.fr/api/job/v1/search"
CLES = {"Authorization": f"Bearer {os.environ['LBA_API_KEY']}"}
ROMES_INFO = ",".join(f"M18{n:02d}" for n in range(100)) + ",I1401"

for nom, (lat, lon) in {"Pile Paris": (48.859, 2.347), "Pile Saint-Denis 974": (-20.910, 55.445)}.items():
    r = requests.get(URL, headers=CLES, timeout=30,
                     params={"latitude": lat, "longitude": lon, "radius": 3, "romes": ROMES_INFO})
    print(f"\n=== {nom} : statut {r.status_code} ===")
    if not r.ok:
        print("Erreur :", r.text[:300])
        continue
    jobs = r.json().get("jobs", [])
    print(f"{len(jobs)} offres | par source :", dict(Counter(j["identifier"]["partner_label"] for j in jobs)))
    for j in jobs[:15]:
        print("  -", j["offer"]["title"][:65], "|", j["offer"].get("rome_codes"))