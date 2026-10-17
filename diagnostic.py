import re
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
PAGES = [
    "https://recrutement.airfrance.com/offre-de-emploi/liste-toutes-offres.aspx?all=1&mode=list",
    "https://careers.smartrecruiters.com/BPIFrance",
    "https://ag.wd3.myworkdayjobs.com/en-US/Airbus",
]
# Mots qu'on s'attend à trouver dans l'adresse d'une offre
MOTIF = re.compile(r"job|offre|offer|emploi|poste|position|vacanc|annonce|requisition|\d{4,}", re.I)

with sync_playwright() as p:
    navigateur = p.chromium.launch()
    for url in PAGES:
        page = navigateur.new_page(user_agent=UA)
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(5000)   # 5 s pour laisser la liste s'afficher
        liens = page.eval_on_selector_all("a", "els => els.map(e => e.href)")
        candidats = sorted({l for l in liens if MOTIF.search(l)})
        print(f"\n=== {url}\n{len(liens)} liens, dont {len(candidats)} ressemblent à des offres :")
        for l in candidats[:8]:
            print("  ", l)
        page.close()
    navigateur.close()