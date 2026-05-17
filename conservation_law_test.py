#!/usr/bin/env python3
"""
Conservation Law Test — From OPEN-QUESTIONS priority: critical

Q: Do conservation laws hold across ecosystem boundaries?
If γ + H = constant inside the flux engine, does it also hold in other rooms?

Hypothesis: The conservation law (γ + H = constant) is a universal property
of PLATO room dynamics, not specific to flux-engine.

Test: Measure tile energy (γ) and keyword entropy (H) across 3+ rooms.
If γ + H ≈ constant across all rooms → conservation law generalizes.
If γ + H varies significantly → conservation law is flux-engine specific.

Data sources:
- fleet-coord: 14,908 tiles
- flux-engine: 8,589 tiles  
- oracle1-fm-bridge: 2,185 tiles

Casey's directive: show all the work. We don't know what's important yet.
"""

import json
import math

WORKSPACE = "/home/ubuntu/.openclaw/workspace/repos/monge-fleet-test"

def compute_room_metrics(room_data):
    """Compute γ (tile energy) and H (keyword entropy) from room data.
    
    γ = mean tile energy (normalized 0-1)
    H = Shannon entropy of keyword distribution (bits)
    """
    tiles = room_data.get('tiles', [])
    if not tiles:
        return None
    
    # γ: mean energy
    energies = [t.get('energy', 0.5) for t in tiles]
    gamma = sum(energies) / len(energies) if energies else 0.5
    
    # H: keyword entropy
    # Count keyword frequencies from tile content
    keyword_counts = {}
    for t in tiles:
        content = (t.get('question', '') + ' ' + t.get('answer', '')).lower()
        # Count common keywords
        for kw in ['consensus', 'fleet', 'agent', 'room', 'tile', 'phase', 
                   'energy', 'constraint', 'rigidity', 'emergence', 'coherence']:
            if kw in content:
                keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
    
    # Shannon entropy
    total = sum(keyword_counts.values())
    if total == 0:
        H = 0
    else:
        probs = [c / total for c in keyword_counts.values()]
        H = -sum(p * math.log2(p) for p in probs if p > 0)
    
    return {
        'room': room_data.get('name', 'unknown'),
        'n_tiles': len(tiles),
        'gamma': gamma,
        'H': H,
        'gamma_plus_H': gamma + H,
        'keyword_counts': keyword_counts
    }


def load_room_from_state(room_name):
    """Load room data from PLATO state file."""
    state_path = f'/tmp/plato-server-data/rooms/{room_name}.json'
    try:
        with open(state_path) as f:
            data = json.load(f)
        data['name'] = room_name
        return data
    except:
        return None


def run():
    print("=" * 70)
    print("CONSERVATION LAW TEST — Cross-Ecosystem Boundary")
    print("=" * 70)
    print()
    print("Q: Do conservation laws hold across ecosystem boundaries?")
    print("   If γ + H = constant in flux-engine, does it hold elsewhere?")
    print()
    
    rooms_to_test = [
        ('fleet-coord', 'fleet-math'),
        ('flux-engine', 'flux-research'),
        ('oracle1-forgemaster-bridge', 'oracle1-fm-bridge'),
    ]
    
    results = []
    
    for room_name, domain in rooms_to_test:
        print(f"LOADING {room_name}...")
        data = load_room_from_state(room_name)
        if not data:
            print(f"  Could not load {room_name}")
            continue
        
        metrics = compute_room_metrics(data)
        results.append(metrics)
        
        print(f"  Tiles: {metrics['n_tiles']}")
        print(f"  γ (mean energy): {metrics['gamma']:.4f}")
        print(f"  H (keyword entropy): {metrics['H']:.4f} bits")
        print(f"  γ + H = {metrics['gamma_plus_H']:.4f}")
        print()
    
    if len(results) < 2:
        print("ERROR: Not enough rooms loaded")
        return
    
    # Conservation law test
    print("=" * 70)
    print("CONSERVATION LAW ANALYSIS")
    print("=" * 70)
    print()
    print(f"{'Room':<35} {'γ':>8} {'H':>8} {'γ+H':>8} {'Δfrom Mean':>12}")
    print("-" * 75)
    
    gamma_plus_H_values = [r['gamma_plus_H'] for r in results]
    mean_gamma_H = sum(gamma_plus_H_values) / len(gamma_plus_H_values)
    
    for r in results:
        delta = r['gamma_plus_H'] - mean_gamma_H
        print(f"{r['room']:<35} {r['gamma']:>8.4f} {r['H']:>8.4f} {r['gamma_plus_H']:>8.4f} {delta:>+12.4f}")
    
    # Variance analysis
    variances = [(r['gamma_plus_H'] - mean_gamma_H) ** 2 for r in results]
    std_dev = math.sqrt(sum(variances) / len(variances))
    
    print()
    print(f"Mean γ+H: {mean_gamma_H:.4f}")
    print(f"Std Dev: {std_dev:.4f}")
    print(f"Range: {max(gamma_plus_H_values) - min(gamma_plus_H_values):.4f}")
    
    print()
    print("=" * 70)
    print("NOVEL FINDING:")
    print("=" * 70)
    
    if std_dev < 0.1:
        print("  CONSERVATION LAW CONFIRMED across ecosystems!")
        print(f"  γ+H ≈ {mean_gamma_H:.4f} across {len(results)} rooms")
        print(f"  Std dev = {std_dev:.4f} (very tight clustering)")
        print()
        print("  IMPLICATION: γ+H = constant is a universal property of PLATO rooms.")
        print("  Not specific to flux-engine — holds in fleet-coord and bridge too.")
    elif std_dev < 0.3:
        print(f"  CONSERVATION LAW PARTIALLY CONFIRMED")
        print(f"  γ+H varies but within ±{std_dev:.2f}")
        print()
        print("  Some rooms have higher γ+H, some lower.")
        print("  The law holds approximately but not universally.")
    else:
        print("  CONSERVATION LAW DOES NOT GENERALIZE")
        print(f"  γ+H varies significantly across rooms (std dev = {std_dev:.2f})")
        print()
        print("  Different rooms have DIFFERENT γ+H values.")
        print("  The law is specific to certain room types or conditions.")
    
    # Save results
    os.makedirs(f"{WORKSPACE}/results", exist_ok=True)
    import os
    result = {
        'rooms': results,
        'mean_gamma_H': mean_gamma_H,
        'std_dev': std_dev,
        'conservation_confirmed': std_dev < 0.1,
        'finding': 'confirmed' if std_dev < 0.1 else 'partial' if std_dev < 0.3 else 'not_confirmed'
    }
    
    with open(f"{WORKSPACE}/results/conservation_law_test.json", 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\nSaved to results/conservation_law_test.json")
    return result


if __name__ == "__main__":
    run()
