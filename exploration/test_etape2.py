import os, json, time, sqlite3, html, re
import requests
from dotenv import load_dotenv

load_dotenv()
LBA = "https://api.apprentissage.beta.gouv.fr/api/job/v1/search"
CLES_LBA = {"Authorization": f"Bearer {os.environ['LBA_API_KEY']}"}
GEM = "https://generativelanguage.googleapis.com/v1beta"
CLE_GEM = {"x-goog-api-key": os.environ["GEMINI_API_KEY"]}
MODELES = ["models/gemini-flash-latest", "models/gemini-flash-lite-latest"]

def lire(d, chemin):
    for cle in chemin.split("."):
        d = d.get(cle) if isinstance(d, dict) else None
    return d

# 1. Offres « oui » et « doute » en base
con = sqlite3.connect("data/veilleur.db")
cibles = {i: v for i, v in con.execute("SELECT id, verdict FROM offres_capteur WHERE verdict IN ('oui','doute')")}

# 2. Récupérer leur description autour de 3 villes
offres = {}
for lat, lon in [(47.218, -1.553), (48.111, -1.680), (48.857, 2.352)]:
    r = requests.get(LBA, headers=CLES_LBA, timeout=30, params={"latitude": lat, "longitude": lon, "radius": 30})
    for j in r.json().get("jobs", []):
        i = lire(j, "identifier.id")
        if i in cibles:
            desc = re.sub(r"<[^>]+>", " ", html.unescape(lire(j, "offer.description") or ""))
            offres[i] = (html.unescape(lire(j, "offer.title") or ""), lire(j, "workplace.name") or "?",
                         " ".join(desc.split())[:1500], cibles[i])
print(f"{len(offres)} offres « oui/doute » retrouvées avec leur description\n")

# 3. Étape 2 : jugement sur l'offre complète
CONSIGNE = (
    "Tu es recruteur. Un élève ingénieur cherche une ALTERNANCE dans un MÉTIER TECHNIQUE de l'informatique.\n"
    "OUI : développement, DevOps, cloud, data et BI (y compris data orientée métier : Power BI, SQL, Python, "
    "tableaux de bord pour le marketing ou la finance), IA, cybersécurité, administration systèmes et réseaux "
    "informatiques, support informatique, ERP (paramétrage, développement), QA/tests.\n"
    "NON : gestion de projet ou PMO (même informatique), chef de projet digital, Product Owner, Product Manager, "
    "AMOA/MOA, informatique RSE ou numérique responsable, vente, management, industrie, maintenance matérielle, "
    "câblage, qualité, marketing, RH, finance, même s'ils utilisent des outils informatiques.\n"
    "Toutes ces offres viennent de La bonne alternance, un service public dédié à l'alternance : "
    "l'absence du mot « alternance » n'est PAS une raison de dire non. Dis non pour le contrat seulement "
    "si l'offre indique clairement un CDI, CDD, stage ou intérim sans alternance.\n"
    "\"à vérifier\" seulement si la description est vide ou trop courte, ou si, après lecture, "
    "tu hésites vraiment entre oui et non.\n"
    "Réponds UNIQUEMENT en JSON {\"verdict\": \"oui\", \"non\" ou \"à vérifier\", \"raison\": \"courte\"}.\n\n"
)

DERNIER = [None]  # modèle qui a répondu en dernier

def juger(titre, entreprise, desc):
    texte = CONSIGNE + f"Titre : {titre}\nEntreprise : {entreprise}\nDescription : {desc}"
    ordre = sorted(MODELES, key=lambda m: m != DERNIER[0])  # le dernier qui a répondu passe en premier
    for modele in ordre:
        for essai in range(2):
            try:
                r = requests.post(f"{GEM}/{modele}:generateContent", headers=CLE_GEM, timeout=20, json={
                    "contents": [{"parts": [{"text": texte}]}],
                    "generationConfig": {"temperature": 0, "responseMimeType": "application/json"}})
            except requests.exceptions.RequestException:
                print(f"   … {modele.split('/')[-1]} ne répond pas")
                continue
            if r.ok:
                try:
                    v = json.loads(r.json()["candidates"][0]["content"]["parts"][0]["text"])
                    DERNIER[0] = modele
                    return v, modele.split("/")[-1]
                except (KeyError, ValueError):
                    pass
            elif r.status_code in (429, 503):
                time.sleep(10)
    return {"verdict": "erreur", "raison": "Gemini indisponible"}, "-"

for i, (titre, entreprise, desc, avant) in offres.items():
    v, modele = juger(titre, entreprise, desc)
    print(f"{avant:5} → {v.get('verdict', '?'):6} | {titre[:55]:55} | {v.get('raison', '')[:70]} [{modele}]")
    time.sleep(2)