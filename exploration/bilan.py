"""Carte 5 — bilan chiffré du projet. Lecture seule : rien n'est modifié, rien n'est envoyé.
    python exploration/bilan.py ~/Agent-IA-veille-alternance-data/veilleur.db > ~/bilan.txt
"""
import sqlite3
import sys

base = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
q = lambda sql: base.execute(sql).fetchall()


def titre(t):
    print("\n" + "=" * 60 + f"\n{t}")


titre("1. Passages (journal)")
for r in q("""SELECT moteur, COUNT(*), MIN(debut), MAX(debut), ROUND(AVG(duree_min), 1), MAX(duree_min),
                     SUM(nouvelles), SUM(envoyees), SUM(erreurs IS NOT NULL AND erreurs != '')
              FROM passages GROUP BY moteur"""):
    print(f"{r[0]:9} {r[1]} passages du {r[2]} au {r[3]} | durée moy {r[4]} min, max {r[5]} | "
          f"nouvelles {r[6]} | envoyées {r[7]} | passages avec erreurs {r[8]}")
print("Envoyées par jour :")
for r in q("SELECT substr(debut, 1, 10) j, moteur, SUM(envoyees) FROM passages GROUP BY j, moteur ORDER BY j"):
    print(f"   {r[0]} {r[1]:9} {r[2]}")

titre("2. Capteur (La bonne alternance) — verdicts")
print("total offres mémorisées :", q("SELECT COUNT(*) FROM offres_capteur")[0][0])
for r in q("""SELECT verdict, verdict2, envoyee, COUNT(*) FROM offres_capteur
              GROUP BY 1, 2, 3 ORDER BY 4 DESC"""):
    print(f"   étape1={r[0]!s:12} étape2={r[1]!s:12} envoyée={r[2]} : {r[3]}")

titre("3. Veilleur (sites carrières) — verdicts")
print("total offres mémorisées :", q("SELECT COUNT(*) FROM offres")[0][0],
      "| entreprises :", q("SELECT COUNT(DISTINCT entreprise) FROM offres")[0][0])
for r in q("""SELECT verdict, verdict2, envoyee, COUNT(*) FROM offres
              GROUP BY 1, 2, 3 ORDER BY 4 DESC"""):
    print(f"   étape1={r[0]!s:12} étape2={r[1]!s:12} envoyée={r[2]} : {r[3]}")

titre("4. Veilleur — entreprises ayant donné au moins une offre retenue à l'étape 2")
for r in q("""SELECT entreprise, COUNT(*) FROM offres WHERE verdict2 IS NOT NULL AND verdict2 != 'non'
              GROUP BY entreprise ORDER BY 2 DESC"""):
    print(f"   {r[1]:3} × {r[0]}")
