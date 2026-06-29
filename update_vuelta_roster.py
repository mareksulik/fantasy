#!/usr/bin/env python3
"""
Update Vuelta a España 2025 Roster - Based on TdF approach

This script updates the combined_vuelta_data.json file to include only the
final 183 riders from all_vuelta_riders.csv, using the same approach as update_tdf_roster.py
"""

import json
import csv
from datetime import datetime
from difflib import SequenceMatcher

def normalize_name_for_matching(name):
    """Normalize names for better matching"""
    import re
    name = re.sub(r'[^\w\s]', '', name.upper().strip())
    # Remove extra whitespace
    name = ' '.join(name.split())
    return name

def find_rider_match(vuelta_name, existing_riders, debug=False):
    """Find matching rider in existing combined data"""
    vuelta_normalized = normalize_name_for_matching(vuelta_name)
    
    best_match = None
    best_score = 0
    
    for rider in existing_riders:
        fantasy_normalized = normalize_name_for_matching(rider['fantasy_name'])
        
        # Direct match
        if fantasy_normalized == vuelta_normalized:
            if debug:
                print(f"  Direct match: {vuelta_name} -> {rider['fantasy_name']}")
            return rider
        
        # Similarity match
        score = SequenceMatcher(None, vuelta_normalized, fantasy_normalized).ratio()
        if score > best_score and score > 0.8:  # High threshold
            best_score = score
            best_match = rider
    
    if best_match and debug:
        print(f"  Similarity match: {vuelta_name} -> {best_match['fantasy_name']} (score: {best_score:.2f})")
    
    return best_match

def load_vuelta_riders():
    """Load Vuelta riders from CSV file"""
    vuelta_riders = []
    try:
        with open('all_vuelta_riders.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                vuelta_riders.append({
                    'name': row['Meno jazdca'].strip().strip('"'),
                    'team': row['Tím'].strip().strip('"'),
                    'category': row['Kategória'].strip().strip('"'),
                    'price': int(row['Cena'].strip().strip('"'))
                })
    except Exception as e:
        print(f"❌ Error loading Vuelta riders: {e}")
        return []
    
    print(f"✓ Loaded {len(vuelta_riders)} Vuelta riders")
    return vuelta_riders

def update_vuelta_roster():
    """Update combined_vuelta_data.json with Vuelta riders from existing data"""
    
    # Load Vuelta riders list
    vuelta_riders = load_vuelta_riders()
    if not vuelta_riders:
        return 0
    
    print(f"Processing {len(vuelta_riders)} riders for Vuelta a España 2025...")
    
    # Load existing combined data (created by simple-pcs-script.py)
    try:
        with open('combined_riders_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading combined_riders_data.json: {e}")
        print("First run: python simple-pcs-script.py")
        return 0
    
    existing_riders = data['riders']
    print(f"✓ Loaded {len(existing_riders)} existing riders from combined data\n")
    
    # Find matches and create new rider list
    new_riders = []
    unmatched_riders = []
    team_updates = 0
    
    for i, vuelta_rider in enumerate(vuelta_riders, 1):
        rider_name = vuelta_rider['name']
        team_name = vuelta_rider['team']
        
        print(f"[{i:3d}/183] Processing {rider_name:<30}", end=' ')
        
        match = find_rider_match(rider_name, existing_riders, debug=False)
        if match:
            # Update team name if different
            if match['team'] != team_name:
                print(f"(team update: {match['team'][:20]}... -> {team_name[:20]}...)")
                match['team'] = team_name
                team_updates += 1
            else:
                print("✓")
            
            # Update price and category from Vuelta data
            match['price'] = vuelta_rider['price']
            match['category'] = vuelta_rider['category']
            
            # Recalculate points per credit
            if match.get('pcs_points_2025', 0) > 0 and vuelta_rider['price'] > 0:
                match['points_per_credit'] = match['pcs_points_2025'] / vuelta_rider['price']
                
                # Update value category
                ppc = match['points_per_credit']
                if ppc > 50:
                    match['value_category'] = 'Excellent'
                elif ppc > 35:
                    match['value_category'] = 'Great'
                elif ppc > 20:
                    match['value_category'] = 'Good'
                elif ppc > 10:
                    match['value_category'] = 'Average'
                else:
                    match['value_category'] = 'Poor'
            
            new_riders.append(match)
        else:
            unmatched_riders.append(vuelta_rider)
            print("❌ NO MATCH")
    
    print(f"\n📊 MATCHING RESULTS:")
    print(f"   Matched: {len(new_riders)} riders")
    print(f"   Unmatched: {len(unmatched_riders)} riders") 
    print(f"   Team updates: {team_updates}")
    
    # Show unmatched riders for debugging
    if unmatched_riders:
        print(f"\n❌ UNMATCHED RIDERS ({len(unmatched_riders)}):")
        for rider in unmatched_riders:
            print(f"   - {rider['name']} ({rider['team']}) - {rider['category']}")
    
    # Create Vuelta data structure
    vuelta_data = {
        'integration_info': {
            'type': 'Fantasy Vuelta + PCS Data Integration',
            'fantasy_riders_count': len(vuelta_riders),
            'pcs_riders_count': len(existing_riders),
            'matched_riders': len(new_riders),
            'match_rate': f"{(len(new_riders)/len(vuelta_riders)*100):.1f}%",
            'last_update': datetime.now().isoformat(),
            'race_type': 'vuelta',
            'notes': f'Vuelta a España 2025 roster with {len(new_riders)} riders from combined data'
        },
        'riders': new_riders
    }
    
    # Save updated data
    with open('combined_vuelta_data.json', 'w', encoding='utf-8') as f:
        json.dump(vuelta_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Updated combined_vuelta_data.json with {len(new_riders)} riders")
    
    # Print summary by team
    team_counts = {}
    for rider in new_riders:
        team = rider['team']
        team_counts[team] = team_counts.get(team, 0) + 1
    
    print(f"\nRiders by team ({len(team_counts)} teams):")
    for team, count in sorted(team_counts.items()):
        print(f"  {team}: {count} riders")
    
    # Final statistics
    match_rate = (len(new_riders)/len(vuelta_riders))*100
    print(f"\n📈 FINAL STATISTICS:")
    print(f"  Total Vuelta riders: {len(vuelta_riders)}")
    print(f"  Successfully matched: {len(new_riders)}")
    print(f"  Match rate: {match_rate:.1f}%")
    
    if match_rate >= 99.0:
        print(f"\n🎉 SUCCESS! Achieved {match_rate:.1f}% match rate for Vuelta riders!")
    else:
        print(f"\n⚠️  Current match rate: {match_rate:.1f}%")
        print("   Some riders may need manual mapping")
    
    return len(new_riders)

if __name__ == "__main__":
    print("🚀 VUELTA A ESPAÑA 2025 - ROSTER UPDATE")
    print("=" * 50)
    final_count = update_vuelta_roster()
    
    if final_count > 0:
        print(f"\n✅ Process completed successfully!")
        print(f"   Vuelta data saved in combined_vuelta_data.json")
        print(f"   Ready for Flask application with race=vuelta parameter")
    else:
        print(f"\n❌ Process failed. Check error messages above.")