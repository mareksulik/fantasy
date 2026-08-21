#!/usr/bin/env python3
"""Scrape each rider's number of 2026 victories from their PCS season page.
Uses the stored pcs_url so slugs are always correct. Caches to wins_2026.csv."""
import json, csv, time, urllib.request
from bs4 import BeautifulSoup

HDR = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
       'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'}


def wins_for(url):
    page = urllib.request.urlopen(urllib.request.Request(url.rstrip('/') + '/2026', headers=HDR), timeout=25)
    soup = BeautifulSoup(page.read().decode('utf-8', 'ignore'), 'html.parser')
    tbl = soup.find('table')
    if not tbl:
        return 0
    rows = tbl.find_all('tr')
    head = [c.get_text(strip=True).lower() for c in rows[0].find_all(['th', 'td'])]
    ri = next((i for i, h in enumerate(head) if 'result' in h), 1)
    wins = 0
    for tr in rows[1:]:
        tds = tr.find_all('td')
        if len(tds) <= ri or tds[ri].get_text(strip=True) != '1':
            continue
        # PCS counts stage/one-day/GC victories as wins, but NOT secondary
        # classifications (points/mountains/youth), whose rows also show "1".
        label = tr.get_text(' ', strip=True).lower()
        if 'classification' in label and 'general classification' not in label:
            continue
        wins += 1
    return wins


def main():
    riders = json.load(open('combined_riders_data.json', encoding='utf-8'))['riders']
    out = {}
    for i, r in enumerate(riders, 1):
        url = r.get('pcs_url')
        name = r.get('pcs_name')
        if not (url and name):
            continue
        try:
            out[name] = wins_for(url)
        except Exception as e:
            out[name] = 0
            print(f"  [{i}] {name}: ERR {e}")
        if i % 25 == 0:
            print(f"  ...{i}/{len(riders)} done")
        time.sleep(0.5)
    with open('wins_2026.csv', 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['pcs_name', 'wins_2026'])
        for k, v in out.items():
            w.writerow([k, v])
    print(f"DONE: {len(out)} riders -> wins_2026.csv | total wins {sum(out.values())}")


if __name__ == '__main__':
    main()
