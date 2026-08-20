#!/usr/bin/env python3
"""Vuelta 2026 fantasy roster -> PCS integration.

Offline variant of vuelta-pcs-script.py: instead of scraping PCS live (blocked
in the remote session), it reuses the repo's cached PCS snapshots
(pcs_riders_data.csv = 2026 season points, pcs_riders_12m.csv, wins_2026.csv,
all scraped 2026-06-30) and matches the Vuelta 2026 fantasy roster from
all_vuelta_riders.csv against them.

Matching = explicit manual map for every name the fuzzy pass can't resolve
safely (Spanish double surnames, renamed teams, PCS spelling quirks), fuzzy
initial+surname fallback for the rest. Every fuzzy match below similarity 1.0
is printed for manual review.

Outputs combined_vuelta_data.json / .csv in the same shape app.py loads for
race_type='vuelta' (pcs_points_2025 = current-season points, see CLAUDE.md).
"""

import csv
import json
import re
from datetime import datetime
from difflib import SequenceMatcher

from value_utils import recompute_value

FANTASY_CSV = 'all_vuelta_riders.csv'
PCS_2026_CSV = 'pcs_riders_data.csv'
PCS_12M_CSV = 'pcs_riders_12m.csv'
WINS_CSV = 'wins_2026.csv'

# Verified fantasy-name -> PCS-name pairs. Fuzzy handles plain "X. SURNAME"
# cases; everything ambiguous (double surnames, renamed riders, diacritics)
# is pinned here. None = genuinely absent from the cached PCS top 1500.
MANUAL_MAP = {
    'T. POGACAR': 'POGAČAR Tadej',
    'P. ROGLIC': 'ROGLIČ Primož',
    'E. MAS NICOLAU': 'MAS Enric',
    'J. BRENNAN': 'BRENNAN Matthew',          # Visma; fantasy initial is wrong, only one Brennan there
    'M. SKJELMOSE': 'SKJELMOSE Mattias',
    'E. ONLEY': 'ONLEY Oscar',                # fantasy shows E., PCS Oscar Onley
    'C. RODRIGUEZ': 'RODRÍGUEZ Carlos',
    'C. UIJTDEBROEKS': 'UIJTDEBROEKS Cian',
    'M. LANDA MEANA': 'LANDA Mikel',
    'S. BUITRAGO SANCHEZ': 'BUITRAGO Santiago',
    'J. NORDHAGEN': 'NORDHAGEN Jørgen',
    'I. ROMEO ABAD': 'ROMEO Iván',
    'L. BISIAUX': 'BISIAUX Léo',
    'G. MARTIN GUYONNET': 'MARTIN Guillaume',
    'D. MARTINEZ POVEDA': 'MARTÍNEZ Daniel Felipe',
    'P. CASTRILLO ZAPATER': 'CASTRILLO Pablo',
    'V. PARET PEINTRE': 'PARET-PEINTRE Valentin',
    'H. TEJADA CANACUE': 'TEJADA Harold',
    'T. JOHANNESSEN': 'JOHANNESSEN Tobias Halland',
    'R. GARCIA PIERNA': 'GARCÍA PIERNA Raúl',
    'I. IZAGIRRE INSAUSTI': 'IZAGIRRE Ion',
    'C. RODRIGUEZ MARTIN': 'RODRÍGUEZ Cristián',
    'E. RUBIO REYES': 'RUBIO Einer',
    'O. AULAR SANABRIA': 'AULAR Orluis',
    'P. BILBAO LOPEZ DE ARMENTIA': 'BILBAO Pello',
    'G. Mühlberger': 'MÜHLBERGER Gregor',
    'M. CORT NIELSEN': 'CORT Magnus',
    'P. TORRES ARIAS': 'TORRES Pablo',
    'U. BERRADE FERNANDEZ': 'BERRADE Urko',
    'F. FISHER - BLACK': 'FISHER-BLACK Finn',
    'S. CRAS': 'CRAS Steff',
    'J. LOPEZ PEREZ': 'LÓPEZ Juan Pedro',
    'A. FAGUNDEZ LIMA': 'FAGÚNDEZ Eric Antonio',
    'J. DIAZ GALLEGO': 'DÍAZ José Manuel',
    'S. HIGUITA GARCIA': 'HIGUITA Sergio',
    'D. DE LA CRUZ MELGAREJO': 'DE LA CRUZ David',
    'I. SOSA CUERVO': 'SOSA Iván Ramiro',
    'M. CAMPRUBI  PIJUAN': 'CAMPRUBÍ Marcel',
    'R. ADRIA OLIVERAS': 'ADRIÀ Roger',       # TdF map's 'OLIVEIRA Rui' was wrong; Movistar, ES
    'H. MULUEBERHAN': 'MULUBRHAN Henok',
    'P. Øxenberg': 'ØXENBERG Peter',
    'S. CHUMIL GONZALEZ': 'CHUMIL Sergio Geovani',
    'M. APARICIO MUÑOZ': 'APARICIO Mario',
    'B. RIVERA VARGAS': 'RIVERA Brandon Smith',
    'M. BRUSTENGA MASAGUE': 'BRUSTENGA Marc',
    'C. CANAL BLANCO': 'CANAL Carlos',
    'I. RUIZ SEDANO': 'RUIZ Ibon',
    'Y. FEDOROV': 'FEDOROV Yevgeniy',
    'M. VAN DEN BERG': 'VAN DEN BERG Marijn',
    'V. LAENGEN': 'LAENGEN Vegard Stake',
    'M. BELOKI FERNANDEZ': 'BELOKI Markel',
    'X. AZPARREN IRURZUN': 'AZPARREN Xabier Mikel',
    'S. DALBY': 'DALBY Simon',
    'V. ALBANESE': 'ALBANESE Vincenzo',
    'A. RENARD': 'RENARD Alexis',
    'I. COBO CAYON': 'COBO Iván',
    'E. SVESTAD-BÅRDSENG': 'SVESTAD-BÅRDSENG Embret',
    'A. L\'HOTE': 'L\'HOTE Antoine',
    'C. MACIAS ESTRADA': 'MACÍAS César',
    'G. GLIVAR': 'GLIVAR Gal',
    'M. VAN DER MEULEN': 'VAN DER MEULEN Max',
    'D. URIARTE BELZUNEGI': 'URIARTE Diego',
    'J. LABROSSE': 'LABROSSE Jordan',
    'E. LIEPINS': 'LIEPIŅŠ Emīls',
    'I. ALVES OLIVEIRA': 'OLIVEIRA Ivo',
    'A. GHEBREIGZABHIER': 'GHEBREIGZABHIER Amanuel',
    'J. RODRIGUEZ CONTRERAS': 'RODRIGUEZ Juan Felipe',
    'S. NORSGAARD': 'SUNEKÆR NORSGAARD Mathias',
    'S. FERNANDEZ RODRIGUEZ': 'FERNÁNDEZ Sinuhé',
    'L. VAN BOVEN': 'VAN BOVEN Luca',
    'H. DE LA CALLE ARANGO': 'DE LA CALLE Hugo',
    'J. FAURA ASENSIO': 'FAURA José Luis',
    'I. ELOSEGUI MOMEÑE': 'ELOSEGUI Iñigo',
    'U. IRIBAR JAUREGI': 'IRIBAR Unai',
    'P. MIQUEL DELGADO': 'MIQUEL Pau',
    'J. VAN DEN BERG': 'VAN DEN BERG Julius',
    'D. GONZALEZ LOPEZ': 'GONZÁLEZ David',
    'J. GUTIERREZ GONZALEZ': 'GUTIÉRREZ Jorge',
    'J. JENSEN': 'PLOWRIGHT Jensen',
    'S. SAMITIER SAMITIER': 'SAMITIER Sergio',
    'D. CAVIA SANZ': 'CAVIA Daniel',
    'C. PEREZ LOPEZ': 'PÉREZ César',
    'M. VAN GILS': 'VAN GILS Maxim',
    'P. MARTI SORIANO': 'MARTÍ Pau',
    'S. DE SCHUYTENEER': 'DE SCHUYTENEER Steffen',
    'P. ALLEGAERT': 'ALLEGAERT Piet',
    'L. SLOCK': 'SLOCK Liam',
    'L. CRAPS': 'CRAPS Lars',
    'R. DEBRUYNE': 'DEBRUYNE Ramses',
    'J. BIERMANS': 'BIERMANS Jenthe',
    'B. ROLLAND': 'ROLLAND Brieuc',
    'R. VAN SINTMAARTENSDIJK': 'VAN SINTMAARTENSDIJK Roel',
    'V. BRAET': 'BRAET Vito',
    'S. DE PESTEL': 'DE PESTEL Sander',
    'M. PAASSCHENS': 'PAASSCHENS Mathijs',
    'P. GAMPER': 'GAMPER Patrick',
    'P. OURSELIN': 'OURSELIN Paul',
    'D. VAN BEKKUM': 'VAN BEKKUM Darren',
    'K. VERMAERKE': 'VERMAERKE Kevin',
    'D. NOVAK': 'NOVAK Domen',
    'A. LUTSENKO': 'LUTSENKO Alexey',
    'E. BUCHMANN': 'BUCHMANN Emanuel',
    'L. KÄMNA': 'KÄMNA Lennard',
    'C. HARPER': 'HARPER Chris',
    'C. BERTHET': 'BERTHET Clément',
    'C. CHAMPOUSSIN': 'CHAMPOUSSIN Clément',
    'K. BOUWMAN': 'BOUWMAN Koen',
    'G. BENNETT': 'BENNETT George',
    'A. LEKNESSUND': 'LEKNESSUND Andreas',
    'L. DE PLUS': 'DE PLUS Laurens',
    'I. VAN WILDER': 'VAN WILDER Ilan',
    'B. ARMIRAIL': 'ARMIRAIL Bruno',
    'V. MADOUAS': 'MADOUAS Valentin',
    'Q. PACHER': 'PACHER Quentin',
    'L. VERVAEKE': 'VERVAEKE Louis',
    'J. BERNARD': 'BERNARD Julien',
    'L. WARBASSE': 'WARBASSE Larry',
    'F. DVERSNES': 'DVERSNES LAVIK Fredrik',
    'W. BARTA': 'BARTA Will',
    'N. EEKHOFF': 'EEKHOFF Nils',
    'A. LAURANCE': 'LAURANCE Axel',
    'D. TEUNS': 'TEUNS Dylan',
    'S. GRIGNARD': 'GRIGNARD Sébastien',
    'M. SCHACHMANN': 'SCHACHMANN Maximilian',
    'G. VERMEERSCH': 'VERMEERSCH Gianni',
    'M. MAYRHOFER': 'MAYRHOFER Marius',
    'L. ROTA': 'ROTA Lorenzo',
    'C. SCOTSON': 'SCOTSON Callum',
    'R. TILLER': 'TILLER Rasmus',
    'G. MOSCON': 'MOSCON Gianni',
    'B. TRONCHON': 'TRONCHON Bastien',
    'T. NYS': 'NYS Thibau',
    'L. PLAPP': 'PLAPP Luke',
    'W. VAN AERT': 'VAN AERT Wout',
    'M. PEDERSEN': 'PEDERSEN Mads',
    'S. KÜNG': 'KÜNG Stefan',
    'B. COQUARD': 'COQUARD Bryan',
    'E. DUNBAR': 'DUNBAR Eddie',
    'J. ALMEIDA': 'ALMEIDA João',
    'P. SIVAKOV': 'SIVAKOV Pavel',
    'P. BLACKMORE': 'BLACKMORE Joseph',
    'T. DE JONG': 'DE JONG Timo',
}

def norm(s):
    return re.sub(r'[^\w\s]', '', (s or '').upper()).strip()

def fantasy_surname(name):
    parts = norm(name).split()
    return ' '.join(parts[1:]) if len(parts) >= 2 and len(parts[0]) <= 2 else ' '.join(parts)

def fantasy_initial(name):
    parts = norm(name).split()
    return parts[0][0] if parts and len(parts[0]) <= 2 else ''

def pcs_split(name):
    """PCS format: SURNAME(S) Firstname(s) — surname tokens are ALL-CAPS."""
    tokens = name.split()
    sur, first = [], []
    for t in tokens:
        if t.upper() == t and not first:
            sur.append(t)
        else:
            first.append(t)
    return norm(' '.join(sur)), norm(' '.join(first))

def team_sim(a, b):
    na = re.sub(r'\s*(TEAM|CYCLING|PRO)\s*', ' ', norm(a))
    nb = re.sub(r'\s*(TEAM|CYCLING|PRO)\s*', ' ', norm(b))
    na, nb = re.sub(r'\s+', ' ', na).strip(), re.sub(r'\s+', ' ', nb).strip()
    if na == nb:
        return 1.0
    if na and nb and (na in nb or nb in na):
        return 0.8
    return SequenceMatcher(None, na, nb).ratio()

def find_fuzzy(fr, pcs_riders):
    f_sur, f_ini = fantasy_surname(fr['fantasy_name']), fantasy_initial(fr['fantasy_name'])
    best, best_score = None, 0.0
    for pr in pcs_riders:
        p_sur, p_first = pcs_split(pr['name'])
        sur_sim = SequenceMatcher(None, f_sur, p_sur).ratio()
        if sur_sim < 0.55:
            continue
        ini_ok = bool(p_first) and p_first[0] == f_ini
        score = 0.62 * sur_sim + (0.18 if ini_ok else 0.0) + 0.20 * team_sim(fr['team'], pr.get('team', ''))
        if score > best_score:
            best, best_score = pr, score
    return (best, best_score) if best_score >= 0.62 else (None, 0.0)

def main():
    fantasy = []
    with open(FANTASY_CSV, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            fantasy.append({
                'fantasy_name': row['Meno jazdca'].strip(),
                'team': row['Tím'].strip(),
                'category': row['Kategória'].strip(),
                'price': int(row['Cena']) if row['Cena'].isdigit() else 0,
            })

    with open(PCS_2026_CSV, encoding='utf-8') as f:
        pcs = list(csv.DictReader(f))
    for r in pcs:
        r['points'] = float(r['points'] or 0)
        r['rank'] = int(r['rank']) if str(r['rank']).isdigit() else r['rank']
    by_name = {r['name']: r for r in pcs}

    with open(PCS_12M_CSV, encoding='utf-8') as f:
        p12 = {r['name']: float(r['points_12m'] or 0) for r in csv.DictReader(f)}
    with open(WINS_CSV, encoding='utf-8') as f:
        wins = {r['pcs_name']: int(r['wins_2026'] or 0) for r in csv.DictReader(f)}

    out, review, unmatched = [], [], []
    for fr in fantasy:
        pcs_match, sim, how = None, 0.0, ''
        if fr['fantasy_name'] in MANUAL_MAP:
            target = MANUAL_MAP[fr['fantasy_name']]
            if target is not None:
                pcs_match = by_name.get(target)
                sim, how = 1.0, 'manual'
                if pcs_match is None and target in p12:
                    # outside the season top-1500 snapshot but present in the
                    # 12-month ranking -> keep the match with 0 season points
                    pcs_match = {'name': target, 'rank': None, 'points': 0.0,
                                 'nationality': None, 'team': None, 'rider_url': None}
                    how = 'manual-12m'
                elif pcs_match is None:
                    print(f"!! manual target missing in PCS csv: {fr['fantasy_name']} -> {target}")
            else:
                how = 'manual-none'
        else:
            pcs_match, sim = find_fuzzy(fr, pcs)
            how = 'fuzzy'
            if pcs_match:
                review.append((fr['fantasy_name'], fr['team'], pcs_match['name'],
                               pcs_match.get('team', ''), round(sim, 3)))

        rider = {
            'fantasy_name': fr['fantasy_name'], 'team': fr['team'],
            'category': fr['category'], 'price': fr['price'],
            'pcs_match_found': pcs_match is not None,
            'match_similarity': round(sim, 3) if pcs_match else 0.0,
        }
        if pcs_match:
            rider.update({
                'pcs_name': pcs_match['name'], 'pcs_rank': pcs_match['rank'],
                'pcs_points_2025': pcs_match['points'],
                'pcs_points_12m': p12.get(pcs_match['name'], 0),
                'wins_2026': wins.get(pcs_match['name'], 0),
                'pcs_nationality': pcs_match.get('nationality'),
                'pcs_team': pcs_match.get('team'), 'pcs_url': pcs_match.get('rider_url'),
            })
        else:
            rider.update({'pcs_name': None, 'pcs_rank': None, 'pcs_points_2025': 0,
                          'pcs_points_12m': 0, 'wins_2026': 0, 'pcs_nationality': None,
                          'pcs_team': None, 'pcs_url': None})
            unmatched.append((fr['fantasy_name'], fr['team'], fr['price'], how))
        out.append(rider)

    recompute_value(out)

    with open('combined_vuelta_data.json', 'w', encoding='utf-8') as f:
        json.dump({
            'integration_info': {
                'type': 'Fantasy Vuelta + PCS Data Integration',
                'edition': 'Vuelta 2026',
                'fantasy_riders_count': len(fantasy),
                'pcs_riders_count': len(pcs),
                'matched_riders': sum(1 for r in out if r['pcs_match_found']),
                'pcs_snapshot_date': '2026-06-30',
                'last_update': datetime.now().isoformat(),
                'race_type': 'vuelta',
            },
            'riders': out,
        }, f, ensure_ascii=False, indent=2)

    cols = ['fantasy_name', 'team', 'category', 'price', 'pcs_match_found', 'match_similarity',
            'pcs_name', 'pcs_rank', 'pcs_points_2025', 'pcs_points_12m', 'wins_2026',
            'pcs_nationality', 'pcs_team', 'pcs_url', 'value_points', 'points_per_credit',
            'value_category']
    with open('combined_vuelta_data.csv', 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in out:
            w.writerow({c: r.get(c) for c in cols})

    print(f"matched {sum(1 for r in out if r['pcs_match_found'])}/{len(out)}")
    print('\n-- FUZZY MATCHES (review) --')
    for row in sorted(review, key=lambda x: x[4]):
        print(f"  {row[4]:.3f}  {row[0]:<28} ({row[1][:24]:<24}) -> {row[2]:<30} ({row[3][:24]})")
    print('\n-- UNMATCHED --')
    for row in unmatched:
        print(f"  {row[0]:<28} {row[1][:26]:<26} {row[2]:>3}cr  [{row[3]}]")

if __name__ == '__main__':
    main()
