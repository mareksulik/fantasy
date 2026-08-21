#!/usr/bin/env python3
"""Vuelta 2026 integration runner.

Reuses the TdF 2026 pipeline (FantasyPCSIntegrator in simple-pcs-script.py) on
all_vuelta_riders.csv and writes combined_vuelta_data.{json,csv}. Steps:
  1. PCS season + 12m ranking scrape, name matching (manual map + fuzzy)
  2. 2026 win counts for the Vuelta roster (cached in wins_vuelta_2026.csv)
  3. value model from value_utils (same as TdF)
"""
import csv
import importlib.util
import json
import sys
import time
from datetime import datetime


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


pcs = load_module('pcs_integrator', 'simple-pcs-script.py')
wins_mod = load_module('wins_scraper', 'scrape_wins_2026.py')

WINS_CACHE = 'wins_vuelta_2026.csv'


def scrape_vuelta_wins(riders, use_cache=('--cached-wins' in sys.argv)):
    """Per-rider 2026 win counts via each rider's PCS page (wins_for from
    scrape_wins_2026.py). Cached so re-runs skip ~180 requests."""
    if use_cache:
        try:
            with open(WINS_CACHE, encoding='utf-8') as f:
                return {row['pcs_name']: int(row['wins_2026']) for row in csv.DictReader(f)}
        except FileNotFoundError:
            print(f"⚠️  {WINS_CACHE} not found, scraping fresh")
    out = {}
    todo = [r for r in riders if r.get('pcs_url') and r.get('pcs_name')]
    for i, r in enumerate(todo, 1):
        try:
            out[r['pcs_name']] = wins_mod.wins_for(r['pcs_url'])
        except Exception as e:
            out[r['pcs_name']] = 0
            print(f"  [{i}/{len(todo)}] {r['pcs_name']}: ERR {e}")
        if i % 25 == 0:
            print(f"  wins {i}/{len(todo)}")
        time.sleep(0.6)
    with open(WINS_CACHE, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['pcs_name', 'wins_2026'])
        for k, v in out.items():
            w.writerow([k, v])
    print(f"Wins cached: {len(out)} riders -> {WINS_CACHE} | total wins {sum(out.values())}")
    return out


def main():
    integ = pcs.FantasyPCSIntegrator(fantasy_csv_path='all_vuelta_riders.csv')
    if not integ.load_fantasy_riders():
        sys.exit(1)

    integ.scrape_pcs_data(limit=1500)
    integ.save_pcs_data(csv_filename='pcs_vuelta_riders_data.csv')
    integ.scrape_pcs_12m(limit=1500)
    integ.integrate_data()
    integ.apply_page_overrides()

    wins = scrape_vuelta_wins(integ.integrated_data)
    for r in integ.integrated_data:
        r['wins_2026'] = wins.get(r.get('pcs_name') or '', 0)

    integ.calculate_value_metrics()
    integ.save_integrated_data(csv_filename='combined_vuelta_data.csv',
                               json_filename='combined_vuelta_data.json')

    # Patch integration_info for the Vuelta dataset (save_integrated_data labels it TdF)
    with open('combined_vuelta_data.json', encoding='utf-8') as f:
        data = json.load(f)
    data['integration_info']['type'] = 'Fantasy Vuelta + PCS Data Integration'
    data['integration_info']['race_type'] = 'vuelta'
    data['integration_info']['edition'] = 'Vuelta a España 2026'
    data['integration_info']['source_roster'] = 'all_vuelta_riders.csv'
    data['integration_info']['last_update'] = datetime.now().isoformat()
    with open('combined_vuelta_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    integ.print_integration_summary(15)

    # Audit trail: list fuzzy (non-manual) matches for manual verification
    fuzzy = [r for r in data['riders']
             if r['pcs_match_found'] and 0 < r['match_similarity'] < 1.0]
    print(f"\n=== FUZZY MATCHES TO AUDIT ({len(fuzzy)}) ===")
    for r in sorted(fuzzy, key=lambda x: x['match_similarity']):
        print(f"  {r['match_similarity']:.2f}  {r['fantasy_name']:<25} -> {r['pcs_name']:<30} ({r['team']} / {r['pcs_team']})")
    unmatched = [r for r in data['riders'] if not r['pcs_match_found']]
    print(f"\n=== UNMATCHED ({len(unmatched)}) ===")
    for r in unmatched:
        print(f"  {r['fantasy_name']} ({r['team']}, {r['category']})")


if __name__ == '__main__':
    main()
