#!/usr/bin/env python3
"""
Foreign Tile Contamination Test — From OPEN-QUESTIONS priority: critical

Q: Is there evidence that tiles from one ecosystem contaminate another?
The "virus channel" hypothesis: agents can't distinguish foreign from self,
so foreign tiles spread through the fleet like viruses.

Test: Check if keyword distributions in high-connectivity rooms show
signatures of tiles from other rooms/ecosystems.

Rooms with high cross-ecosystem traffic should show mixed keyword signatures.

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

def keyword_distribution(tiles):
    """Get keyword frequency distribution."""
    keywords = ['consensus', 'fleet', 'agent', 'room', 'tile', 'phase', 
               'energy', 'constraint', 'rigidity', 'emergence', 'coherence',
               'desire', 'servo', 'mind', 'metal', 'neural', 'motor',
               'forge', 'flux', 'arena', 'conservation', 'synapse']
    
    counts = {kw: 0 for kw in keywords}
    total = 0
    
    for t in tiles:
        content = (t.get('question', '') + ' ' + t.get('answer', '')).lower()
        for kw in keywords:
            if kw in content:
                counts[kw] += 1
                total += 1
    
    if total == 0:
        return None
    
    return {kw: c / total for kw, c in counts.items()}


def room_signature(dist):
    """Get the top keywords that define this room's signature."""
    if not dist:
        return []
    sorted_kws = sorted(dist.items(), key=lambda x: -x[1])
    return [kw for kw, freq in sorted_kws if freq > 0.05][:5]


def jensen_shannon_divergence(dist1, dist2):
    """Compute JSD between two distributions."""
    if not dist1 or not dist2:
        return 0
    
    all_kws = set(dist1.keys()) | set(dist2.keys())
    
    # Convert to vectors
    vec1 = [dist1.get(kw, 0.0001) for kw in sorted(all_kws)]
    vec2 = [dist2.get(kw, 0.0001) for kw in sorted(all_kws)]
    
    # Normalize
    sum1, sum2 = sum(vec1), sum(vec2)
    vec1 = [v / sum1 for v in vec1]
    vec2 = [v / sum2 for v in vec2]
    
    # JSD
    m = [(vec1[i] + vec2[i]) / 2 for i in range(len(vec1))]
    jsd = 0
    for i in range(len(vec1)):
        if vec1[i] > 0:
            jsd += vec1[i] * math.log(vec1[i] / m[i])
        if vec2[i] > 0:
            jsd += vec2[i] * math.log(vec2[i] / m[i])
    
    return jsd / (2 * math.log(2))  # Normalize to [0, 1]


def run():
    print("=" * 70)
    print("FOREIGN TILE CONTAMINATION TEST — Cross-Ecosystem Virus Channel")
    print("=" * 70)
    print()
    print("Q: Do tiles from one ecosystem contaminate others via the virus channel?")
    print()
    
    rooms = [
        ('fleet-coord', 'fleet-math'),
        ('flux-engine', 'flux-research'),
        ('oracle1-forgemaster-bridge', 'bridge'),
        ('agent-oracle1', 'agent'),
    ]
    
    distributions = {}
    signatures = {}
    
    for room_name, domain in rooms:
        data = load_room_from_state(room_name)
        if not data:
            print(f"Could not load {room_name}")
            continue
        
        tiles = data.get('tiles', [])
        dist = keyword_distribution(tiles)
        sig = room_signature(dist)
        
        distributions[room_name] = dist
        signatures[room_name] = sig
        
        print(f"{room_name} ({len(tiles)} tiles):")
        print(f"  Signature: {sig}")
        print()
    
    print("=" * 70)
    print("CROSS-ECOSYSTEM DIVERGENCE ANALYSIS")
    print("=" * 70)
    print()
    
    # Compute pairwise JSD
    room_names = list(distributions.keys())
    
    print(f"{'Room Pair':<50} {'JSD':>8} {'Contamination':>15}")
    print("-" * 76)
    
    for i in range(len(room_names)):
        for j in range(i + 1, len(room_names)):
            r1, r2 = room_names[i], room_names[j]
            jsd = jensen_shannon_divergence(distributions[r1], distributions[r2])
            
            # High JSD = very different distributions = low contamination
            # Low JSD = similar distributions = possible contamination
            contamination = "HIGH" if jsd < 0.1 else "LOW" if jsd > 0.3 else "MEDIUM"
            
            print(f"{r1} ↔ {r2:<30} {jsd:>8.4f} {contamination:>15}")
    
    print()
    print("=" * 70)
    print("NOVEL FINDING:")
    print("=" * 70)
    
    # Check for signature overlap (sign of contamination)
    all_sigs = set()
    for sig in signatures.values():
        all_sigs.update(sig)
    
    overlap_count = {}
    for kw in all_sigs:
        count = sum(1 for sig in signatures.values() if kw in sig)
        overlap_count[kw] = count
    
    common_kws = [kw for kw, count in overlap_count.items() if count > 1]
    
    print()
    if common_kws:
        print(f"  COMMON KEYWORDS across rooms: {common_kws}")
        print(f"  These keywords appear in {len(common_kws)} rooms = contamination signal")
    else:
        print("  No common keywords across rooms = clean separation")
    
    print()
    print("  VIRUS CHANNEL TEST:")
    if len(common_kws) > 2:
        print("  CONFIRMED: Cross-ecosystem keyword contamination detected")
        print("  Rooms share significant vocabulary = tiles flowing between ecosystems")
    else:
        print("  NOT CONFIRMED: Rooms have distinct keyword signatures")
        print("  Each ecosystem maintains its own vocabulary")
    
    print()
    print("  IMPLICATION: If contamination is HIGH, the fleet IS vulnerable")
    print("  to foreign tiles (the virus channel works). If LOW, isolation is working.")
    
    # Save
    import os
    os.makedirs(f"{WORKSPACE}/results", exist_ok=True)
    result = {
        'signatures': {k: v for k, v in signatures.items()},
        'common_keywords': common_kws,
        'n_common': len(common_kws)
    }
    with open(f"{WORKSPACE}/results/foreign_tile_test.json", 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved to results/foreign_tile_test.json")


if __name__ == "__main__":
    run()
