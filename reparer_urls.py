import pandas as pd
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

# Identité d'un navigateur classique (certains sites bloquent les robots)
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
MOTS_CARRIERE = ["carrière", "carrières", "carriere", "careers", "career", "recrutement",
                 "nous rejoindre", "rejoignez", "rejoindre", "join us", "jobs", "talents"]
MOTS_OFFRES = ["offres d'emploi", "offres d’emploi", "nos offres", "toutes les offres",
               "voir les offres", "job offers", "search jobs", "jobs", "emplois",
               "opportunités", "postuler"]
PLATEFORMES = ["myworkdayjobs", "smartrecruiters", "teamtailor", "welcometothejungle",
               "jobs.lever.co", "greenhouse.io", "taleo", "successfactors", "talent-soft"]

def ouvrir(navigateur, url):
    """Ouvre une page ; lève une erreur si elle est inaccessible."""
    page = navigateur.new_page(user_agent=UA)
    try:
        reponse = page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)
        if reponse and reponse.status >= 400:
            raise Exception(f"code HTTP {reponse.status}")
        return page
    except Exception:
        page.close()
        raise

def meilleur_lien(page, mots, bonus_plateforme=False):
    """Renvoie le lien dont le texte ressemble le plus aux mots donnés."""
    liens = page.eval_on_selector_all(
        "a", "els => els.map(e => [e.innerText.trim().toLowerCase(), e.href])")
    candidats = []
    for texte, href in liens:
        if not href.startswith("http"):
            continue
        score = sum(m in texte for m in mots)
        if bonus_plateforme:
            score += 3 * any(p in href for p in PLATEFORMES)
        if score:
            candidats.append((score, href))
    candidats.sort(reverse=True)
    return candidats[0][1] if candidats else ""

def domaine(url):
    """careers.blablacar.com -> blablacar.com (None si c'est une plateforme de recrutement)."""
    hote = urlparse(url).netloc.lower()
    if any(p in hote for p in PLATEFORMES + ["recrute.fr"]):
        return None
    return ".".join(hote.split(".")[-2:])

def reparer(navigateur, url):
    """Renvoie (méthode, page carrière, page des offres)."""
    # 1) Réessayer l'URL d'origine avec une identité de navigateur classique
    try:
        page = ouvrir(navigateur, url)
        offres = meilleur_lien(page, MOTS_OFFRES, True) or page.url
        page.close()
        return "OK au 2e essai", url, offres
    except Exception:
        pass
    # 2) Repartir de la page d'accueil de l'entreprise
    racine = domaine(url)
    if not racine:
        return "À chercher à la main (ancienne plateforme)", "", ""
    for accueil in [f"https://www.{racine}", f"https://{racine}"]:
        try:
            page = ouvrir(navigateur, accueil)
            carriere = meilleur_lien(page, MOTS_CARRIERE)
            page.close()
            if not carriere:
                return "Accueil OK, lien carrière non trouvé", accueil, ""
            page = ouvrir(navigateur, carriere)
            offres = meilleur_lien(page, MOTS_OFFRES, True) or page.url
            page.close()
            return "Réparée via l'accueil", carriere, offres
        except Exception:
            continue
    return "Échec", "", ""

df = pd.read_excel("data/verification_urls.xlsx")
a_reparer = df[df["Statut"] != "OK"]
print(f"{len(a_reparer)} entreprises à réparer\n")

with sync_playwright() as p:
    navigateur = p.chromium.launch()
    for i, (index, ligne) in enumerate(a_reparer.iterrows(), 1):
        methode, carriere, offres = reparer(navigateur, ligne["URL Excel"])
        print(f"[{i}/{len(a_reparer)}] {ligne['Entreprise']:<30} {methode}")
        df.loc[index, ["Statut", "Adresse finale", "Page des offres proposée"]] = \
            [methode, carriere, offres]
    navigateur.close()

df.to_excel("data/verification_urls_v2.xlsx", index=False)
print("\nRésultat enregistré dans data/verification_urls_v2.xlsx")
print(df["Statut"].value_counts().to_string())