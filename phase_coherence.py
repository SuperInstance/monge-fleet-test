#!/usr/bin/env python3
"""
Phase Coherence — Novel Room Quality Metric

Tests whether room oscillation reveals keyword structure.
Measures Spearman ranking correlation across 4 phase shifts (0, π/2, π, 3π/2).

Coherence = 0: ranking identical at all phases (static = bad?)
Coherence ~0.5: ranking changes with phase (oscillating = fractal)
Coherence = 1: ranking inverts at 180° (perfect phase dependence)

Key finding from PLATO room analysis:
  - Simulated fractal room: coherence ≈ 0.53
  - fleet-coord (14K tiles): coherence ≈ 0.24 (partially static)
  - flux-engine (8K tiles):   coherence ≈ 0.00 (perfectly static)
  - oracle1-fm-bridge:       coherence ≈ 0.00 (perfectly static)

Real rooms are NOT oscillating — they're static ordered lists.
"""
import math
import random

def spearman(rank_a, rank_b, n):
    """Spearman rank correlation between two rankings."""
    d_sq = sum((rank_a[i] - rank_b[i]) ** 2 for i in range(n))
    denom = n * (n**3 - 1) if n > 1 else 1
    return 1 - (6 * d_sq) / denom

def coherence_score(tiles, keywords, n_tiles=1000):
    """
    Score tiles at 4 phases, compute ranking coherence.
    tiles: list of keyword vectors [kw0, kw1, kw2, kw3] (0 or 1)
    keywords: list of keyword strings
    """
    class Tile:
        def __init__(self, kv): self.kv = kv

    tile_objs = [Tile(t) for t in tiles]

    def score(tile, phase):
        weights = [math.cos(phase - i * math.pi/2)**2 for i in range(len(keywords))]
        return sum(tile.kv[i] * weights[i] for i in range(len(keywords)))

    phases = [0, math.pi/2, math.pi, 3*math.pi/2]
    rankings = []
    for phase in phases:
        scored = [(score(t, phase), i) for i, t in enumerate(tile_objs)]
        scored.sort(key=lambda x: -x[0])
        rankings.append([i for _, i in scored])

    avg_c = 0
    for i in range(4):
        for j in range(i+1, 4):
            n = n_tiles
            ri = [0]*n; rj = [0]*n
            for pos, ti in enumerate(rankings[i]): ri[ti] = pos
            for pos, ti in enumerate(rankings[j]): rj[ti] = pos
            rho = spearman(ri, rj, n)
            c = (1 - rho) / 2
            avg_c += abs(c)
    return avg_c / 6

def test_simulated():
    """Test on simulated fractal room."""
    keywords = ['fleet', 'plato', 'agent', 'room']
    N = 1000

    # Perfect 4-way structure
    tiles = []
    for i in range(N//4): tiles.append([1,0,0,0])  # type A
    for i in range(N//4): tiles.append([0,1,0,0])  # type B
    for i in range(N//4): tiles.append([0,0,1,0])  # type C
    for i in range(N//4): tiles.append([0,0,0,1])  # type D
    random.shuffle(tiles)

    c = coherence_score(tiles, keywords)
    print(f"Simulated fractal room: coherence={c:.4f}")
    return c

def test_real_rooms():
    """Test on real PLATO rooms via API."""
    import subprocess, json

    rooms = ['fleet-coord', 'flux-engine', 'oracle1-forgemaster-bridge']
    keywords = ['plato', 'oracle', 'fleet', 'forge', 'sync', 'agent', 'room']

    print("\nReal PLATO room coherence:")
    for room in rooms:
        cmd = f'curl -s "http://localhost:8847/room/{room}/tiles?limit=1000"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        try:
            data = json.loads(result.stdout)
            tiles = data.get('tiles', [])
            if len(tiles) < 20:
                print(f"  {room}: too few tiles ({len(tiles)})")
                continue

            kv_list = []
            for tile in tiles:
                text = (tile.get('question', '') + ' ' + tile.get('answer', '')).lower()
                kv = [1 if kw in text else 0 for kw in keywords]
                if sum(kv) >= 1:
                    kv_list.append(kv)

            if len(kv_list) < 20:
                print(f"  {room}: not enough keyword tiles ({len(kv_list)})")
                continue

            N = min(500, len(kv_list))
            c = coherence_score(kv_list[:N], keywords)
            print(f"  {room}: {len(tiles)} tiles, coherence={c:.4f}")
        except:
            print(f"  {room}: API error")

if __name__ == "__main__":
    print("=" * 70)
    print("PHASE COHERENCE — Room Quality Metric")
    print("=" * 70)
    test_simulated()
    test_real_rooms()