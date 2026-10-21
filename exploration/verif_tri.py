import sqlite3, html
from capteur import INFO

titres = [html.unescape(t or "") for (t,) in sqlite3.connect("data/veilleur.db").execute("SELECT titre FROM offres_api")]
gardees = [t for t in titres if INFO.search(t)]
rejetees = [t for t in titres if not INFO.search(t)]

print(f"Sur {len(titres)} offres envoyées : {len(gardees)} gardées, {len(rejetees)} rejetées\n")
print("=== 20 REJETÉES (doivent être hors informatique) ===")
for t in rejetees[:20]:
    print(" ✗", t[:75])
print("\n=== 20 GARDÉES (doivent être de l'informatique) ===")
for t in gardees[:20]:
    print(" ✓", t[:75])