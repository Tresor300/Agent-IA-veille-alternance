import pandas as pd
import requests

# Mot-signature trouvé dans la page -> nom de la plateforme
SIGNATURES = {
    "myworkdayjobs": "Workday",
    "taleo": "Taleo",
    "successfactors": "SuccessFactors",
    "smartrecruiters": "SmartRecruiters",
    "teamtailor": "Teamtailor",
    "welcometothejungle": "Welcome to the Jungle",
    "greenhouse.io": "Greenhouse",
    "lever.co": "Lever",
    "workable": "Workable",
    "recruitee": "Recruitee",
    "jobvite": "Jobvite",
    "icims": "iCIMS",
    "talent-soft": "Talentsoft (Cegid)",
    "flatchr": "Flatchr",
    "phenompeople": "Phenom",
    "eightfold": "Eightfold",
    "csod.com": "Cornerstone",
}

def detecter_plateforme(url):
    """Ouvre la page carrière et renvoie le nom de la plateforme repérée."""
    try:
        page = requests.get(url, timeout=15,
                            headers={"User-Agent": "Mozilla/5.0"})
    except requests.RequestException:
        return "Erreur (page injoignable)"
    html = page.text.lower()
    for signature, plateforme in SIGNATURES.items():
        if signature in html:
            return plateforme
    return "Non repérée"

df = pd.read_excel("data/Entreprises_cibles.xlsx",
                   sheet_name="Entreprises", header=2)
avec_url = df[df["URL site carrière"].notna()]

# Analyse de toutes les entreprises qui ont une URL
resultats = {}
for i, (index, ligne) in enumerate(avec_url.iterrows(), 1):
    url = ligne["URL site carrière"].split(" | ")[0]
    resultats[index] = detecter_plateforme(url)
    print(f"[{i}/{len(avec_url)}] {ligne['Entreprise']:<25} -> {resultats[index]}")

# Nouvelle colonne "Plateforme", puis enregistrement dans un nouveau fichier
df["Plateforme"] = df.index.map(resultats).fillna("Pas d'URL")
df.to_excel("data/Entreprises_plateformes.xlsx", index=False)

print("\nRépartition par plateforme :")
print(df["Plateforme"].value_counts().to_string())