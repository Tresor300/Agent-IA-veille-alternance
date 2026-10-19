import os
import requests
from dotenv import load_dotenv

load_dotenv()
URL = "https://api.apprentissage.beta.gouv.fr/api/job/v1/search"
CLES = {"Authorization": f"Bearer {os.environ['LBA_API_KEY']}"}
VILLES = {"Lille": (50.633, 3.058), "Roubaix": (50.690, 3.181), "Dunkerque": (51.034, 2.377),
          "Douai": (50.370, 3.080), "Valenciennes": (50.357, 3.523), "Cambrai": (50.176, 3.234),
          "Maubeuge": (50.278, 3.973)}

def ids_ft(params):
    jobs = requests.get(URL, params=params, headers=CLES, timeout=30).json().get("jobs", [])
    ft = [j for j in jobs if j["identifier"]["partner_label"] == "France Travail"]
    return len(ft), {j["identifier"]["id"] for j in ft}

brut, dep = ids_ft({"departements": "59"})
print(f"Département 59 entier : {len(dep)} offres France Travail uniques (brut {brut})")

union = set(dep)
for ville, (lat, lon) in VILLES.items():
    brut, ids = ids_ft({"latitude": lat, "longitude": lon, "radius": 15})
    print(f"{ville:13} : {len(ids):3} uniques (brut {brut}) | nouvelles : {len(ids - union)}")
    union |= ids
print(f"\nTotal France Travail après découpage : {len(union)} (contre {len(dep)})")