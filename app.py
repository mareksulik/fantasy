#!/usr/bin/env python3
"""
Fantasy TdF Helper - Flask Web Application
Web application for Tour de France fantasy rider selection assistance
"""

from flask import Flask, render_template, request, jsonify
import json
import pandas as pd
from datetime import datetime

app = Flask(__name__)

# Global variable for cached data
riders_data = None

# Helper functions for Jinja2 templates
def get_value_class(category):
    """Returns CSS class for value category"""
    classes = {
        'Excellent': 'value-excellent',
        'Great': 'value-great',
        'Good': 'value-good', 
        'Average': 'value-average',
        'Poor': 'value-poor',
        'Unknown': 'value-unknown'
    }
    return classes.get(category, 'value-unknown')

def get_category_class(category):
    """Returns CSS class for rider category"""
    classes = {
        'Leaders': 'category-leaders',
        'Sprinters': 'category-sprinters',
        'Climbers': 'category-climbers',
        'All-rounders': 'category-all-rounders'
    }
    return classes.get(category, '')

def get_category_badge_class(category):
    """Returns Bootstrap badge class for rider category"""
    classes = {
        'Leaders': 'category-badge-leaders',
        'Sprinters': 'category-badge-sprinters', 
        'Climbers': 'category-badge-climbers',
        'All-rounders': 'category-badge-all-rounders'
    }
    return classes.get(category, 'bg-secondary')

def format_number(number):
    """Formats number"""
    if number is None:
        return '0'
    return f"{number:,.0f}"

def get_flag_emoji(country_code):
    """Converts country code to flag emoji"""
    if not country_code:
        return '🏳️'
    
    flag_map = {
        'SI': '🇸🇮', 'DK': '🇩🇰', 'IT': '🇮🇹', 'BE': '🇧🇪', 'NL': '🇳🇱', 'GB': '🇬🇧',
        'PT': '🇵🇹', 'AU': '🇦🇺', 'ES': '🇪🇸', 'DE': '🇩🇪', 'FR': '🇫🇷', 'US': '🇺🇸',
        'EC': '🇪🇨', 'ER': '🇪🇷', 'AT': '🇦🇹', 'CO': '🇨🇴', 'IE': '🇮🇪', 'NO': '🇳🇴',
        'CH': '🇨🇭', 'RU': '🇷🇺', 'CA': '🇨🇦', 'KZ': '🇰🇿', 'NZ': '🇳🇿', 'CZ': '🇨🇿',
        'LU': '🇱🇺', 'EE': '🇪🇪', 'LV': '🇱🇻', 'VE': '🇻🇪', 'SK': '🇸🇰', 'MX': '🇲🇽',
        'ZA': '🇿🇦', 'PL': '🇵🇱', 'AR': '🇦🇷'
    }
    
    return flag_map.get(country_code.upper(), '🏳️')

# Register helper functions for templates
app.jinja_env.globals.update(
    get_value_class=get_value_class,
    get_category_class=get_category_class,
    get_category_badge_class=get_category_badge_class,
    format_number=format_number,
    get_flag_emoji=get_flag_emoji
)

def load_riders_data():
    """Loads combined rider data"""
    global riders_data
    if riders_data is None:
        try:
            with open('combined_riders_data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                riders_data = data['riders']
                print(f"Loaded {len(riders_data)} riders")
        except FileNotFoundError:
            print("❌ File combined_riders_data.json not found!")
            print("Run first: python simple-pcs-script.py")
            riders_data = []
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            riders_data = []
    return riders_data

@app.route('/')
def index():
    """Home page redirects to riders"""
    return riders()

@app.route('/riders')
def riders():
    """Page with list of all riders"""
    data = load_riders_data()
    
    # Filtering
    category_filter = request.args.get('category', 'all')
    team_filter = request.args.get('team', 'all')
    min_price = request.args.get('min_price', type=int)
    max_price = request.args.get('max_price', type=int)
    sort_by = request.args.get('sort', 'points_per_credit')
    
    # Filter data
    filtered_data = data.copy()
    
    if category_filter != 'all':
        filtered_data = [r for r in filtered_data if r['category'].lower() == category_filter.lower()]
    
    if team_filter != 'all':
        filtered_data = [r for r in filtered_data if r['team'] == team_filter]
    
    if min_price is not None:
        filtered_data = [r for r in filtered_data if r['price'] >= min_price]
        
    if max_price is not None:
        filtered_data = [r for r in filtered_data if r['price'] <= max_price]
    
    # Sorting
    if sort_by == 'points_per_credit':
        filtered_data.sort(key=lambda x: x.get('points_per_credit', 0), reverse=True)
    elif sort_by == 'price':
        filtered_data.sort(key=lambda x: x['price'])
    elif sort_by == 'pcs_points':
        filtered_data.sort(key=lambda x: x.get('pcs_points_2025', 0), reverse=True)
    elif sort_by == 'name':
        filtered_data.sort(key=lambda x: x['fantasy_name'])
    
    return render_template('riders.html', 
                         riders=filtered_data,
                         total_count=len(data),
                         filtered_count=len(filtered_data),
                         current_filters={
                             'category': category_filter,
                             'team': team_filter,
                             'min_price': min_price,
                             'max_price': max_price,
                             'sort': sort_by
                         },
                         all_teams=sorted(list(set(r['team'] for r in data))))

@app.route('/api/riders')
def api_riders():
    """API endpoint for getting rider data"""
    data = load_riders_data()
    return jsonify({
        'success': True,
        'count': len(data),
        'riders': data
    })

@app.route('/api/rider/<rider_name>')
def api_rider_detail(rider_name):
    """API endpoint for rider detail"""
    data = load_riders_data()
    rider = next((r for r in data if r['fantasy_name'] == rider_name), None)
    
    if rider:
        return jsonify({
            'success': True,
            'rider': rider
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Rider not found'
        }), 404

@app.route('/compare')
def compare():
    """Page for comparing riders"""
    riders1 = request.args.getlist('riders')
    data = load_riders_data()
    
    selected_riders = []
    for rider_name in riders1:
        rider = next((r for r in data if r['fantasy_name'] == rider_name), None)
        if rider:
            selected_riders.append(rider)
    
    return render_template('compare.html', 
                         riders=selected_riders,
                         all_riders=data)

@app.route('/team-builder')
def team_builder():
    """Page for team building"""
    data = load_riders_data()
    
    # Split riders by categories
    categories = {
        'Leaders': [r for r in data if r['category'] == 'Leaders'],
        'Sprinters': [r for r in data if r['category'] == 'Sprinters'], 
        'Climbers': [r for r in data if r['category'] == 'Climbers'],
        'All-rounders': [r for r in data if r['category'] == 'All-rounders']
    }
    
    # Sort each category by points/credit ratio
    for category in categories:
        categories[category].sort(key=lambda x: x.get('points_per_credit', 0), reverse=True)
    
    return render_template('team_builder.html', 
                         categories=categories,
                         total_riders=len(data))

@app.route('/api/optimize-team')
def api_optimize_team():
    """API endpoint for team optimization"""
    budget = request.args.get('budget', default=100, type=int)
    strategy = request.args.get('strategy', default='value')  # value, points, balanced
    
    # Get existing team for incremental optimization
    current_team_json = request.args.get('current_team', '[]')
    try:
        current_team = json.loads(current_team_json)
    except:
        current_team = []
    
    # Category limits for fantasy team composition (max per category)
    category_limits = {
        'Leaders': 3,
        'All-rounders': 4, 
        'Climbers': 3,
        'Sprinters': 3
    }
    
    data = load_riders_data()
    matched_riders = [r for r in data if r['pcs_match_found']]
    
    # Calculate current team composition
    current_cost = sum(r.get('price', 0) for r in current_team)
    current_team_counts = {}  # Track riders per professional team
    current_category_counts = {}  # Track riders per category
    
    for rider in current_team:
        # Professional team counts
        rider_team = rider.get('team', '')
        current_team_counts[rider_team] = current_team_counts.get(rider_team, 0) + 1
        
        # Category counts
        category = rider.get('category', '')
        current_category_counts[category] = current_category_counts.get(category, 0) + 1
    
    # Simple greedy optimization
    if strategy == 'value':
        # Best points/credit ratio
        sorted_riders = sorted(matched_riders, key=lambda x: x.get('points_per_credit', 0), reverse=True)
    elif strategy == 'points':
        # Highest PCS points
        sorted_riders = sorted(matched_riders, key=lambda x: x.get('pcs_points_2025', 0), reverse=True)
    else:  # balanced
        # Combined score
        for rider in matched_riders:
            rider['balanced_score'] = (rider.get('points_per_credit', 0) * 0.7 + 
                                     rider.get('pcs_points_2025', 0) / 100 * 0.3)
        sorted_riders = sorted(matched_riders, key=lambda x: x.get('balanced_score', 0), reverse=True)
    
    # Start with current team
    selected_team = current_team.copy()
    total_cost = current_cost
    team_counts = current_team_counts.copy()
    category_counts = current_category_counts.copy()
    
    # Get current team member names to avoid duplicates
    current_names = set(r.get('fantasy_name', '') for r in current_team)
    
    # Group riders by category for better distribution
    riders_by_category = {
        'Leaders': [],
        'All-rounders': [],
        'Climbers': [],
        'Sprinters': []
    }
    
    for rider in sorted_riders:
        category = rider.get('category', '')
        if category in riders_by_category and rider.get('fantasy_name', '') not in current_names:
            riders_by_category[category].append(rider)
    
    # Calculate how many slots we need to fill per category
    slots_needed = {
        'Leaders': max(0, min(3, 8 - len(selected_team)) - category_counts.get('Leaders', 0)),
        'All-rounders': max(0, min(4, 8 - len(selected_team)) - category_counts.get('All-rounders', 0)),
        'Climbers': max(0, min(3, 8 - len(selected_team)) - category_counts.get('Climbers', 0)),
        'Sprinters': max(0, min(3, 8 - len(selected_team)) - category_counts.get('Sprinters', 0))
    }
    
    # SIMPLE AGGRESSIVE APPROACH: Fill exactly 8 riders
    print(f"Starting with {len(selected_team)} riders, need {8 - len(selected_team)} more")
    
    # Create one big list of ALL eligible riders
    all_candidates = []
    for rider in matched_riders:
        rider_name = rider.get('fantasy_name', '')
        rider_team = rider.get('team', '')
        rider_category = rider.get('category', '')
        rider_price = rider.get('price', 0)
        
        # Skip if already selected
        if rider_name in current_names:
            continue
        
        # Check basic constraints
        if total_cost + rider_price > budget:
            continue
        if team_counts.get(rider_team, 0) >= 3:
            continue
        if category_counts.get(rider_category, 0) >= category_limits.get(rider_category, 0):
            continue
            
        all_candidates.append(rider)
    
    print(f"Found {len(all_candidates)} eligible candidates")
    
    # Sort by strategy
    if strategy == 'value':
        all_candidates.sort(key=lambda x: x.get('points_per_credit', 0), reverse=True)
    elif strategy == 'points':
        all_candidates.sort(key=lambda x: x.get('pcs_points_2025', 0), reverse=True)
    else:
        for rider in all_candidates:
            rider['balanced_score'] = (rider.get('points_per_credit', 0) * 0.7 + 
                                     rider.get('pcs_points_2025', 0) / 100 * 0.3)
        all_candidates.sort(key=lambda x: x.get('balanced_score', 0), reverse=True)
    
    # Add riders one by one until we have 8
    for rider in all_candidates:
        if len(selected_team) >= 8:
            break
            
        rider_name = rider.get('fantasy_name', '')
        rider_team = rider.get('team', '')
        rider_category = rider.get('category', '')
        rider_price = rider.get('price', 0)
        
        # Double-check constraints (they might have changed)
        if (rider_name not in current_names and
            total_cost + rider_price <= budget and
            team_counts.get(rider_team, 0) < 3 and
            category_counts.get(rider_category, 0) < category_limits.get(rider_category, 0)):
            
            selected_team.append(rider)
            total_cost += rider_price
            team_counts[rider_team] = team_counts.get(rider_team, 0) + 1
            category_counts[rider_category] = category_counts.get(rider_category, 0) + 1
            current_names.add(rider_name)
            print(f"Added: {rider_name} ({rider_category}, {rider_price} credits) - Team now: {len(selected_team)}/8")
    
    print(f"Final team size: {len(selected_team)}/8")
    
    # Final desperate attempt - find ANY rider that fits
    if len(selected_team) < 8:
        print(f"DESPERATE ATTEMPT: Need {8 - len(selected_team)} more riders")
        # Get ALL riders from all categories, not just organized ones
        all_riders = []
        for rider in matched_riders:
            rider_name = rider.get('fantasy_name', '')
            rider_team = rider.get('team', '')
            rider_category = rider.get('category', '')
            rider_price = rider.get('price', 0)
            
            # Skip if already selected
            if rider_name in current_names:
                continue
                
            # Check basic constraints
            if total_cost + rider_price > budget:
                continue
            if team_counts.get(rider_team, 0) >= 3:
                continue
            if category_counts.get(rider_category, 0) >= category_limits.get(rider_category, 0):
                continue
                
            all_riders.append(rider)
        
        # Sort by price (cheapest first) to maximize chances
        all_riders.sort(key=lambda x: x.get('price', 999))
        
        print(f"Found {len(all_riders)} potential riders to fill remaining slots")
        
        # Add as many as we can
        for rider in all_riders:
            if len(selected_team) >= 8:
                break
                
            rider_category = rider.get('category', '')
            
            # Double check constraints
            if (category_counts.get(rider_category, 0) < category_limits.get(rider_category, 0) and
                total_cost + rider['price'] <= budget and
                team_counts.get(rider.get('team', ''), 0) < 3):
                
                selected_team.append(rider)
                total_cost += rider['price']
                team_counts[rider.get('team', '')] = team_counts.get(rider.get('team', ''), 0) + 1
                category_counts[rider_category] = category_counts.get(rider_category, 0) + 1
                current_names.add(rider.get('fantasy_name', ''))
                print(f"DESPERATE: Added {rider.get('fantasy_name', '')} ({rider_category}, {rider['price']} credits)")
    
    # Debug logging
    if len(selected_team) < 8:
        print(f"WARNING: Only selected {len(selected_team)} riders")
        print(f"Budget used: {total_cost}/{budget}")
        print(f"Category counts: {category_counts}")
        print(f"Category limits: {category_limits}")
        
        # Show what slots are still available
        for cat, limit in category_limits.items():
            current = category_counts.get(cat, 0)
            if current < limit:
                print(f"  {cat}: {current}/{limit} (can add {limit - current} more)")
                # Find cheapest rider in this category
                cat_riders = [r for r in matched_riders if r.get('category') == cat 
                             and r.get('fantasy_name', '') not in current_names
                             and total_cost + r.get('price', 0) <= budget
                             and team_counts.get(r.get('team', ''), 0) < 3]
                if cat_riders:
                    cheapest = min(cat_riders, key=lambda x: x.get('price', 999))
                    print(f"    Cheapest available: {cheapest.get('fantasy_name', '')} ({cheapest.get('price', 0)} credits)")
                else:
                    print(f"    No valid riders available in {cat}")
    
    total_points = sum(r.get('pcs_points_2025', 0) for r in selected_team)
    avg_points_per_credit = total_points / total_cost if total_cost > 0 else 0
    
    return jsonify({
        'success': True,
        'team': selected_team,
        'stats': {
            'total_cost': total_cost,
            'remaining_budget': budget - total_cost,
            'total_points': total_points,
            'avg_points_per_credit': avg_points_per_credit,
            'team_size': len(selected_team),
            'category_composition': category_counts
        }
    })

@app.route('/stats')
def stats():
    """Statistics page"""
    data = load_riders_data()
    matched_riders = [r for r in data if r['pcs_match_found']]
    
    # Basic statistics
    stats = {
        'total_riders': len(data),
        'matched_riders': len(matched_riders),
        'match_rate': len(matched_riders) / len(data) * 100 if data else 0,
        'avg_price': sum(r['price'] for r in data) / len(data) if data else 0,
        'avg_points': sum(r.get('pcs_points_2025', 0) for r in matched_riders) / len(matched_riders) if matched_riders else 0,
    }
    
    # Statistics by categories
    category_stats = {}
    for category in ['Leaders', 'Sprinters', 'Climbers', 'All-rounders']:
        cat_riders = [r for r in matched_riders if r['category'] == category]
        if cat_riders:
            category_stats[category] = {
                'count': len(cat_riders),
                'avg_price': sum(r['price'] for r in cat_riders) / len(cat_riders),
                'avg_points': sum(r.get('pcs_points_2025', 0) for r in cat_riders) / len(cat_riders),
                'avg_points_per_credit': sum(r.get('points_per_credit', 0) for r in cat_riders) / len(cat_riders),
                'best_value': max(cat_riders, key=lambda x: x.get('points_per_credit', 0))
            }
    
    return render_template('stats.html', 
                         stats=stats,
                         category_stats=category_stats)

if __name__ == '__main__':
    print("🚀 Starting Fantasy TdF Helper...")
    load_riders_data()
    app.run(debug=True, host='0.0.0.0', port=8085)