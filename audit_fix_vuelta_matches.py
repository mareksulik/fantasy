#!/usr/bin/env python3
"""Audit + fix Vuelta 2026 fuzzy matches against the official PCS startlist.

Fuzzy matching produces false positives on compound Spanish names, so every
rider with match_similarity < 1.0 (plus unmatched ones) is re-resolved
deterministically: same team on the PCS startlist + first surname + given-name
initial. Riders not on the startlist are re-checked against the scraped
top-1500 season ranking with the same strict rule; if still absent they are
left unmatched (0 pts) rather than wrongly matched.
"""
import csv
import importlib.util
import json
import re
import time
import unicodedata
from datetime import datetime

import requests
from bs4 import BeautifulSoup

import value_utils as V

HDR = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
       '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
BASE = 'https://www.procyclingstats.com'
WINS_CACHE = 'wins_vuelta_2026.csv'


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


wins_mod = load_module('wins_scraper', 'scrape_wins_2026.py')


def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


def norm(s):
    return re.sub(r'\s+', ' ', strip_accents(s or '').replace('-', ' ').upper()).strip()


def split_pcs_name(display):
    """PCS format 'SURNAME(S) Givenname' -> (surname_tokens, given). Surname
    tokens are the leading all-caps tokens of the original string."""
    toks = display.replace('-', ' ').split()
    surname = []
    given = []
    for t in toks:
        if not given and t == t.upper():
            surname.append(norm(t))
        else:
            given.append(t)
    return surname, ' '.join(given)


def split_fantasy_name(fname):
    """Fantasy format 'X. SURNAME1 SURNAME2' -> (initial, surname_tokens)."""
    toks = norm(fname).split()
    initial = toks[0].rstrip('.')
    return initial, toks[1:]


def team_tokens(t):
    drop = {'TEAM', 'PRO', 'CYCLING', 'THE'}
    return {w for w in re.split(r'[^A-Z0-9]+', norm(t)) if len(w) > 2 and w not in drop}


def name_matches(initial, f_surnames, pcs_display):
    p_sur, p_given = split_pcs_name(pcs_display)
    if not p_sur or not p_given:
        return False
    if norm(p_given)[0] != initial[0]:
        return False
    # first surnames must agree; extra fantasy surnames (2nd apellido) are OK
    n = min(len(p_sur), len(f_surnames))
    return n > 0 and p_sur[:n] == f_surnames[:n]


def fetch_startlist():
    r = requests.get(f'{BASE}/race/vuelta-a-espana/2026/startlist', headers=HDR, timeout=25)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')
    teams = []
    for li in soup.select('.startlist_v4 li'):
        tname_el = li.select_one('.team a') or li.find('a')
        riders = []
        for a in li.select('a'):
            href = a.get('href', '')
            if href.startswith('rider/'):
                riders.append({'display': a.get_text(' ', strip=True), 'slug': href[len('rider/'):]})
        if riders and tname_el:
            teams.append({'team': tname_el.get_text(' ', strip=True), 'riders': riders})
    return teams


def season_points_from_page(slug):
    """Current-season points from the rider's own PCS page (for riders outside
    the scraped top-1500)."""
    year = str(datetime.now().year)
    try:
        resp = requests.get(f'{BASE}/rider/{slug}', headers=HDR, timeout=25)
        soup = BeautifulSoup(resp.text, 'html.parser')
        for tbl in soup.find_all('table'):
            for tr in tbl.find_all('tr'):
                c = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                if len(c) >= 2 and c[0] == year:
                    return float(c[1]) if c[1].replace('.', '').isdigit() else 0.0
    except Exception as e:
        print(f'  ⚠️ page fetch failed for {slug}: {e}')
    return 0.0


def scrape_12m_map(limit=1500):
    out = {}
    print('Re-scraping 12m ranking for corrected riders...')
    for offset in range(0, limit, 100):
        params = {'p': 'me', 's': '', 'date': datetime.now().strftime('%Y-%m-%d'),
                  'nation': '', 'age': '', 'page': 'smallerorequal', 'team': '',
                  'teamlevel': '', 'offset': str(offset), 'filter': 'Filter'}
        url = f'{BASE}/rankings.php?' + '&'.join(f'{k}={v}' for k, v in params.items())
        try:
            resp = requests.get(url, headers=HDR, timeout=25)
            resp.raise_for_status()
        except requests.RequestException:
            break
        soup = BeautifulSoup(resp.text, 'html.parser')
        table = soup.find('table', class_='basic') or soup.find('table')
        rows = table.find_all('tr')[1:] if table else []
        if not rows:
            break
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 7:
                name = cols[4].get_text(' ', strip=True)
                pts = cols[6].text.strip()
                out[name] = float(pts) if pts.replace('.', '').isdigit() else 0.0
        time.sleep(1)
    return out


def main():
    with open('combined_vuelta_data.json', encoding='utf-8') as f:
        data = json.load(f)
    riders = data['riders']

    with open('pcs_vuelta_riders_data.csv', encoding='utf-8') as f:
        season = list(csv.DictReader(f))
    season_by_name = {norm(r['name']): r for r in season}

    startlist = fetch_startlist()
    n_starters = sum(len(t['riders']) for t in startlist)
    print(f'Startlist: {len(startlist)} teams, {n_starters} riders')

    suspects = [r for r in riders if (not r['pcs_match_found']) or r['match_similarity'] < 1.0]
    print(f'Auditing {len(suspects)} riders (fuzzy or unmatched)\n')

    corrections, confirmed, dropped, ambiguous = [], [], [], []
    for r in suspects:
        initial, f_surnames = split_fantasy_name(r['fantasy_name'])
        f_team = team_tokens(r['team'])

        # 1) same-team startlist candidates
        cands = []
        for t in startlist:
            if f_team & team_tokens(t['team']):
                cands += [c for c in t['riders'] if name_matches(initial, f_surnames, c['display'])]
        # 2) whole startlist
        if not cands:
            for t in startlist:
                cands += [c for c in t['riders'] if name_matches(initial, f_surnames, c['display'])]
        # 3) scraped top-1500 season ranking (non-starters in the fantasy pool)
        if not cands:
            cands = [{'display': s['name'], 'slug': s['rider_url'].rsplit('/', 1)[-1]}
                     for s in season if name_matches(initial, f_surnames, s['name'])]

        uniq = {c['slug']: c for c in cands}
        if len(uniq) > 1:
            ambiguous.append((r['fantasy_name'], [c['display'] for c in uniq.values()]))
            continue
        if not uniq:
            if r['pcs_match_found']:
                dropped.append((r['fantasy_name'], r['pcs_name']))
                r.update({'pcs_match_found': False, 'match_similarity': 0.0, 'pcs_name': None,
                          'pcs_rank': None, 'pcs_points_2025': 0, 'pcs_points_12m': 0,
                          'pcs_nationality': None, 'pcs_team': None, 'pcs_url': None})
            continue

        c = next(iter(uniq.values()))
        if r['pcs_match_found'] and norm(r['pcs_name'] or '') == norm(c['display']):
            confirmed.append((r['fantasy_name'], c['display']))
            r['match_similarity'] = 1.0
            continue
        corrections.append((r, c))

    print(f'Confirmed fuzzy matches: {len(confirmed)}')
    for f, p in confirmed:
        print(f'  ✓ {f} -> {p}')
    print(f'\nCorrections: {len(corrections)}')

    m12 = scrape_12m_map() if corrections else {}
    wins_cache = {}
    try:
        with open(WINS_CACHE, encoding='utf-8') as f:
            wins_cache = {row['pcs_name']: int(row['wins_2026']) for row in csv.DictReader(f)}
    except FileNotFoundError:
        pass

    for r, c in corrections:
        old = r['pcs_name'] if r['pcs_match_found'] else '(unmatched)'
        s = season_by_name.get(norm(c['display']))
        if s:
            pts = float(s['points'])
            rank = int(s['rank']) if str(s['rank']).isdigit() else None
            nat, url = s['nationality'], s['rider_url']
            display = s['name']
        else:
            pts = season_points_from_page(c['slug'])
            rank, nat = None, None
            url = f"{BASE}/rider/{c['slug']}"
            display = c['display']
            time.sleep(0.5)
        r.update({'pcs_match_found': True, 'match_similarity': 1.0, 'pcs_name': display,
                  'pcs_rank': rank, 'pcs_points_2025': pts,
                  'pcs_points_12m': m12.get(display, pts),
                  'pcs_nationality': nat, 'pcs_team': None, 'pcs_url': url})
        if display not in wins_cache:
            try:
                wins_cache[display] = wins_mod.wins_for(url)
                time.sleep(0.5)
            except Exception:
                wins_cache[display] = 0
        r['wins_2026'] = wins_cache.get(display, 0)
        print(f'  ✏️  {r["fantasy_name"]:<25} {old:<28} -> {display} ({pts} pts, {r["wins_2026"]} wins)')

    print(f'\nDropped wrong matches (no PCS record found): {len(dropped)}')
    for f, p in dropped:
        print(f'  ✗ {f} (was wrongly {p})')
    if ambiguous:
        print(f'\nAMBIGUOUS (manual decision needed): {ambiguous}')

    with open(WINS_CACHE, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['pcs_name', 'wins_2026'])
        for k, v in wins_cache.items():
            w.writerow([k, v])

    V.recompute_value(riders)
    data['integration_info']['matched_riders'] = sum(1 for r in riders if r['pcs_match_found'])
    data['integration_info']['last_update'] = datetime.now().isoformat()
    data['integration_info']['match_audit'] = 'startlist-verified ' + datetime.now().isoformat()
    with open('combined_vuelta_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    import pandas as pd
    pd.DataFrame(riders).to_csv('combined_vuelta_data.csv', index=False, encoding='utf-8')
    print(f"\nSaved. Matched {data['integration_info']['matched_riders']}/{len(riders)}")


if __name__ == '__main__':
    main()
