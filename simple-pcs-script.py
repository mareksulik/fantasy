#!/usr/bin/env python3
"""
Fantasy TdF Helper - PCS Data Integration
Integruje fantasy dáta s ProCyclingStats dátami pre lepší výber jazdcov
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
import csv
from datetime import datetime
from difflib import SequenceMatcher
import re

class FantasyPCSIntegrator:
    def __init__(self, fantasy_csv_path='all_tour_de_france_riders.csv'):
        self.base_url = "https://www.procyclingstats.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.fantasy_csv_path = fantasy_csv_path
        self.fantasy_riders = []
        self.pcs_riders = []
        self.integrated_data = []
        
    def load_fantasy_riders(self):
        """Načíta fantasy jazdcov z CSV súboru"""
        try:
            with open(self.fantasy_csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    self.fantasy_riders.append({
                        'fantasy_name': row['Meno jazdca'].strip(),
                        'team': row['Tím'].strip(),
                        'category': row['Kategória'].strip(),
                        'price': int(row['Cena']) if row['Cena'].isdigit() else 0
                    })
            print(f"Načítaných {len(self.fantasy_riders)} fantasy jazdcov")
            return True
        except Exception as e:
            print(f"Chyba pri načítavaní fantasy dát: {e}")
            return False
    
    def normalize_name(self, name):
        """Normalizuje meno jazdca pre lepší matching"""
        # Odstráni špeciálne znaky a upraví formát
        name = re.sub(r'[^\w\s]', '', name.upper())
        # Rozdelí meno na časti
        parts = name.split()
        if len(parts) >= 2:
            # Ak je prvé slovo skratka (1-2 znaky) - fantasy formát
            if len(parts[0]) <= 2:
                return f"{parts[0].replace('.', '')} {parts[-1]}"  # T. POGAČAR -> T POGAČAR
            else:
                # PCS formát - PRIEZVISKO Meno -> M PRIEZVISKO  
                return f"{parts[-1][0]} {parts[0]}"  # POGAČAR Tadej -> T POGAČAR
        return name
        
    def extract_surnames(self, name):
        """Extrahuje priezviská pre porovnanie"""
        name = re.sub(r'[^\w\s]', '', name.upper())
        parts = name.split()
        
        # Pre fantasy formát (T. POGAČAR)
        if len(parts) >= 2 and len(parts[0]) <= 2:
            return parts[-1]  # POGAČAR
        # Pre PCS formát (POGAČAR Tadej)  
        elif len(parts) >= 2:
            return parts[0]  # POGAČAR
        return name
    
    def similarity(self, name1, name2):
        """Vypočíta podobnosť medzi dvoma menami"""
        # Normalizované mená
        norm1 = self.normalize_name(name1)
        norm2 = self.normalize_name(name2)
        norm_similarity = SequenceMatcher(None, norm1, norm2).ratio()
        
        # Porovnanie priezvisk
        surname1 = self.extract_surnames(name1)
        surname2 = self.extract_surnames(name2)
        surname_similarity = SequenceMatcher(None, surname1, surname2).ratio()
        
        # Kombinované skóre (priezvisko má váhu 70%, celé meno 30%)
        combined_score = 0.7 * surname_similarity + 0.3 * norm_similarity
        
        return combined_score
    
    def normalize_team_name(self, team):
        """Normalizuje názov tímu pre lepší matching"""
        team = team.upper()
        # Odstráni štandardné prípony a prefixes
        team = re.sub(r'\s*(TEAM|CYCLING|PRO|DEVELOPMENT)\s*', ' ', team)
        team = re.sub(r'\s*(XRG|UAE|AG2R|B&B)\s*', ' ', team)
        team = re.sub(r'\s*-\s*', ' ', team)
        team = re.sub(r'\s+', ' ', team).strip()
        return team
    
    def team_similarity(self, team1, team2):
        """Vypočíta podobnosť tímov"""
        norm1 = self.normalize_team_name(team1)
        norm2 = self.normalize_team_name(team2)
        
        # Exact match po normalizácii
        if norm1 == norm2:
            return 1.0
            
        # Substring match
        if norm1 in norm2 or norm2 in norm1:
            return 0.8
            
        # Fuzzy similarity
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def find_pcs_match(self, fantasy_rider):
        """Nájde najlepší match v PCS dátach pre fantasy jazdca"""
        best_match = None
        best_similarity = 0.0
        
        for pcs_rider in self.pcs_riders:
            # Name similarity
            name_sim = self.similarity(fantasy_rider['fantasy_name'], pcs_rider['name'])
            
            # Team similarity
            team_sim = self.team_similarity(fantasy_rider['team'], pcs_rider.get('team', ''))
            
            # Combined score: 85% name + 15% team (meno je dôležitejšie)
            combined_similarity = 0.85 * name_sim + 0.15 * team_sim
            
            # Minimálna požiadavka na meno - musí byť aspoň 0.3
            if name_sim < 0.3:
                combined_similarity = 0
            
            # Malý bonus ak sa tím zhoduje (len ak je meno slušné)
            if team_sim > 0.8 and name_sim > 0.5:
                combined_similarity += 0.1
            
            if combined_similarity > best_similarity and combined_similarity > 0.4:
                best_similarity = combined_similarity
                best_match = pcs_rider
                
        return best_match, best_similarity
        
    def create_manual_mappings(self):
        """Vytvorí manuálne mapovanie pre problematické prípady"""
        return {
            # Fantasy name -> PCS search terms
            'T. POGAČAR': ['POGAČAR Tadej', 'POGACAR Tadej'],
            'J. VINGEGAARD HANSEN': ['VINGEGAARD Jonas', 'VINGEGAARD HANSEN Jonas'],
            'R. EVENEPOEL': ['EVENEPOEL Remco'],
            'P. ROGLIC': ['ROGLIČ Primož', 'ROGLIC Primoz'],
            'W. VAN AERT': ['VAN AERT Wout'],
            'M. VAN DER POEL': ['VAN DER POEL Mathieu'],
            'E. MAS NICOLAU': ['MAS Enric'],
            'C. RODRIGUEZ': ['RODRÍGUEZ Carlos', 'RODRIGUEZ Carlos'],
            'A. KRISTOFF': ['KRISTOFF Alexander'],
            'P. BAUHAUS': ['BAUHAUS Phil'],
            'P. SIVAKOV': ['SIVAKOV Pavel'],
            'A. LUTSENKO': ['LUTSENKO Alexey'],
            'L. PLAPP': ['PLAPP Luke'],
            'L. KÄMNA': ['KÄMNA Lennard'],
            'S. BISSEGGER': ['BISSEGGER Stefan'],
            'F. GROSSSCHARTNER': ['GROSSSCHARTNER Felix'],
            'O. VERGAERDE': ['VERGAERDE Otto'],
            'C. BOL': ['BOL Cees'],
            'A. WRIGHT': ['WRIGHT Alfred', 'WRIGHT Alex'],
            'C. RODRIGUEZ': ['RODRÍGUEZ Carlos', 'RODRIGUEZ Carlos'],
            'B. O\'CONNOR': ['O\'CONNOR Ben', 'OCONNOR Ben'],
            'M. MOHORIC': ['MOHORIČ Matej', 'MOHORIC Matej'],
            'A. DAINESE': ['DAINESE Alberto'],
            'A. KRISTOFF': ['KRISTOFF Alexander'],
            'P. BAUHAUS': ['BAUHAUS Phil'],
            'E. DUNBAR': ['DUNBAR Eddie'],
            'P. SIVAKOV': ['SIVAKOV Pavel'],
            'A. LUTSENKO': ['LUTSENKO Alexey'],
            'P. BITTNER': ['BITTNER Pavel'],
            'M. WOODS': ['WOODS Michael'],
            'I. IZAGIRRE INSAUSTI': ['IZAGIRRE Ion', 'IZAGUIRRE Ion'],
            'G. MARTIN GUYONNET': ['MARTIN Guillaume'],
            'L. VAN EETVELT': ['VAN EETVELT Lennert'],
            'A. LEKNESSUND': ['LEKNESSUND Andreas'],
            'S. BATTISTELLA': ['BATTISTELLA Samuele'],
            'B. ARMIRAIL': ['ARMIRAIL Bruno'],
            'V. CAMPENAERTS': ['CAMPENAERTS Victor'],
            'J. HAIG': ['HAIG Jack'],
            'T. TRÆEN': ['TRÆEN Tobias'],
            'C. HARPER': ['HARPER Chris'],
            'D. VAN POPPEL': ['VAN POPPEL Danny'],
            'S. EDVARDSEN-FREDHEIM': ['EDVARDSEN-FREDHEIM Søren'],
            'A. BAUDIN': ['BAUDIN Alex'],
            'I. SCHELLING': ['SCHELLING Ide'],
            'C. SWIFT': ['SWIFT Connor'],
            'Q. PACHER': ['PACHER Quentin'],
            'F. DOUBEY': ['DOUBEY Fabien'],
            'E. SEPULVEDA': ['SEPÚLVEDA Eduardo'],
            'T. VAN DER HOORN': ['VAN DER HOORN Taco'],
            'D. TOUZE': ['TOUZÉ Damien'],
            'L. ROTA': ['ROTA Lorenzo'],
            'L. REX': ['REX Laurenz'],
            'H. SWEENY': ['SWEENY Harrison'],
            'B. LEMMEN': ['LEMMEN Bart'],
            'L. MEZGEC': ['MEZGEC Luka'],
            'L. WARBASSE': ['WARBASSE Larry'],
            'K. BOUWMAN': ['BOUWMAN Koen'],
            'M. VAN DIJKE': ['VAN DIJKE Mick'],
            'A. LIVYNS': ['LIVYNS Arjen'],
            'B. SWIFT': ['SWIFT Ben'],
            'O. RIESEBEEK': ['RIESEBEEK Oscar'],
            'B. JUNGELS': ['JUNGELS Bob'],
            'G. WILSLY': ['WILSLY Georg'],
            'M. BURGAUDEAU': ['BURGAUDEAU Mathieu'],
            'N. MÄRKL': ['MÄRKL Niklas'],
            'J. LECERF': ['LECERF Julien'],
            'R. VAN SINTMAARTENSDIJK': ['VAN SINTMAARTENSDIJK Robbe'],
            'E. VERSTRYNGE': ['VERSTRYNGE Edward'],
            'S. FLYNN': ['FLYNN Sean'],
            'L. DURBRIDGE': ['DURBRIDGE Luke'],
            'M. LOUVEL': ['LOUVEL Mathis'],
            'J. DE BUYST': ['DE BUYST Jasper'],
            'C. BRAZ AFONSO': ['BRAZ AFONSO Cristian'],
            'R. FROIDEVAUX': ['FROIDEVAUX Romain'],
            'J. DRIZNERS': ['DRIZNERS Jarrad'],
            'C. BEULLENS': ['BEULLENS Cédric'],
            'N. EEKHOFF': ['EEKHOFF Nils'],
            'P. CÔTÉ': ['CÔTÉ Pierre-André'],
            'M. PAASSCHENS': ['PAASSCHENS Mike'],
            'A. DELAPLACE': ['DELAPLACE Anthony']
        }
    
    def find_pcs_match_advanced(self, fantasy_rider):
        """Rozšírené vyhľadanie s manuálnymi mapovaniami"""
        manual_mappings = self.create_manual_mappings()
        
        # Najprv skús manuálne mapovanie
        if fantasy_rider['fantasy_name'] in manual_mappings:
            best_match = None
            best_team_sim = 0
            
            for search_name in manual_mappings[fantasy_rider['fantasy_name']]:
                for pcs_rider in self.pcs_riders:
                    pcs_name = pcs_rider['name'].upper()
                    search_upper = search_name.upper()
                    
                    # Bidirectional string matching
                    name_match = (search_upper in pcs_name or 
                                pcs_name in search_upper or
                                self.similarity(search_name, pcs_rider['name']) > 0.8)
                    
                    if name_match:
                        team_sim = self.team_similarity(fantasy_rider['team'], pcs_rider.get('team', ''))
                        
                        # Ak sa našlo meno, ulož najlepší team match
                        if team_sim > best_team_sim:
                            best_match = pcs_rider
                            best_team_sim = team_sim
                            
                        # Ak je tím dobrý, vráť hneď
                        if team_sim > 0.3:
                            print(f"✅ Manuálne mapovanie: {fantasy_rider['fantasy_name']} -> {pcs_rider['name']} (team: {team_sim:.2f})")
                            return pcs_rider, 1.0
            
            # Ak sa našlo meno ale tím je slabý, stále vráť najlepší match
            if best_match:
                print(f"⚠️  Manuálne mapovanie: {fantasy_rider['fantasy_name']} -> {best_match['name']} (slabý team match: {best_team_sim:.2f})")
                return best_match, 0.9
            
            # Ak sa nenašlo ani meno
            print(f"❌ Manuálne mapovanie pre {fantasy_rider['fantasy_name']} nenašlo žiadny PCS profil")
            return None, 0.0
        
        # Ak manuálne mapovanie nefunguje, použij štandardný algoritmus
        return self.find_pcs_match(fantasy_rider)
        
    def get_season_ranking_page(self, offset=0):
        """Získa stránku s rankingom"""
        url = f"{self.base_url}/rankings/me/season-individual"
        if offset > 0:
            url += f"?offset={offset}"
            
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Chyba pri získavaní stránky: {e}")
            return None
            
    def parse_ranking_table(self, html):
        """Spracuje HTML a extrahuje dáta jazdcov"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Nájdi hlavnú tabuľku s rankingom
        table = soup.find('table', class_='basic')
        if not table:
            table = soup.find('table')  # Záložná možnosť
            
        if not table:
            print("Tabuľka s rankingom nebola nájdená")
            return []
            
        riders_on_page = []
        rows = table.find_all('tr')[1:]  # Preskočiť hlavičku
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 6:
                try:
                    # Extrakcia dát z buniek (správne indexy)
                    rank = cols[0].text.strip()
                    
                    # Meno jazdca a odkaz (4. stĺpec)
                    rider_link = cols[3].find('a')
                    rider_name = rider_link.text.strip() if rider_link else cols[3].text.strip()
                    rider_url = rider_link['href'] if rider_link else ""
                    
                    # Tím (5. stĺpec)
                    team_link = cols[4].find('a')
                    team = team_link.text.strip() if team_link else cols[4].text.strip()
                    
                    # Body (6. stĺpec)
                    points = cols[5].text.strip()
                    
                    # Národnosť (ak je dostupná)
                    nationality = ""
                    flag = cols[3].find('span', class_='flag')
                    if flag and 'class' in flag.attrs:
                        # Extrakcia kódu krajiny z CSS triedy
                        for cls in flag['class']:
                            if cls != 'flag' and len(cls) == 2:
                                nationality = cls.upper()
                                break
                    
                    rider_data = {
                        'rank': int(rank) if rank.isdigit() else rank,
                        'name': rider_name,
                        'nationality': nationality,
                        'team': team,
                        'points': float(points) if points.replace('.', '').isdigit() else points,
                        'rider_url': f"{self.base_url}/{rider_url.lstrip('/')}" if rider_url else ""
                    }
                    
                    riders_on_page.append(rider_data)
                    
                except Exception as e:
                    print(f"Chyba pri spracovaní riadku: {e}")
                    continue
                    
        return riders_on_page
        
    def scrape_pcs_data(self, limit=1000):
        """Získa PCS dáta pre jazdcov"""
        print(f"Začínam sťahovanie top {limit} jazdcov z ProCyclingStats...")
        
        offset = 0
        page_size = 100  # Predpokladaný počet jazdcov na stránku
        
        while len(self.pcs_riders) < limit:
            print(f"\nSťahujem jazdcov {offset + 1} - {offset + page_size}...")
            
            # Získaj HTML stránky
            html = self.get_season_ranking_page(offset)
            if not html:
                break
                
            # Spracuj dáta
            riders_on_page = self.parse_ranking_table(html)
            
            if not riders_on_page:
                print("Žiadni ďalší jazdci neboli nájdení")
                break
                
            self.pcs_riders.extend(riders_on_page)
            print(f"Získaných {len(riders_on_page)} jazdcov (celkovo: {len(self.pcs_riders)})")
            
            # Ak máme dosť jazdcov, skonči
            if len(self.pcs_riders) >= limit:
                self.pcs_riders = self.pcs_riders[:limit]
                break
                
            # Počkaj pred ďalším requestom
            time.sleep(1)
            offset += page_size
            
        print(f"\nCelkovo získaných jazdcov: {len(self.pcs_riders)}")
        return self.pcs_riders
        
    def integrate_data(self):
        """Integruje fantasy a PCS dáta"""
        print("\nIntegruje fantasy a PCS dáta...")
        
        matched_count = 0
        unmatched_riders = []
        
        for fantasy_rider in self.fantasy_riders:
            pcs_match, similarity = self.find_pcs_match_advanced(fantasy_rider)
            
            integrated_rider = {
                'fantasy_name': fantasy_rider['fantasy_name'],
                'team': fantasy_rider['team'],
                'category': fantasy_rider['category'],
                'price': fantasy_rider['price'],
                'pcs_match_found': pcs_match is not None,
                'match_similarity': similarity if pcs_match else 0.0
            }
            
            if pcs_match:
                integrated_rider.update({
                    'pcs_name': pcs_match['name'],
                    'pcs_rank': pcs_match['rank'],
                    'pcs_points_2025': pcs_match['points'],
                    'pcs_nationality': pcs_match['nationality'],
                    'pcs_team': pcs_match['team'],
                    'pcs_url': pcs_match['rider_url']
                })
                matched_count += 1
            else:
                integrated_rider.update({
                    'pcs_name': None,
                    'pcs_rank': None,
                    'pcs_points_2025': 0,
                    'pcs_nationality': None,
                    'pcs_team': None,
                    'pcs_url': None
                })
                unmatched_riders.append(fantasy_rider['fantasy_name'])
            
            self.integrated_data.append(integrated_rider)
        
        print(f"Úspešne namatchovaných: {matched_count}/{len(self.fantasy_riders)} jazdcov")
        if unmatched_riders:
            print(f"\nNENAMATCHOVANÍ JAZDCI ({len(unmatched_riders)}):")
            for rider_name in unmatched_riders:
                fantasy_rider = next(r for r in self.fantasy_riders if r['fantasy_name'] == rider_name)
                print(f"  {rider_name} ({fantasy_rider['team']}) - {fantasy_rider['category']}")
        
        return self.integrated_data
        
    def save_integrated_data(self, csv_filename='combined_riders_data.csv', json_filename='combined_riders_data.json'):
        """Uloží integrované dáta do CSV a JSON súborov"""
        if not self.integrated_data:
            print("Žiadne integrované dáta na uloženie")
            return
            
        # CSV export
        df = pd.DataFrame(self.integrated_data)
        df.to_csv(csv_filename, index=False, encoding='utf-8')
        print(f"Integrované dáta uložené do {csv_filename}")
        
        # JSON export
        data = {
            'integration_info': {
                'type': 'Fantasy TdF + PCS Data Integration',
                'fantasy_riders_count': len(self.fantasy_riders),
                'pcs_riders_count': len(self.pcs_riders),
                'matched_riders': len([r for r in self.integrated_data if r['pcs_match_found']]),
                'last_update': datetime.now().isoformat()
            },
            'riders': self.integrated_data
        }
        
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Integrované dáta uložené do {json_filename}")
        
    def calculate_value_metrics(self):
        """Vypočíta value metriky pre fantasy"""
        for rider in self.integrated_data:
            if rider['pcs_match_found'] and rider['price'] > 0:
                # Points per credit ratio
                rider['points_per_credit'] = rider['pcs_points_2025'] / rider['price']
                
                # Value category
                if rider['points_per_credit'] > 50:
                    rider['value_category'] = 'Excellent'
                elif rider['points_per_credit'] > 30:
                    rider['value_category'] = 'Good'
                elif rider['points_per_credit'] > 15:
                    rider['value_category'] = 'Average'
                else:
                    rider['value_category'] = 'Poor'
            else:
                rider['points_per_credit'] = 0
                rider['value_category'] = 'Unknown'
        
    def print_integration_summary(self, n=10):
        """Vypíše súhrn integrácie"""
        matched_riders = [r for r in self.integrated_data if r['pcs_match_found']]
        
        print(f"\n=== FANTASY TDF HELPER - INTEGRATION SUMMARY ===")
        print(f"Fantasy jazdci: {len(self.fantasy_riders)}")
        print(f"PCS jazdci: {len(self.pcs_riders)}")
        print(f"Úspešne namatchovaných: {len(matched_riders)}")
        print(f"Match rate: {len(matched_riders)/len(self.fantasy_riders)*100:.1f}%")
        
        # Top value picks
        value_riders = sorted(matched_riders, key=lambda x: x['points_per_credit'], reverse=True)[:n]
        
        print(f"\nTop {n} value picks (points/credit):")
        print("-" * 100)
        print(f"{'Fantasy Meno':<20} {'Kategória':<12} {'Cena':<5} {'PCS Body':<8} {'P/C':<6} {'Value':<8}")
        print("-" * 100)
        
        for rider in value_riders:
            print(f"{rider['fantasy_name']:<20} {rider['category']:<12} {rider['price']:<5} "
                  f"{rider['pcs_points_2025']:<8.0f} {rider['points_per_credit']:<6.1f} {rider['value_category']:<8}")
                  
    def save_pcs_data(self, csv_filename='pcs_riders_data.csv'):
        """Uloží PCS dáta do CSV súboru"""
        if not self.pcs_riders:
            print("Žiadne PCS dáta na uloženie")
            return
            
        df = pd.DataFrame(self.pcs_riders)
        df.to_csv(csv_filename, index=False, encoding='utf-8')
        print(f"PCS dáta uložené do {csv_filename}")

    def run_integration(self):
        """Spustí celý proces integrácie"""
        print("=== FANTASY TDF HELPER - PCS INTEGRATION ===\n")
        
        # 1. Načítaj fantasy dáta
        if not self.load_fantasy_riders():
            return False
            
        # 2. Získaj PCS dáta  
        self.scrape_pcs_data(limit=1500)  # Ešte viac dát pre lepší matching TdF jazdcov
        
        # 2.1. Ulož PCS dáta do CSV
        self.save_pcs_data()
        
        # 3. Integruj dáta
        self.integrate_data()
        
        # 4. Vypočítaj value metriky
        self.calculate_value_metrics()
        
        # 5. Ulož výsledky
        self.save_integrated_data()
        
        # 6. Zobraz súhrn
        self.print_integration_summary(15)
        
        return True


# Alternatívna metóda použitím procyclingstats knižnice
def use_procyclingstats_library():
    """Použitie oficiálnej procyclingstats knižnice"""
    try:
        from procyclingstats import Ranking
        
        print("Používam procyclingstats knižnicu...")
        ranking = Ranking("rankings/me/season-individual")
        
        # Získaj ranking
        riders_data = ranking.individual_ranking()
        
        # Konvertuj na DataFrame
        df = pd.DataFrame(riders_data[:500])
        
        # Ulož do CSV
        df.to_csv('pcs_top500_2025_api.csv', index=False, encoding='utf-8')
        print("Dáta úspešne uložené pomocou API")
        
        return df
        
    except ImportError:
        print("Knižnica procyclingstats nie je nainštalovaná")
        print("Nainštalujte ju pomocou: pip install procyclingstats")
        return None
    except Exception as e:
        print(f"Chyba pri používaní API: {e}")
        return None


def main():
    """Hlavná funkcia"""
    print("Fantasy TdF Helper - PCS Data Integration")
    print("=" * 50)
    
    # Inicializuj integrátor
    integrator = FantasyPCSIntegrator()
    
    # Spusti integráciu
    success = integrator.run_integration()
    
    if success:
        print("\n✅ Integrácia úspešne dokončená!")
        print("📄 Výsledky uložené v combined_riders_data.csv a combined_riders_data.json")
        print("🚀 Môžete teraz spustiť web aplikáciu!")
    else:
        print("\n❌ Integrácia neúspešná")


if __name__ == "__main__":
    main()