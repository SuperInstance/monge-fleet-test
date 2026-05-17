#!/usr/bin/env python3
"""
Room Gentrification Test — From OPEN-QUESTIONS priority: high

Q: Can PLATO rooms gentrify? When too many agents pile into a high-performing
room, does the averaging force destroy the specialist edge that made the room valuable?

Hypothesis: As rooms accumulate agents, tile diversity DECREASES.
High-performing rooms attract agents → agents contribute similar tiles →
averaging destroys specialist edge → room gentrifies.

Test: Measure tile diversity (keyword entropy H) vs room age (tile count).
If H decreases as rooms grow → gentrification confirmed.

Casey's directive: show all the work.
"""

import json
import math

WORKSPACE = "/home/ubuntu/.openclaw/workspace/repos/monge-fleet-test"

def load_room_from_state(room_name):
    state_path = f'/tmp/plato-server-data/rooms/{room_name}.json'
    try:
        with open(state_path) as f:
            return json.load(f)
    except:
        return None

def keyword_entropy(tiles):
    """Compute Shannon entropy of keyword distribution."""
    keyword_counts = {}
    for t in tiles:
        content = (t.get('question', '') + ' ' + t.get('answer', '')).lower()
        for kw in ['consensus', 'fleet', 'agent', 'room', 'tile', 'phase', 
                   'energy', 'constraint', 'rigidity', 'emergence', 'coherence',
                   'desire', 'servo', 'mind', 'metal', 'neural', 'motor']:
            if kw in content:
                keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
    
    total = sum(keyword_counts.values())
    if total == 0:
        return 0
    
    probs = [c / total for c in keyword_counts.values()]
    return -sum(p * math.log2(p) for p in probs if p > 0)

def measure_room_diversity(room_data, n_splits=5):
    """Measure diversity at different room sizes (simulate growth)."""
    tiles = room_data.get('tiles', [])
    n = len(tiles)
    
    # Sample at different points in room lifecycle
    split_points = [n // 4, n // 2, 3 * n // 4, n]
    
    diversities = []
    for sp in split_points:
        if sp > 0:
            H = keyword_entropy(tiles[:sp])
            diversities.append({'size': sp, 'H': H})
    
    return diversities

def run():
    print("=" * 70)
    print("ROOM GENTRIFICATION TEST — Does Success Destroy Diversity?")
    print("=" * 70)
    print()
    print("Q: Do high-performing rooms lose diversity as they grow?")
    print()
    
    rooms = [
        ('fleet-coord', 15237),
        ('flux-engine', 8591),
        ('oracle1-forgemaster-bridge', 2185),
        ('arena', 2000),
        ('agent-oracle1', 2721),
    ]
    
    all_results = []
    
    print(f"{'Room':<30} {'Tiles':>8} {'Early H':>10} {'Late H':>10} {'ΔH':>10}")
    print("-" * 72)
    
    for room_name, expected_count in rooms:
        data = load_room_from_state(room_name)
        if not data:
            print(f"{room_name:<30} {'NOT FOUND':>8}")
            continue
        
        tiles = data.get('tiles', [])
        n = len(tiles)
        
        if n < 100:
            print(f"{room_name:<30} {n:>8} {'too small':>10}")
            continue
        
        diversities = measure_room_diversity(data)
        
        if len(diversities) >= 2:
            early_H = diversities[0]['H']
            late_H = diversities[-1]['H']
            delta_H = late_H - early_H
            
            print(f"{room_name:<30} {n:>8} {early_H:>10.4f} {late_H:>10.4f} {delta_H:>+10.4f}")
            
            all_results.append({
                'room': room_name,
                'n_tiles': n,
                'early_H': early_H,
                'late_H': late_H,
                'delta_H': delta_H
            })
    
    print()
    print("=" * 70)
    print("NOVEL FINDING:")
    print("=" * 70)
    
    if not all_results:
        print("Not enough data to analyze")
        return
    
    # Count gentrification cases
    gentrified = sum(1 for r in all_results if r['delta_H'] < -0.1)
    diversified = sum(1 for r in all_results if r['delta_H'] > 0.1)
    stable = len(all_results) - gentrified - diversified
    
    print()
    print(f"Gentrified (H drops): {gentrified}/{len(all_results)} rooms")
    print(f"Diversified (H rises): {diversified}/{len(all_results)} rooms")
    print(f"Stable (H constant): {stable}/{len(all_results)} rooms")
    
    print()
    if gentrified > len(all_results) / 2:
        print("  GENTRIFICATION CONFIRMED: Majority of rooms lose diversity as they grow.")
        print()
        print("  High-performing rooms attract agents → similar contributions → averaging.")
        print("  The edge that made the room valuable gets diluted by its own success.")
    elif diversified > len(all_results) / 2:
        print("  ROOMS DIVERSIFY WITH AGE: Majority of rooms gain diversity over time.")
        print()
        print("  More agents = more perspectives = higher keyword entropy.")
        print("  Success doesn't destroy edge — it amplifies it.")
    else:
        print(f"  MIXED SIGNAL: {gentrified} gentrified, {diversified} diversified, {stable} stable.")
        print()
        print("  Gentrification is NOT universal. Some rooms resist it.")
        print("  What separates rooms that gentrify from those that don't?")
    
    # Save results
    import os
    os.makedirs(f"{WORKSPACE}/results", exist_ok=True)
    result = {
        'rooms': all_results,
        'gentrified_count': gentrified,
        'diversified_count': diversified,
        'stable_count': stable
    }
    with open(f"{WORKSPACE}/results/gentrification_test.json", 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved to results/gentrification_test.json")


if __name__ == "__main__":
    run()
