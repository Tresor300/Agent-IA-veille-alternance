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
    r"|full.?stack|front.?end|back.?end|java|python|web|intelligence artificielle|machine learning"
    r"|syst[eè]mes? (et|&) r[ée]seaux?|r[ée]seaux? (et|&) t[ée]l[ée]com\w*|admin\w* (syst|r[ée]seau)\w*"
    r"|helpdesk|support (it|informatique)|technicien (it|informatique)|ing[ée]nieur (logiciel|syst[eè]me|cloud|data))\b",
    re.I)

def lire(d, chemin):
    for cle in chemin.split("."):
        d = d.get(cle) if isinstance(d, dict) else None
    return d

toutes, info, satures = {}, {}, []
for dep in DEPARTEMENTS:
    r = requests.get(URL, params={"departements": dep}, headers=CLES, timeout=30)
    jobs = r.json().get("jobs", []) if r.ok else []
    par_source = Counter(lire(j, "identifier.partner_label") for j in jobs)
    satures += [f"{dep}/{s}" for s, n in par_source.items() if n >= 150]
    for j in jobs:
        cle = lire(j, "identifier.id") or lire(j, "apply.url")
        toutes[cle] = j
        if INFO.search(lire(j, "offer.title") or ""):
            info[cle] = j
    print(f"{dep} ", end="", flush=True)
    time.sleep(0.3)

print(f"\n\nAlternances en France, tous métiers : {len(toutes)}")
print(f"Dont informatique (titre) : {len(info)}")
print(f"Départements/sources à la limite de 150 : {satures or 'aucun'}")
print("\n25 exemples :")
for j in list(info.values())[:25]:
    print(" -", (lire(j, "offer.title") or "")[:65], "|", lire(j, "workplace.location.address"))