import os, json
from collections import Counter
import requests
from dotenv import load_dotenv

load_dotenv()
URL = "https://api.apprentissage.beta.gouv.fr/api/job/v1/search"
CLES = {"Authorization": f"Bearer {os.environ['LBA_API_KEY']}"}

def chercher(params):
    return requests.get(URL, params=params, headers=CLES, timeout=30).json().get("jobs", [])

for nom, (lat, lon) in {"Paris centre": (48.866, 2.326), "Saint-Denis 974": (-20.908, 55.438)}.items():
    jobs = chercher({"latitude": lat, "longitude": lon, "radius": 3})
    print(f"\n=== {nom} : {len(jobs)} offres brutes ===")
    print("Par source :", dict(Counter(j["identifier"]["partner_label"] for j in jobs)))
    lieux = Counter(json.dumps(j["workplace"]["location"].get("geopoint") or j["workplace"]["location"].get("address"))
                    for j in jobs)
    print("Lieux les plus fréquents :")
    for lieu, n in lieux.most_common(3):
        print(f"  {n:3} offres → {lieu[:90]}")

print("\n=== Champs disponibles dans 'location' ===")
print(list(jobs[0]["workplace"]["location"].keys()))