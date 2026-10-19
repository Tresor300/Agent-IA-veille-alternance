import os, re, math, time, sqlite3, html
from datetime import datetime
from collections import Counter
import pandas as pd
import requests
from dotenv import load_dotenv
from alerte import envoyer

load_dotenv()
URL = "https://api.apprentissage.beta.gouv.fr/api/job/v1/search"
CLES = {"Authorization": f"Bearer {os.environ['LBA_API_KEY']}"}
BASE = "data/veilleur.db"
NANTES = (47.218, -1.553)
ROMES_INFO = ",".join(f"M18{n:02d}" for n in range(100)) + ",I1401"
INFO = re.compile(
    r"informati|d[ée]velopp(eu|ement)|devops|devsecops|\bsre\b|cloud|infra(structure)?s?\b|logiciel"
    r"|full.?stack|front.?end|back.?end|\bjava\b|python|\bc#|\bc\+\+|react|angular|\.net|android|\bios\b"
    r"|webmaster|\bweb\s?master|d[ée]v(eloppeu)?.{0,3}web|web\s?d[ée]v"
    r"|\bdata\b|donn[ée]es|power\s?bi|business intelligence|\bbi\b|machine learning|apprentissage automatique"
    r"|intelligence artificielle|\bia\b|\bai\b|\bllm"
    r"|cyber|s[ée]curit[ée] (informatique|des syst|si\b)|security|cryptograph|digital trust"
    r"|syst[eè]mes? d.informa|\bsi\b|\bit\b|r[ée]seaux?\b|t[ée]l[ée]com|voip|middleware|container"
    r"|kubernetes|docker|linux|ansible|terraform|observabilit|supervision"
    r"|admin\w*\s*(\(\w+\))?\s*(syst|r[ée]seau)|helpdesk|support (it|informatique|applicatif)"
    r"|technicien (de |du )?(support|proximit)|applicati[fo]|\berp\b|\bsap\b|salesforce|sage x3"
    r"|int[ée]grat(eur|ion)s?\b|\bqa\b|automatisation des tests|tech.?lead|product owner"
    r"|business analy|analyste fonctionnel|\bmoa\b|ing[ée]nieur d[ée]veloppement",
    re.I)
EXCLU = re.compile(r"commercial|foncier|vendeu|vente|\bpaie\b|stock|marketing|business developer", re.I)
DOM = [(16.25, -61.58, 60), (14.64, -61.02, 50), (4.94, -52.33, 150), (-21.11, 55.53, 60), (-12.78, 45.15, 40)]

stats = {"requetes": 0, "piles": 0}
toutes = {}


def lire(d, chemin):
    for cle in chemin.split("."):
        d = d.get(cle) if isinstance(d, dict) else None
    return d


# ---------- 1. Collecte ----------
def chercher(params):
    for essai in range(3):
        try:
            r = requests.get(URL, params=params, headers=CLES, timeout=30)
            stats["requetes"] += 1
            time.sleep(0.2)
            if r.ok:
                return r.json().get("jobs", [])
        except requests.RequestException:
            pass
        time.sleep(3)
    return []


def ranger(jobs):
    for j in jobs:
        ident = lire(j, "identifier.id")
        if ident:
            toutes[ident] = j


def plafonne(jobs):
    return any(n >= 150 for n in Counter(lire(j, "identifier.partner_label") for j in jobs).values())


def balayer(lat, lon, rayon):
    zone = {"latitude": round(lat, 4), "longitude": round(lon, 4), "radius": max(1, round(rayon))}
    jobs = chercher(zone)
    ranger(jobs)
    if not plafonne(jobs):
        return
    if rayon > 5:                      # zone dense : 4 cercles plus petits
        d_lat = (rayon / 2) / 111
        d_lon = d_lat / math.cos(math.radians(lat))
        for a in (-1, 1):
            for b in (-1, 1):
                balayer(lat + a * d_lat, lon + b * d_lon, rayon * 0.71)
    else:                              # pile d'offres au même point : filet informatique
        stats["piles"] += 1
        filet = chercher({**zone, "romes": ROMES_INFO})
        ranger(filet)
        if plafonne(filet):
            print("⚠️ Pile encore plafonnée malgré le filet :", zone)


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


# ---------- 2. Tri et mise en forme ----------
def est_info(j):
    titre = lire(j, "offer.title") or ""
    return bool(INFO.search(titre)) and not EXCLU.search(titre)

def distance_nantes(j):
    coords = lire(j, "workplace.location.geopoint.coordinates")
    if not coords:
        return None
    lon, lat = coords
    la1, lo1, la2, lo2 = map(math.radians, (NANTES[0], NANTES[1], lat, lon))
    a = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return round(6371 * 2 * math.asin(math.sqrt(a)))


CIBLES = [str(n).lower().strip() for n in pd.read_excel("data/pages_a_surveiller.xlsx")["Entreprise"].dropna()]


def est_cible(entreprise):
    e = (entreprise or "").lower()
    return any(len(n) >= 3 and re.search(rf"\b{re.escape(n)}\b", e) for n in CIBLES)


def bloc(j):
    entreprise = lire(j, "workplace.name") or "Entreprise non précisée"
    km = distance_nantes(j)
    etoile = "⭐ " if est_cible(entreprise) else ""
    return (f"{etoile}{html.unescape(lire(j, 'offer.title') or '')}\n"
            f"🏢 {entreprise} · 📍 {lire(j, 'workplace.location.address') or '?'}"
            f"{f' ({km} km)' if km is not None else ''}\n"
            f"{lire(j, 'apply.url') or 'lien indisponible'}\n")


def decouper(entete, blocs, limite=3800):
    messages, courant = [], entete
    for b in blocs:
        if len(courant) + len(b) + 1 > limite:
            messages.append(courant)
            courant = ""
        courant += "\n" + b
    messages.append(courant)
    return messages


# ---------- 3. Programme principal ----------
def lancer():
    debut = time.time()
    cercles = list(grille_metropole()) + DOM
    for i, (lat, lon, rayon) in enumerate(cercles, 1):
        balayer(lat, lon, rayon)
        if i % 100 == 0:
            print(f"{i}/{len(cercles)} cercles | {len(toutes)} offres", flush=True)

    info = {k: j for k, j in toutes.items() if est_info(j)}

    con = sqlite3.connect(BASE)
    con.execute("CREATE TABLE IF NOT EXISTS offres_api (id TEXT PRIMARY KEY, titre TEXT, "
                "entreprise TEXT, lieu TEXT, url TEXT, vue_le TEXT)")
    deja = {r[0] for r in con.execute("SELECT id FROM offres_api")}
    premiere = not deja
    nouvelles = [j for k, j in info.items() if k not in deja]
    nouvelles.sort(key=lambda j: (not est_cible(lire(j, "workplace.name")),
                                  distance_nantes(j) if distance_nantes(j) is not None else 99999))

    if nouvelles:
        entete = (f"🛰️ Capteur — {len(nouvelles)} alternance(s) informatique(s)"
                  f"{' (liste actuelle)' if premiere else ' nouvelle(s)'}\n")
        envoi_ok = all(envoyer(m) for m in decouper(entete, [bloc(j) for j in nouvelles]))
        if envoi_ok:
            maintenant = datetime.now().isoformat(timespec="seconds")
            con.executemany("INSERT OR IGNORE INTO offres_api VALUES (?,?,?,?,?,?)",
                            [(lire(j, "identifier.id"), lire(j, "offer.title"), lire(j, "workplace.name"),
                              lire(j, "workplace.location.address"), lire(j, "apply.url"), maintenant)
                             for j in nouvelles])
            con.commit()
        else:
            print("❌ Échec d'envoi Telegram : offres non mémorisées, elles seront renvoyées.")
    con.close()

    print(f"\n=== BILAN CAPTEUR ({round((time.time() - debut) / 60, 1)} min) ===")
    print(f"Requêtes : {stats['requetes']} | piles traitées : {stats['piles']}")
    print(f"Alternances collectées : {len(toutes)} | informatique : {len(info)} | nouvelles : {len(nouvelles)}")


if __name__ == "__main__":
    lancer()