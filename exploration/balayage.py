import os, re, math, time
from collections import Counter
import requests
from dotenv import load_dotenv

load_dotenv()
URL = "https://api.apprentissage.beta.gouv.fr/api/job/v1/search"
CLES = {"Authorization": f"Bearer {os.environ['LBA_API_KEY']}"}
INFO = re.compile(
    r"\b(informatique|d[ée]veloppeu[rs]e?|devops|devsecops|data|cyber\w*|cloud|logiciel"
    r"|full.?stack|front.?end|back.?end|java|python|web|intelligence artificielle|machine learning"
    r"|syst[eè]mes? (et|&) r[ée]seaux?|r[ée]seaux? (et|&) t[ée]l[ée]com\w*|admin\w* (syst|r[ée]seau)\w*"
    r"|helpdesk|support (it|informatique)|technicien (it|informatique)|ing[ée]nieur (logiciel|syst[eè]me|cloud|data))\b",
    re.I)

toutes, compteur, encore_plafonne = {}, {"requetes": 0}, []

def chercher(lat, lon, rayon):
    for essai in range(2):
        try:
            r = requests.get(URL, headers=CLES, timeout=30,
                             params={"latitude": round(lat, 4), "longitude": round(lon, 4), "radius": round(rayon)})
            compteur["requetes"] += 1
            time.sleep(0.2)
            return r.json().get("jobs", []) if r.ok else []
        except requests.RequestException:
            time.sleep(2)
    return []

def balayer(lat, lon, rayon):
    jobs = chercher(lat, lon, rayon)
    for j in jobs:
        toutes[j["identifier"]["id"]] = j
    plafonne = any(n >= 150 for n in Counter(j["identifier"]["partner_label"] for j in jobs).values())
    if plafonne and rayon > 3:
        d_lat = (rayon / 2) / 111
        d_lon = d_lat / math.cos(math.radians(lat))
        for a in (-1, 1):
            for b in (-1, 1):
                balayer(lat + a * d_lat, lon + b * d_lon, rayon * 0.71)
    elif plafonne:
        encore_plafonne.append((round(lat, 3), round(lon, 3)))

def grille_metropole(rayon=30):
    pas_lat = rayon * 1.4 / 111
    lat = 41.3
    while lat <= 51.2:
        pas_lon = pas_lat / math.cos(math.radians(lat))
        lon = -5.2
        while lon <= 9.7:
            yield lat, lon, rayon
            lon += pas_lon
        lat += pas_lat

DOM = [(16.25, -61.58, 60), (14.64, -61.02, 50), (4.94, -52.33, 150), (-21.11, 55.53, 60), (-12.78, 45.15, 40)]

debut = time.time()
cercles = list(grille_metropole()) + DOM
for i, (lat, lon, rayon) in enumerate(cercles, 1):
    balayer(lat, lon, rayon)
    if i % 50 == 0:
        print(f"{i}/{len(cercles)} cercles | {len(toutes)} offres uniques", flush=True)

info = [j for j in toutes.values() if INFO.search(j["offer"]["title"] or "")]
print(f"\nRequêtes envoyées : {compteur['requetes']} | durée : {round((time.time() - debut) / 60, 1)} min")
print(f"Alternances uniques en France : {len(toutes)} (le balayage par département en donnait 10 613)")
print(f"Dont informatique (titre) : {len(info)} (contre 74)")
print(f"Zones encore plafonnées : {encore_plafonne or 'aucune'}")