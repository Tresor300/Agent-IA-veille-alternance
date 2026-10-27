#!/bin/bash
# Envoie dans le dépôt privé la dernière liste « pages_a_surveiller » téléchargée dans Windows.
# Usage (depuis n'importe quel dossier) :   ~/Agent-IA-veille-alternance/envoyer_pages.sh
set -e
DEPOT=~/Agent-IA-veille-alternance-data
TELECHARGEMENTS=/mnt/c/Users/PC/Downloads

# 1. Pas pendant un passage : ils démarrent aux heures paires à h+17 et durent environ 50 min
heure=$((10#$(date +%H))); minute=$((10#$(date +%M)))
if { [ $((heure % 2)) -eq 0 ] && [ "$minute" -ge 15 ]; } || { [ $((heure % 2)) -eq 1 ] && [ "$minute" -le 10 ]; }; then
    echo "⛔ Un passage de l'agent est probablement en cours (h+17 → h+1h10)."
    echo "   Vérifie l'onglet Actions ou réessaie après $(( (heure + (heure % 2 == 0 ? 1 : 0)) % 24 ))h10."
    exit 1
fi

# 2. Le fichier téléchargé le plus récent
FICHIER=$(ls -t "$TELECHARGEMENTS"/pages_a_surveiller*.xlsx 2>/dev/null | head -1)
[ -z "$FICHIER" ] && { echo "⛔ Aucun pages_a_surveiller*.xlsx dans $TELECHARGEMENTS"; exit 1; }
echo "📄 Fichier utilisé : $FICHIER ($(date -r "$FICHIER" '+%d/%m %H:%M'))"

# 3. Copie alignée sur GitHub (la version de GitHub fait foi), puis remplacement du fichier
cd "$DEPOT"
git fetch --quiet
git reset --hard --quiet origin/main
cp "$FICHIER" pages_a_surveiller.xlsx
rm -f ./*Zone.Identifier

# 4. Contrôle : le fichier se lit et contient des pages surveillées
python3 -c "
import pandas as pd
d = pd.read_excel('pages_a_surveiller.xlsx')
n = d['Verdict'].isin(['✅ Fiable', '🔧 Corrigée']).sum()
print(f'✅ Fichier lisible : {len(d)} entreprises, {n} pages surveillées')
assert n > 50, 'trop peu de pages surveillées : fichier suspect'
"

# 5. Envoi
if git diff --quiet; then
    echo "ℹ️  Ce fichier est identique à celui de GitHub : rien à envoyer."
    exit 0
fi
git add pages_a_surveiller.xlsx
git commit --quiet -m "Pages à surveiller : mise à jour du $(date '+%d/%m/%Y %H:%M')"
git push --quiet
echo "🚀 Liste envoyée. Elle servira au prochain passage."