import pandas as pd
from playwright.sync_api import sync_playwright

LIMITE = None   # nombre d'entreprises testées (None = toutes)

# Textes de lien qui ressemblent à une liste d'offres
MOTS = ["offres d'emploi", "offres d’emploi", "nos offres", "toutes les offres",
        "voir les offres", "job offers", "search jobs", "jobs", "emplois",
        "opportunités", "postuler", "rejoignez", "nous rejoindre"]
# Plateformes de recrutement : un lien vers elles est un très bon indice
PLATEFORMES = ["myworkdayjobs", "smartrecruiters", "teamtailor", "welcometothejungle",
               "jobs.lever.co", "greenhouse.io", "taleo", "successfactors", "talent-soft"]

def verifier(navigateur, url):
    """Renvoie (statut, adresse finale, page des offres proposée)."""
    page = navigateur.new_page()
    try:
        reponse = page.goto(url, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(3000)   # laisse 3 s au JavaScript pour afficher la page
        if reponse and reponse.status >= 400:
            return f"Erreur HTTP {reponse.status}", page.url, ""
        if any(m in page.title().lower() for m in ["introuvable", "not found", "404"]):
            return "Page introuvable", page.url, ""
        liens = page.eval_on_selector_all(
            "a", "els => els.map(e => [e.innerText.trim().toLowerCase(), e.href])")
        candidats = []
        for texte, href in liens:
            if not href.startswith("http"):
                continue
            score = sum(m in texte for m in MOTS) + 3 * any(p in href for p in PLATEFORMES)
            if score:
                candidats.append((score, href))
        candidats.sort(reverse=True)
        return "OK", page.url, candidats[0][1] if candidats else ""
    except Exception as e:
        return "Erreur : " + str(e).splitlines()[0][:80], url, ""
    finally:
        page.close()

df = pd.read_excel("data/Entreprises_cibles.xlsx", sheet_name="Entreprises", header=2)
df = df[df["URL site carrière"].notna()].head(LIMITE)

resultats = []
with sync_playwright() as p:
    navigateur = p.chromium.launch()
    for i, (_, ligne) in enumerate(df.iterrows(), 1):
        url = str(ligne["URL site carrière"]).split(" | ")[0]
        statut, finale, proposition = verifier(navigateur, url)
        print(f"[{i}/{len(df)}] {ligne['Entreprise']:<30} {statut}")
        resultats.append([ligne["Entreprise"], url, statut, finale, proposition])
    navigateur.close()

sortie = pd.DataFrame(resultats, columns=["Entreprise", "URL Excel", "Statut",
                                          "Adresse finale", "Page des offres proposée"])
sortie.to_excel("data/verification_urls.xlsx", index=False)
print("\nRésultat enregistré dans data/verification_urls.xlsx")
print(sortie["Statut"].value_counts().to_string())