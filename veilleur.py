import re
import pandas as pd
import sqlite3
from datetime import datetime
from alerte import envoyer
from playwright.sync_api import sync_playwright

URL = "https://vousfaciliter-it.fr/offres-emploi"
ENTREPRISE = "VFLIT"
BASE = "data/veilleur.db"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
# Une offre se reconnaît à son adresse : job, offre, emploi... ou un numéro d'identifiant
MOTIF = re.compile(r"job|offre|offer|emploi|poste|position|vacanc|annonce|requisition|\d{4,}", re.I)

def extraire_offres(page):
    """Renvoie {adresse: titre} pour les liens dont l'adresse ressemble à une offre."""
    page_url = page.url.split("#")[0].rstrip("/")
    liens = page.eval_on_selector_all(
        "a", "els => els.map(e => [e.innerText.trim(), e.href])")
    offres = {}
    for texte, href in liens:
        href = href.split("#")[0]
        if not href.startswith("http") or href.rstrip("/") == page_url:
            continue
        if MOTIF.search(href):
            texte = " ".join(texte.split())
            if len(texte) > len(offres.get(href, "")):
                offres[href] = texte
    return offres

def garder_nouvelles(offres, entreprise):
    """Enregistre les offres jamais vues. Renvoie (nouvelles, première_visite)."""
    connexion = sqlite3.connect(BASE)
    connexion.execute("""CREATE TABLE IF NOT EXISTS offres (
        url TEXT PRIMARY KEY, entreprise TEXT, titre TEXT, vue_le TEXT)""")
    deja = connexion.execute(
        "SELECT COUNT(*) FROM offres WHERE entreprise = ?", (entreprise,)).fetchone()[0]
    nouvelles = {}
    for url, titre in offres.items():
        if not connexion.execute("SELECT 1 FROM offres WHERE url = ?", (url,)).fetchone():
            connexion.execute("INSERT INTO offres VALUES (?, ?, ?, ?)",
                (url, entreprise, titre, datetime.now().isoformat(timespec="seconds")))
            nouvelles[url] = titre
    connexion.commit()
    connexion.close()
    return nouvelles, deja == 0
# Sites à surveiller : pages validées (✅ Fiable et 🔧 Corrigée)
df = pd.read_excel("data/pages_a_surveiller.xlsx")
df = df[df["Verdict"].isin(["✅ Fiable", "🔧 Corrigée"])]
SITES = [(ligne["Entreprise"], ligne["Page à surveiller"]) for _, ligne in df.iterrows()]

def visiter(navigateur, url, essais=2):
    """Renvoie (offres, erreur). Ne plante jamais : en cas d'échec, offres est vide."""
    erreur = None
    for essai in range(essais):
        page = navigateur.new_page(user_agent=UA)
        try:
            reponse = page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(5000)   # 5 s pour laisser la liste s'afficher
            if reponse and reponse.status >= 400:
                raise Exception(f"code HTTP {reponse.status}")
            titre = page.title().lower()
            if "introuvable" in titre or "not found" in titre:
                raise Exception("page introuvable")
            return extraire_offres(page), None
        except Exception as e:
            erreur = str(e).splitlines()[0]   # 1re ligne du message suffit
        finally:
            page.close()
    return {}, erreur

# Filtre provisoire (avant le filtre IA) : seulement les offres en alternance
ALTERNANCE = re.compile(r"alternan|apprenti|apprentissage|contrat pro", re.I)

bilan = {"avec offres": 0, "0 offre": [], "erreur": []}
with sync_playwright() as p:
    navigateur = p.chromium.launch()
    for i, (entreprise, url) in enumerate(SITES, 1):
        offres, erreur = visiter(navigateur, url)
        if erreur:
            print(f"[{i}/{len(SITES)}] ⚠️  {entreprise} : {erreur}")
            bilan["erreur"].append(entreprise)
            continue
        nouvelles, premiere_visite = garder_nouvelles(offres, entreprise)
        print(f"[{i}/{len(SITES)}] {entreprise} : {len(offres)} offres, dont {len(nouvelles)} nouvelles")
        if premiere_visite:
            print("    (première visite : offres mémorisées, pas d'alerte)")
        for url_offre, titre in nouvelles.items():
            passe_filtre = bool(ALTERNANCE.search(titre + " " + url_offre))
            if not passe_filtre:
                etat = "pas d'alerte (filtre)"
            elif premiere_visite:
                etat = "pas d'alerte (1re visite)"
            elif envoyer(f"🆕 {entreprise}\n{titre}\n{url_offre}"):
                etat = "alerte envoyée ✅"
            else:
                etat = "ÉCHEC d'envoi ❌"
            print(f"    🆕 {titre[:60]} → {etat}")
        if offres:
            bilan["avec offres"] += 1
        else:
            bilan["0 offre"].append(entreprise)
    navigateur.close()

print(f"\nBILAN : {bilan['avec offres']} sites avec des offres, "
      f"{len(bilan['0 offre'])} sites à 0 offre, {len(bilan['erreur'])} erreurs")
print("0 offre :", ", ".join(bilan["0 offre"]))
print("Erreurs :", ", ".join(bilan["erreur"]))