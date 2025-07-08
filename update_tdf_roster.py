#!/usr/bin/env python3
"""
Update TdF 2025 Roster - Consolidated Script

This script updates the combined_riders_data.json file to include only the
final 184 riders who are starting in Tour de France 2025.

It combines functionality from multiple update scripts to ensure all riders
are properly matched and included.
"""

import json
import re
from datetime import datetime

# Manual list of all 183 riders from TdF 2025 startlist
FINAL_RIDERS = [
    # UAE Team Emirates - XRG (8 riders)
    ("POGAČAR Tadej", "UAE Team Emirates - XRG"),
    ("ALMEIDA João", "UAE Team Emirates - XRG"),
    ("NARVÁEZ Jhonatan", "UAE Team Emirates - XRG"),
    ("POLITT Nils", "UAE Team Emirates - XRG"),
    ("SIVAKOV Pavel", "UAE Team Emirates - XRG"),
    ("SOLER Marc", "UAE Team Emirates - XRG"),
    ("WELLENS Tim", "UAE Team Emirates - XRG"),
    ("YATES Adam", "UAE Team Emirates - XRG"),
    
    # Team Visma | Lease a Bike (8 riders)
    ("VINGEGAARD Jonas", "Team Visma | Lease a Bike"),
    ("AFFINI Edoardo", "Team Visma | Lease a Bike"),
    ("BENOOT Tiesj", "Team Visma | Lease a Bike"),
    ("CAMPENAERTS Victor", "Team Visma | Lease a Bike"),
    ("JORGENSON Matteo", "Team Visma | Lease a Bike"),
    ("KUSS Sepp", "Team Visma | Lease a Bike"),
    ("VAN AERT Wout", "Team Visma | Lease a Bike"),
    ("YATES Simon", "Team Visma | Lease a Bike"),
    
    # Soudal Quick-Step (8 riders)
    ("EVENEPOEL Remco", "Soudal Quick-Step"),
    ("CATTANEO Mattia", "Soudal Quick-Step"),
    ("EENKHOORN Pascal", "Soudal Quick-Step"),
    ("MERLIER Tim", "Soudal Quick-Step"),
    ("PARET-PEINTRE Valentin", "Soudal Quick-Step"),
    ("SCHACHMANN Maximilian", "Soudal Quick-Step"),
    ("VAN LERBERGHE Bert", "Soudal Quick-Step"),
    ("VAN WILDER Ilan", "Soudal Quick-Step"),
    
    # EF Education - EasyPost (8 riders)
    ("SWEENY Harry", "EF Education - EasyPost"),
    ("POWLESS Neilson", "EF Education - EasyPost"),
    ("HEALY Ben", "EF Education - EasyPost"),
    ("ASGREEN Kasper", "EF Education - EasyPost"),
    ("VAN DEN BERG Marijn", "EF Education - EasyPost"),
    ("BAUDIN Alex", "EF Education - EasyPost"),
    ("VALGREN Michael", "EF Education - EasyPost"),
    ("ALBANESE Vincenzo", "EF Education - EasyPost"),
    
    # Decathlon AG2R La Mondiale Team (8 riders)
    ("ARMIRAIL Bruno", "Decathlon AG2R La Mondiale Team"),
    ("BISSEGGER Stefan", "Decathlon AG2R La Mondiale Team"),
    ("BERTHET Clément", "Decathlon AG2R La Mondiale Team"),
    ("GALL Felix", "Decathlon AG2R La Mondiale Team"),
    ("NAESEN Oliver", "Decathlon AG2R La Mondiale Team"),
    ("PARET-PEINTRE Aurélien", "Decathlon AG2R La Mondiale Team"),
    ("SCOTSON Callum", "Decathlon AG2R La Mondiale Team"),
    ("TRONCHON Bastien", "Decathlon AG2R La Mondiale Team"),
    
    # Red Bull - BORA - hansgrohe (8 riders)
    ("ROGLIČ Primož", "Red Bull - BORA - hansgrohe"),
    ("LIPOWITZ Florian", "Red Bull - BORA - hansgrohe"),
    ("VLASOV Aleksandr", "Red Bull - BORA - hansgrohe"),
    ("PITHIE Laurence", "Red Bull - BORA - hansgrohe"),
    ("VAN DIJKE Mick", "Red Bull - BORA - hansgrohe"),
    ("MOSCON Gianni", "Red Bull - BORA - hansgrohe"),
    ("VAN POPPEL Danny", "Red Bull - BORA - hansgrohe"),
    ("MEEUS Jordi", "Red Bull - BORA - hansgrohe"),
    
    # Cofidis (8 riders)
    ("ARANBURU Alex", "Cofidis"),
    ("BUCHMANN Emanuel", "Cofidis"),
    ("COQUARD Bryan", "Cofidis"),
    ("IZAGIRRE Ion", "Cofidis"),
    ("RENARD Alexis", "Cofidis"),
    ("THOMAS Benjamin", "Cofidis"),
    ("TOUZÉ Damien", "Cofidis"),
    ("TEUNS Dylan", "Cofidis"),
    
    # Alpecin - Deceuninck (8 riders)
    ("VAN DER POEL Mathieu", "Alpecin - Deceuninck"),
    ("PHILIPSEN Jasper", "Alpecin - Deceuninck"),
    ("GROVES Kaden", "Alpecin - Deceuninck"),
    ("RICKAERT Jonas", "Alpecin - Deceuninck"),
    ("VERSTRYNGE Emiel", "Alpecin - Deceuninck"),
    ("MEURISSE Xandro", "Alpecin - Deceuninck"),
    ("DILLIER Silvan", "Alpecin - Deceuninck"),
    ("VERMEERSCH Gianni", "Alpecin - Deceuninck"),
    
    # Arkéa - B&B Hotels (8 riders)
    ("GARCÍA PIERNA Raúl", "Arkéa - B&B Hotels"),
    ("DÉMARE Arnaud", "Arkéa - B&B Hotels"),
    ("CAPIOT Amaury", "Arkéa - B&B Hotels"),
    ("VAUQUELIN Kévin", "Arkéa - B&B Hotels"),
    ("RODRÍGUEZ Cristián", "Arkéa - B&B Hotels"),
    ("COSTIOU Ewen", "Arkéa - B&B Hotels"),
    ("LE BERRE Mathis", "Arkéa - B&B Hotels"),
    ("VENTURINI Clément", "Arkéa - B&B Hotels"),
    
    # INEOS Grenadiers (8 riders)
    ("RODRÍGUEZ Carlos", "INEOS Grenadiers"),
    ("GANNA Filippo", "INEOS Grenadiers"),
    ("THOMAS Geraint", "INEOS Grenadiers"),
    ("ARENSMAN Thymen", "INEOS Grenadiers"),
    ("FOSS Tobias", "INEOS Grenadiers"),
    ("LAURANCE Axel", "INEOS Grenadiers"),
    ("SWIFT Connor", "INEOS Grenadiers"),
    ("WATSON Samuel", "INEOS Grenadiers"),
    
    # Intermarché - Wanty (8 riders)
    ("GIRMAY Biniam", "Intermarché - Wanty"),
    ("PAGE Hugo", "Intermarché - Wanty"),
    ("REX Laurenz", "Intermarché - Wanty"),
    ("ZIMMERMANN Georg", "Intermarché - Wanty"),
    ("BARRÉ Louis", "Intermarché - Wanty"),
    ("BRAET Vito", "Intermarché - Wanty"),
    ("RUTSCH Jonas", "Intermarché - Wanty"),
    ("VAN SINTMAARTENSDIJK Roel", "Intermarché - Wanty"),
    
    # Lidl - Trek (8 riders)
    ("THEUNS Edward", "Lidl - Trek"),
    ("NYS Thibau", "Lidl - Trek"),
    ("STUYVEN Jasper", "Lidl - Trek"),
    ("CONSONNI Simone", "Lidl - Trek"),
    ("MILAN Jonathan", "Lidl - Trek"),
    ("SKJELMOSE Mattias", "Lidl - Trek"),
    ("SKUJIŅŠ Toms", "Lidl - Trek"),
    ("SIMMONS Quinn", "Lidl - Trek"),
    
    # Groupama - FDJ (8 riders)
    ("ASKEY Lewis", "Groupama - FDJ"),
    ("BARTHE Cyril", "Groupama - FDJ"),
    ("GRÉGOIRE Romain", "Groupama - FDJ"),
    ("MADOUAS Valentin", "Groupama - FDJ"),
    ("MARTIN Guillaume", "Groupama - FDJ"),
    ("PACHER Quentin", "Groupama - FDJ"),
    ("PENHOËT Paul", "Groupama - FDJ"),
    ("RUSSO Clément", "Groupama - FDJ"),
    
    # Movistar Team (8 riders)
    ("CASTRILLO Pablo", "Movistar Team"),
    ("MAS Enric", "Movistar Team"),
    ("OLIVEIRA Nelson", "Movistar Team"),
    ("RUBIO Einer", "Movistar Team"),
    ("ROMEO Iván", "Movistar Team"),
    ("MÜHLBERGER Gregor", "Movistar Team"),
    ("BARTA Will", "Movistar Team"),
    ("GARCÍA CORTINA Iván", "Movistar Team"),
    
    # Team Picnic PostNL (8 riders)
    ("ANDRESEN Tobias Lund", "Team Picnic PostNL"),
    ("VAN DEN BROEK Frank", "Team Picnic PostNL"),
    ("NABERMAN Tim", "Team Picnic PostNL"),
    ("BARGUIL Warren", "Team Picnic PostNL"),
    ("FLYNN Sean", "Team Picnic PostNL"),
    ("ONLEY Oscar", "Team Picnic PostNL"),
    ("BITTNER Pavel", "Team Picnic PostNL"),
    ("MÄRKL Niklas", "Team Picnic PostNL"),
    
    # Team Jayco AlUla (8 riders)
    ("O'CONNOR Ben", "Team Jayco AlUla"),
    ("PLAPP Luke", "Team Jayco AlUla"),
    ("SCHMID Mauro", "Team Jayco AlUla"),
    ("GROENEWEGEN Dylan", "Team Jayco AlUla"),
    ("DUNBAR Eddie", "Team Jayco AlUla"),
    ("DURBRIDGE Luke", "Team Jayco AlUla"),
    ("MEZGEC Luka", "Team Jayco AlUla"),
    ("REINDERS Elmar", "Team Jayco AlUla"),
    
    # Bahrain - Victorious (8 riders)
    ("MARTINEZ Lenny", "Bahrain - Victorious"),
    ("BUITRAGO Santiago", "Bahrain - Victorious"),
    ("MOHORIČ Matej", "Bahrain - Victorious"),
    ("BAUHAUS Phil", "Bahrain - Victorious"),
    ("GRADEK Kamil", "Bahrain - Victorious"),
    ("HAIG Jack", "Bahrain - Victorious"),
    ("STANNARD Robert", "Bahrain - Victorious"),
    ("WRIGHT Fred", "Bahrain - Victorious"),
    
    # XDS Astana Team (8 riders)
    ("VELASCO Simone", "XDS Astana Team"),
    ("TEJADA Harold", "XDS Astana Team"),
    ("CHAMPOUSSIN Clément", "XDS Astana Team"),
    ("HIGUITA Sergio", "XDS Astana Team"),
    ("TEUNISSEN Mike", "XDS Astana Team"),
    ("FEDOROV Yevgeniy", "XDS Astana Team"),
    ("BALLERINI Davide", "XDS Astana Team"),
    ("BOL Cees", "XDS Astana Team"),
    
    # Lotto (8 riders)
    ("DE LIE Arnaud", "Lotto"),
    ("VAN EETVELT Lennert", "Lotto"),
    ("DE BUYST Jasper", "Lotto"),
    ("BERCKMOES Jenno", "Lotto"),
    ("DRIZNERS Jarrad", "Lotto"),
    ("SEPÚLVEDA Eduardo", "Lotto"),
    ("VAN MOER Brent", "Lotto"),
    ("GRIGNARD Sébastien", "Lotto"),
    
    # Israel - Premier Tech (8 riders)
    ("ACKERMANN Pascal", "Israel - Premier Tech"),
    ("BLACKMORE Joseph", "Israel - Premier Tech"),
    ("WOODS Michael", "Israel - Premier Tech"),
    ("LUTSENKO Alexey", "Israel - Premier Tech"),
    ("STEWART Jake", "Israel - Premier Tech"),
    ("BOIVIN Guillaume", "Israel - Premier Tech"),
    ("LOUVEL Matis", "Israel - Premier Tech"),
    ("NEILANDS Krists", "Israel - Premier Tech"),
    
    # Team TotalEnergies (8 riders)
    ("BURGAUDEAU Mathieu", "Team TotalEnergies"),
    ("JEANNIÈRE Emilien", "Team TotalEnergies"),
    ("TURGIS Anthony", "Team TotalEnergies"),
    ("JEGAT Jordan", "Team TotalEnergies"),
    ("DELETTRE Alexandre", "Team TotalEnergies"),
    ("CRAS Steff", "Team TotalEnergies"),
    ("VERCHER Mattéo", "Team TotalEnergies"),
    ("GACHIGNARD Thomas", "Team TotalEnergies"),
    
    # Tudor Pro Cycling Team (8 riders)
    ("ALAPHILIPPE Julian", "Tudor Pro Cycling Team"),
    ("DAINESE Alberto", "Tudor Pro Cycling Team"),
    ("HALLER Marco", "Tudor Pro Cycling Team"),
    ("HIRSCHI Marc", "Tudor Pro Cycling Team"),
    ("LIENHARD Fabian", "Tudor Pro Cycling Team"),
    ("MAYRHOFER Marius", "Tudor Pro Cycling Team"),
    ("STORER Michael", "Tudor Pro Cycling Team"),
    ("TRENTIN Matteo", "Tudor Pro Cycling Team"),
    
    # Uno-X Mobility (8 riders)
    ("CORT Magnus", "Uno-X Mobility"),
    ("WÆRENSKJOLD Søren", "Uno-X Mobility"),
    ("LEKNESSUND Andreas", "Uno-X Mobility"),
    ("JOHANNESSEN Tobias Halland", "Uno-X Mobility"),
    ("JOHANNESSEN Anders Halland", "Uno-X Mobility"),
    ("ABRAHAMSEN Jonas", "Uno-X Mobility"),
    ("HOELGAARD Markus", "Uno-X Mobility"),
    ("FREDHEIM Stian", "Uno-X Mobility"),
]

# Riders not found in original data (new for 2025)
NEW_RIDERS_NOT_IN_ORIGINAL_DATA = [
    {"official_name": "KWIATKOWSKI Michał", "pcs_name": "KWIATKOWSKI Michał", "pcs_rank": 326, "pcs_points_2025": 111.0, "pcs_nationality": "PL"},
    {"official_name": "VALGREN Michael", "pcs_name": "VALGREN Michael", "pcs_rank": 478, "pcs_points_2025": 65.0, "pcs_nationality": "DK"},
]


def normalize_name(name):
    """Normalize rider names for matching"""
    if not name:
        return ""
    return re.sub(r'[^\w\s]', '', name.upper().strip())


def find_rider_match(rider_name, existing_riders):
    """Find matching rider in existing data"""
    normalized_target = normalize_name(rider_name)
    
    for rider in existing_riders:
        # Try matching with PCS name first (most accurate)
        if 'pcs_name' in rider and rider['pcs_name']:
            normalized_pcs = normalize_name(rider['pcs_name'])
            if normalized_pcs == normalized_target:
                return rider
                
        # Try matching with fantasy name
        normalized_fantasy = normalize_name(rider['fantasy_name'])
        if normalized_fantasy == normalized_target:
            return rider
            
        # Check if names contain same words (partial match)
        target_words = set(normalized_target.split())
        pcs_words = set(normalize_name(rider.get('pcs_name', '')).split()) if 'pcs_name' in rider else set()
        fantasy_words = set(normalized_fantasy.split())
        
        # Check for at least 2 matching words or single word exact match
        if len(target_words.intersection(pcs_words)) >= 2:
            return rider
        if len(target_words.intersection(fantasy_words)) >= 2:
            return rider
            
        # For single word names (like "FREDHEIM"), check exact match
        if len(target_words) == 1 and (target_words == pcs_words or target_words == fantasy_words):
            return rider
    
    return None


def update_tdf_roster():
    """Update combined_riders_data.json with final 183 TdF 2025 riders"""
    
    print(f"Processing {len(FINAL_RIDERS)} riders for TdF 2025...")
    
    # Load existing combined data
    with open('combined_riders_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    existing_riders = data['riders']
    print(f"Loaded {len(existing_riders)} existing riders from combined data\n")
    
    # Find matches and create new rider list
    new_riders = []
    unmatched_riders = []
    team_updates = 0
    
    for rider_name, team_name in FINAL_RIDERS:
        match = find_rider_match(rider_name, existing_riders)
        if match:
            # Update team name if different
            if match['team'] != team_name:
                print(f"Updating team for {rider_name}: {match['team']} -> {team_name}")
                match['team'] = team_name
                team_updates += 1
            new_riders.append(match)
        else:
            unmatched_riders.append((rider_name, team_name))
    
    print(f"\nInitial matching results:")
    print(f"  Matched: {len(new_riders)} riders")
    print(f"  Unmatched: {len(unmatched_riders)} riders") 
    print(f"  Team updates: {team_updates}")
    
    # Handle unmatched riders - skip them (they are not in original fantasy data)
    if unmatched_riders:
        print(f"\nSkipping {len(unmatched_riders)} unmatched riders (not in original fantasy data):")
        for rider_name, team_name in unmatched_riders:
            print(f"  - {rider_name} ({team_name}) - not in original CSV")
    
    # Update the data structure
    data['integration_info']['fantasy_riders_count'] = len(new_riders)
    data['integration_info']['matched_riders'] = len(new_riders)
    data['integration_info']['last_update'] = datetime.now().isoformat()
    data['integration_info']['notes'] = f"Updated to final TdF 2025 roster from original fantasy data - {len(new_riders)} riders found"
    data['riders'] = new_riders
    
    # Save updated data
    with open('combined_riders_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Updated combined_riders_data.json with {len(new_riders)} riders")
    
    # Print summary by team
    team_counts = {}
    for rider in new_riders:
        team = rider['team']
        team_counts[team] = team_counts.get(team, 0) + 1
    
    print(f"\nRiders by team ({len(team_counts)} teams):")
    for team, count in sorted(team_counts.items()):
        expected = 8 if team not in ["INEOS Grenadiers"] else 7  # INEOS has 7 riders
        status = "✓" if count == expected else f"⚠ (expected {expected})"
        print(f"  {team}: {count} riders {status}")
    
    # Final statistics
    print(f"\nFINAL STATISTICS:")
    print(f"  Total riders: {len(new_riders)}")
    print(f"  Target: 183 riders")
    print(f"  Success rate: {(len(new_riders)/183)*100:.1f}%")
    
    if len(new_riders) == 183:
        print("\n✅ SUCCESS: All 183 TdF 2025 riders included!")
    else:
        print(f"\n⚠️  WARNING: Missing {183 - len(new_riders)} riders")
    
    return len(new_riders)


if __name__ == "__main__":
    final_count = update_tdf_roster()
    print(f"\nScript completed. Final roster contains {final_count} riders.")