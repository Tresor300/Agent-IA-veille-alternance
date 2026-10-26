"""Étape 1 du plan « connecteurs + découvreur » — exploration en lecture seule.

A. Les interfaces publiques officielles des plateformes de recrutement répondent-elles,
   et que donnent-elles (titre, contrat, lieu, description) ?
B. Que donne La bonne alternance sur les entreprises « susceptibles de recruter » (sans offre) ?

Rien n'est écrit, rien n'est envoyé. À lancer depuis le dossier du projet :
    python exploration/explorer_acces.py
"""
import json
import os
import re
from collections import Counter

import requests
from dotenv import load_dotenv

load_dotenv()
ALTERNANCE = re.compile(r"altern|apprenti|apprentissage|work[- ]?study|apprenticeship", re.I)


def lire(d, chemin):
    for cle in chemin.split("."):
        d = d.get(cle) if isinstance(d, dict) else None
    return d


# ---------- A. Interfaces officielles des plateformes ----------
TESTS = [
    # (entreprise, plateforme, adresse de l'interface, où est la liste, champ titre, champ contrat, champ lien, champ description)
    ("Algolia", "Greenhouse", "https://boards-api.greenhouse.io/v1/boards/algolia/jobs?content=true",
     "jobs", "title", None, "absolute_url", "content"),
    ("Qonto", "Lever", "https://api.lever.co/v0/postings/qonto?mode=json",
     None, "text", "categories.commitment", "hostedUrl", "descriptionPlain"),
    ("Sopra Steria", "SmartRecruiters", "https://api.smartrecruiters.com/v1/companies/SopraSteria1/postings?limit=100",
     "content", "name", "typeOfEmployment.label", "ref", None),
    ("Apside", "Recruitee", "https://apside.recruitee.com/api/offers/",
     "offers", "title", "employment_type_code", "careers_url", "description"),
]

print("=" * 70)
print("A. INTERFACES OFFICIELLES DES PLATEFORMES")
print("=" * 70)
for entreprise, plateforme, url, liste, titre, contrat, lien, desc in TESTS:
    print(f"\n▶ {entreprise} ({plateforme})")
    try:
        r = requests.get(url, timeout=30, headers={"Accept": "application/json"})
        print(f"  Code HTTP : {r.status_code}")
        if not r.ok:
            continue
        donnees = r.json()
        offres = donnees if liste is None else donnees.get(liste, [])
        total = donnees.get("totalFound", len(offres)) if isinstance(donnees, dict) else len(offres)
        alt = [o for o in offres if ALTERNANCE.search(f"{lire(o, titre)} {lire(o, contrat) if contrat else ''}")]
        print(f"  Offres renvoyées : {len(offres)} (total annoncé : {total}) — dont alternance : {len(alt)}")
        print(f"  Description fournie : {'oui' if desc and offres and lire(offres[0], desc) else 'non'}")
        for o in (alt or offres)[:3]:
            print(f"   - {str(lire(o, titre))[:60]} | contrat : {lire(o, contrat) if contrat else '?'} | {lire(o, lien)}")
    except Exception as e:
        print(f"  ❌ {type(e).__name__} : {str(e)[:120]}")

# SmartRecruiters accepte une recherche : on vérifie le filtre « alternance »
try:
    r = requests.get("https://api.smartrecruiters.com/v1/companies/SopraSteria1/postings",
                     params={"q": "alternance", "limit": 100}, timeout=30)
    print(f"\n▶ Sopra Steria, recherche « alternance » : code {r.status_code}, "
          f"{r.json().get('totalFound', '?') if r.ok else '-'} offres")
except Exception as e:
    print(f"\n▶ Recherche SmartRecruiters : ❌ {type(e).__name__}")

# ---------- B. Entreprises « susceptibles de recruter » (La bonne alternance) ----------
print("\n" + "=" * 70)
print("B. LA BONNE ALTERNANCE : ENTREPRISES SANS OFFRE")
print("=" * 70)
r = requests.get("https://api.apprentissage.beta.gouv.fr/api/job/v1/search", timeout=60,
                 headers={"Authorization": f"Bearer {os.environ['LBA_API_KEY']}"},
                 params={"latitude": 47.218, "longitude": -1.553, "radius": 30})
print("Code HTTP :", r.status_code)
donnees = r.json()
print("Rubriques de la réponse :", {k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in donnees.items()})


def chemins(objet, prefixe=""):
    if isinstance(objet, dict):
        for k, v in objet.items():
            yield from chemins(v, f"{prefixe}.{k}" if prefixe else k)
    else:
        yield prefixe, json.dumps(objet, ensure_ascii=False)[:80]


rubrique = next((k for k in donnees if "recruit" in k.lower() or "recrut" in k.lower()), None)
print("Rubrique des entreprises sans offre :", rubrique)
if rubrique and donnees[rubrique]:
    entreprises = donnees[rubrique]
    print(f"{len(entreprises)} entreprises autour de Nantes (30 km). Champs de la 1re :")
    for c, v in chemins(entreprises[0]):
        print(f"   - {c} = {v}")
    naf, sites = Counter(), 0
    for e in entreprises:
        champs = dict(chemins(e))
        sites += any("website" in c.lower() and v not in ("null", '""') for c, v in champs.items())
        for c, v in champs.items():
            if "naf" in c.lower() and "code" in c.lower():
                naf[v] += 1
    print(f"\nAvec un site web renseigné : {sites} / {len(entreprises)}")
    print("Codes d'activité (NAF) les plus fréquents :", naf.most_common(12))