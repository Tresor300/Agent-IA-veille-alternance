import sqlite3
from datetime import datetime
from playwright.sync_api import sync_playwright

URL = "https://vousfaciliter-it.fr/offres-emploi"
ENTREPRISE = "VFLIT"
BASE = "data/veilleur.db"

def extraire_offres(page):
    """Renvoie {adresse de l'offre: titre} pour les liens situés sous la page carrière."""
    base = page.url.rstrip("/") + "/"
    liens = page.eval_on_selector_all(
        "a", "els => els.map(e => [e.innerText.trim(), e.href])")
    offres = {}
    for texte, href in liens:
        href = href.split("#")[0]
        if href.startswith(base) and len(href) > len(base):
            texte = " ".join(texte.split())
            if len(texte) > len(offres.get(href, "")):
                offres[href] = texte
    return offres

def garder_nouvelles(offres, entreprise):
    """Enregistre les offres jamais vues et renvoie uniquement celles-là."""
    connexion = sqlite3.connect(BASE)
    connexion.execute("""CREATE TABLE IF NOT EXISTS offres (
        url TEXT PRIMARY KEY, entreprise TEXT, titre TEXT, vue_le TEXT)""")
    nouvelles = {}
    for url, titre in offres.items():
        deja_vue = connexion.execute(
            "SELECT 1 FROM offres WHERE url = ?", (url,)).fetchone()
        if not deja_vue:
            connexion.execute("INSERT INTO offres VALUES (?, ?, ?, ?)",
                (url, entreprise, titre, datetime.now().isoformat(timespec="seconds")))
            nouvelles[url] = titre
    connexion.commit()
    connexion.close()
    return nouvelles

# Sites à surveiller : (entreprise, page carrière)
SITES = [
    ("VFLIT", "https://vousfaciliter-it.fr/offres-emploi"),
    ("Site cassé (test)", "https://site-qui-nexiste-pas-12345.fr/carrieres"),
]

def visiter(navigateur, url, essais=2):
    """Renvoie (offres, erreur). Ne plante jamais : en cas d'échec, offres est vide."""
    erreur = None
    for essai in range(essais):
        page = navigateur.new_page()
        try:
            reponse = page.goto(url, wait_until="networkidle", timeout=30000)
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

with sync_playwright() as p:
    navigateur = p.chromium.launch()
    for entreprise, url in SITES:
        offres, erreur = visiter(navigateur, url)
        if erreur:
            print(f"⚠️  {entreprise} : erreur ({erreur}) — site ignoré pour ce passage")
            continue
        nouvelles = garder_nouvelles(offres, entreprise)
        print(f"{entreprise} : {len(offres)} offres en ligne, dont {len(nouvelles)} nouvelles")
        for url_offre, titre in nouvelles.items():
            print(f" 🆕 {titre}\n    {url_offre}")
    navigateur.close()