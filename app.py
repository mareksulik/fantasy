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

def format_number(number):
    """Formats number"""
    if number is None:
        return '0'
    return f"{number:,.0f}"

# Register helper functions for templates
app.jinja_env.globals.update(
    get_value_class=get_value_class,
    get_category_class=get_category_class,
    format_number=format_number
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
    """Main page"""
    return render_template('index.html')

@app.route('/riders')
def riders():
    """Page with list of all riders"""
    data = load_riders_data()
    
    # Filtering
    category_filter = request.args.get('category', 'all')
    min_price = request.args.get('min_price', type=int)
    max_price = request.args.get('max_price', type=int)
    sort_by = request.args.get('sort', 'points_per_credit')
    
    # Filter data
    filtered_data = data.copy()
    
    if category_filter != 'all':
        filtered_data = [r for r in filtered_data if r['category'].lower() == category_filter.lower()]
    
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
                             'min_price': min_price,
                             'max_price': max_price,
                             'sort': sort_by
                         })

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
    
    data = load_riders_data()
    matched_riders = [r for r in data if r['pcs_match_found']]
    
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
    
    # Greedy selection s budget constraint
    selected_team = []
    total_cost = 0
    
    for rider in sorted_riders:
        if total_cost + rider['price'] <= budget:
            selected_team.append(rider)
            total_cost += rider['price']
            
            # Limit to 8 riders (standard fantasy team)
            if len(selected_team) >= 8:
                break
    
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
            'team_size': len(selected_team)
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