"""Pourquoi le veilleur voit « 0 offre » sur des pages qui en affichent ? Lecture seule, sur ton PC.

Pour chaque page : on l'ouvre comme le veilleur, on attend 10 s, puis on affiche
les liens trouvés (texte + adresse), les cadres intégrés (iframe) et quelques indices.
    python exploration/diagnostic_pages.py
"""
import re
from playwright.sync_api import sync_playwright

PAGES = {
    "Econocom": "https://carrieres.econocom.com/offres-emploi/",
    "Synetis": "https://www.synetis.com/carriere/offres-emplois/",
    "Talentia Software": "https://www.talentia-software.com/fr/carrieres/#position",
    "Tehtris": "https://tehtris.taleez.com/",
    "Betclic Group": "https://betclicgroup.com/people#jobs",
}
MOTIF = re.compile(r"job|offre|offer|emploi|poste|position|vacanc|annonce|requisition|\d{4,}", re.I)
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

with sync_playwright() as p:
    navigateur = p.chromium.launch()
    for nom, url in PAGES.items():
        print("\n" + "=" * 70 + f"\n{nom} — {url}")
        page = navigateur.new_page(user_agent=UA)
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(10000)
            liens = page.eval_on_selector_all("a", "els => els.map(e => [e.innerText.trim(), e.href])")
            retenus = [(t, h) for t, h in liens if h.startswith("http") and MOTIF.search(h)]
            cadres = [f.url for f in page.frames if f.url and f.url != page.url and f.url != "about:blank"]
            texte = " ".join(page.inner_text("body").split())
            print(f"Titre de la page : {page.title()}")
            print(f"Liens : {len(liens)} au total, {len(retenus)} reconnus comme offres par le veilleur")
            print(f"Cadres intégrés (iframe) : {cadres[:5] or 'aucun'}")
            print(f"Boutons « suivant / voir plus » : {page.locator('text=/voir plus|plus d.offres|load more|suivant|next/i').count()}")
            print("Début du texte visible :", texte[:300])
            print("Liens (30 premiers avec du texte) :")
            for t, h in [l for l in liens if l[0]][:30]:
                print(f"   {'✔' if MOTIF.search(h) else ' '} {t[:45]:45} → {h[:90]}")
        except Exception as e:
            print("❌", str(e).splitlines()[0])
        finally:
            page.close()
    navigateur.close()