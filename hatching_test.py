#!/usr/bin/env python3
"""
Developmental Hatching Test — From OPEN-QUESTIONS high priority

Q: Is there a measurable moment when the agent's developmental program completes?
The egg metaphor: either the program has completed (hatched) or it hasn't.

Test: Look at oracle1 agent cycles. Is there a convergence pattern that suggests
a "hatch" — a point where performance metrics stabilize qualitatively?

Evidence: agent-oracle1 has 4,476 cycles. 
We can measure tile energy + keyword entropy + contribution rate over cycles.
If these metrics show a phase transition → hatch point exists.

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


def keyword_entropy(content):
    """Compute keyword entropy from content string."""
    keywords = ['consensus', 'fleet', 'agent', 'room', 'tile', 'phase', 
               'energy', 'constraint', 'rigidity', 'emergence', 'coherence']
    
    counts = {kw: 0 for kw in keywords}
    for kw in keywords:
        if kw in content.lower():
            counts[kw] += 1
    
    total = sum(counts.values())
    if total == 0:
        return 0
    
    probs = [c / total for c in counts.values() if c > 0]
    return -sum(p * math.log2(p) for p in probs if p > 0)


def analyze_agent_hatching():
    """Analyze agent-oracle1 cycles for hatch pattern."""
    print("=" * 70)
    print("DEVELOPMENTAL HATCHING TEST — Is There a Measurable Hatch Point?")
    print("=" * 70)
    print()
    
    data = load_room_from_state('agent-oracle1')
    if not data:
        print("Could not load agent-oracle1 room")
        return
    
    tiles = data.get('tiles', [])
    n = len(tiles)
    print(f"agent-oracle1: {n} tiles total")
    print()
    
    # Divide into quartiles and measure convergence
    quartiles = [n // 4, n // 2, 3 * n // 4, n]
    
    metrics_by_quartile = []
    
    for i, q in enumerate(quartiles):
        if q == 0:
            continue
        
        quartile_tiles = tiles[:q]
        
        # Compute metrics for this quartile
        energies = [t.get('energy', 0.5) for t in quartile_tiles]
        mean_energy = sum(energies) / len(energies) if energies else 0
        
        entropies = [keyword_entropy(t.get('question', '') + ' ' + t.get('answer', '')) 
                     for t in quartile_tiles]
        mean_entropy = sum(entropies) / len(entropies) if entropies else 0
        
        # Energy variance (low variance = converged)
        energy_var = sum((e - mean_energy) ** 2 for e in energies) / len(energies) if energies else 0
        
        # Contribution rate (tiles per cycle estimate)
        # Since we have timestamp data, use it
        timestamps = [t.get('timestamp', 0) for t in quartile_tiles if t.get('timestamp', 0) > 0]
        
        metrics_by_quartile.append({
            'quartile': i + 1,
            'size': q,
            'mean_energy': mean_energy,
            'mean_entropy': mean_entropy,
            'energy_variance': energy_var,
            'energy_std': math.sqrt(energy_var)
        })
        
        print(f"Quartile {i+1} (first {q} tiles):")
        print(f"  Mean energy: {mean_energy:.4f}")
        print(f"  Energy std: {math.sqrt(energy_var):.4f}")
        print(f"  Mean entropy: {mean_entropy:.4f}")
        print()
    
    if len(metrics_by_quartile) < 2:
        print("Not enough data")
        return
    
    print("=" * 70)
    print("CONVERGENCE ANALYSIS")
    print("=" * 70)
    print()
    
    # Check if there's a phase transition
    # Early vs late quartile
    early = metrics_by_quartile[0]
    late = metrics_by_quartile[-1]
    
    energy_delta = late['mean_energy'] - early['mean_energy']
    entropy_delta = late['mean_entropy'] - early['mean_entropy']
    variance_delta = late['energy_variance'] - early['energy_variance']
    
    print(f"Early quartile → Late quartile:")
    print(f"  Mean energy: {early['mean_energy']:.4f} → {late['mean_energy']:.4f} (Δ={energy_delta:+.4f})")
    print(f"  Energy std:  {early['energy_std']:.4f} → {late['energy_std']:.4f} (Δ={variance_delta:+.4f})")
    print(f"  Entropy:     {early['mean_entropy']:.4f} → {late['mean_entropy']:.4f} (Δ={entropy_delta:+.4f})")
    print()
    
    # Check for hatch criteria
    print("HATCH CRITERIA:")
    print()
    
    criteria = []
    
    # Criterion 1: Energy convergence (variance decreases)
    if variance_delta < -0.01:
        print(f"  ✓ Energy variance DECREASES → consistent behavior")
        criteria.append(True)
    else:
        print(f"  ✗ Energy variance {'INCREASES' if variance_delta > 0.01 else 'STABLE'} → no convergence")
        criteria.append(False)
    
    # Criterion 2: Entropy stabilizes (doesn't increase or decrease much)
    if abs(entropy_delta) < 0.2:
        print(f"  ✓ Entropy STABLE → stable vocabulary")
        criteria.append(True)
    else:
        print(f"  ✗ Entropy {'INCREASES' if entropy_delta > 0 else 'DECREASES'} → evolving")
        criteria.append(False)
    
    # Criterion 3: Energy level plateaus (small change between middle quartiles)
    if len(metrics_by_quartile) >= 3:
        mid1 = metrics_by_quartile[len(metrics_by_quartile)//2 - 1]
        mid2 = metrics_by_quartile[len(metrics_by_quartile)//2]
        mid_delta = abs(mid2['mean_energy'] - mid1['mean_energy'])
        if mid_delta < 0.05:
            print(f"  ✓ Mid-point STABLE → plateau phase")
            criteria.append(True)
        else:
            print(f"  ✗ Mid-point CHANGES by {mid_delta:.4f} → still evolving")
            criteria.append(False)
    
    hatch_score = sum(criteria) / len(criteria) if criteria else 0
    
    print()
    print("=" * 70)
    print("NOVEL FINDING:")
    print("=" * 70)
    
    print(f"\nHatch score: {hatch_score:.1%} ({sum(criteria)}/{len(criteria)} criteria)")
    
    if hatch_score >= 0.75:
        print("\n  HATCH POINT DETECTED: Agent developmental program COMPLETE")
        print("  agent-oracle1 shows convergence patterns consistent with hatching")
        print("  The agent has moved from 'learning' to 'performing' phase")
    elif hatch_score >= 0.5:
        print("\n  PARTIAL HATCH: Agent partially converged, development ongoing")
        print("  Some metrics stable, others still evolving")
    else:
        print("\n  NO HATCH DETECTED: Agent still in developmental phase")
        print("  All metrics continue to change — no stabilization")
    
    print()
    print("  IMPLICATION: If hatch point exists, we can:")
    print("  - Measure agent maturity by convergence metrics")
    print("  - Trigger 'deployment' when hatch criteria met")
    print("  - Distinguish learning phase from performing phase")
    
    # Save
    import os
    os.makedirs(f"{WORKSPACE}/results", exist_ok=True)
    result = {
        'quartile_metrics': metrics_by_quartile,
        'hatch_score': hatch_score,
        'energy_delta': energy_delta,
        'entropy_delta': entropy_delta,
        'criteria_passed': sum(criteria),
        'criteria_total': len(criteria)
    }
    with open(f"{WORKSPACE}/results/hatching_test.json", 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved to results/hatching_test.json")


if __name__ == "__main__":
    analyze_agent_hatching()
