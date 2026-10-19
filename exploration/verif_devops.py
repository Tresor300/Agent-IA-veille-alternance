import sqlite3, html, re
from capteur import INFO

TECH = re.compile(r"devops|devsecops|cloud|\bsre\b|infra|kubernetes|docker|linux|ansible|terraform"
                  r"|syst[eè]me|r[ée]seau|s[ée]curit|cyber|data|d[ée]velopp|logiciel|informati", re.I)

titres = [html.unescape(t or "") for (t,) in sqlite3.connect("data/veilleur.db").execute("SELECT titre FROM offres_api")]
gardees = [t for t in titres if INFO.search(t)]
rejetees = [t for t in titres if not INFO.search(t)]
print(f"Sur {len(titres)} offres : {len(gardees)} gardées, {len(rejetees)} rejetées\n")

print("=== Offres DevOps / Cloud / Infra / Systèmes / Réseau / Data / Dev (toutes) ===")
for t in sorted(t for t in titres if TECH.search(t)):
    print(" ✓" if INFO.search(t) else " ✗ REJETÉE :", t[:80])

print("\n=== Toutes les rejetées ===")
for t in rejetees:
    print(" ✗", t[:80])