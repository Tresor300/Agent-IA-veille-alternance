import os, re, time
from collections import Counter
import requests
from dotenv import load_dotenv

load_dotenv()
URL = "https://api.apprentissage.beta.gouv.fr/api/job/v1/search"
CLES = {"Authorization": f"Bearer {os.environ['LBA_API_KEY']}"}
DEPARTEMENTS = [f"{n:02d}" for n in range(1, 96) if n != 20] + ["2A", "2B", "971", "972", "973", "974", "976"]
INFO = re.compile(
    r"\b(informatique|d[ée]veloppeu[rs]e?|devops|devsecops|data|cyber\w*|cloud|logiciel"
    r"|full.?stack|front.?end|back.?end|java|python|intelligence artificielle|machine learning"
    r"|syst[eè]mes? (et|&) r[ée]seaux?|r[ée]seaux? (et|&) t[ée]l[ée]com\w*|admin\w* (syst|r[ée]seau)\w*"
    r"|helpdesk|support (it|informatique)|technicien (it|informatique)|ing[ée]nieur (logiciel|syst[eè]me|cloud|data))\b",
    re.I)

def chercher(params):
    r = requests.get(URL, params=params, headers=CLES, timeout=30)
    time.sleep(0.2)
    return r.json().get("jobs", []) if r.ok else []

# 1. Codes métier réellement portés par les offres informatiques
codes, vus = Counter(), set()
for dep in DEPARTEMENTS:
    for j in chercher({"departements": dep}):
        if j["identifier"]["id"] not in vus and INFO.search(j["offer"]["title"] or ""):
            vus.add(j["identifier"]["id"])
            codes.update(j["offer"].get("rome_codes") or [])
    print(dep, end=" ", flush=True)
print(f"\n\n1. Codes métier des {len(vus)} offres informatiques :")
print(codes.most_common())

# 2. Test du filet de secours sur la pile de Saint-Denis (974)
liste = ",".join(c for c, _ in codes.most_common())
jobs = chercher({"latitude": -20.908, "longitude": 55.438, "radius": 3, "romes": liste})
print(f"\n2. Pile Saint-Denis avec ces codes : {len(jobs)} offres")
print("   Par source :", dict(Counter(j["identifier"]["partner_label"] for j in jobs)))
for j in jobs[:10]:
    print("   -", j["offer"]["title"][:70])