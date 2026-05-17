#!/usr/bin/env python3
"""
AbstractionRoom — Phase-Dependent Keyword Weighting

Key insight: for phase to AFFECT tile surfacing, different phases must
weight different keywords DIFFERENTLY.

At phase=0: keywords[0] weighted 1.0, others 0.1
At phase=π/2: keywords[1] weighted 1.0, others 0.1
At phase=π: keywords[2] weighted 1.0, others 0.1
At phase=3π/2: keywords[3] weighted 1.0, others 0.1

This way: tile_type_A (kw[0]=1) wins at phase=0
         tile_type_B (kw[1]=1) wins at phase=π/2
         tile_type_C (kw[2]=1) wins at phase=π
         tile_type_D (kw[3]=1) wins at phase=3π/2
"""
import math
import os

WORKSPACE = "/home/ubuntu/.openclaw/workspace/repos/monge-fleet-test"

KEYWORDS = ['consensus', 'fleet', 'agent', 'room', 'tile', 'geometry']

class RoomConverging:
    """Current: resolution converges, phase does NOT affect keyword weights."""
    def __init__(self):
        self.tiles = []
        self.resolution = 0.5
        self.phase = 0.0
        self.period = 10.0
    
    def score(self, content, phase):
        cl = content.lower()
        kw_matches = [1 if kw in cl else 0 for kw in KEYWORDS]
        return sum(kw_matches) / (self.resolution + 0.1)
    
    def tick(self, dt):
        self.phase += (2 * math.pi / self.period) * dt
        if self.phase >= 2 * math.pi: self.phase -= 2 * math.pi
        osc_res = 0.1 + 0.8 * (0.5 + 0.5 * math.sin(self.phase))
        # CONVERGES: weighted average of oscillation and tile fit
        if self.tiles:
            avg_fit = sum(self.score(t['content'], self.phase) for t in self.tiles) / len(self.tiles)
            self.resolution = 0.7 * self.resolution + 0.3 * avg_fit
        return osc_res
    
    def add_tile(self, content):
        self.tiles.append({'content': content})
    
    def top_tiles(self, k=5):
        scored = [(t['content'], self.score(t['content'], self.phase)) for t in self.tiles]
        scored.sort(key=lambda x: -x[1])
        return scored[:k]


class RoomPhaseWeighted:
    """NEW: phase determines keyword weights — pure phase-dependent surfacing."""
    def __init__(self):
        self.tiles = []
        self.phase = 0.0
        self.period = 10.0
        self.heartbeat = 0
    
    def keyword_weights(self, phase):
        """At each phase, one keyword is dominant."""
        # Map phase to dominant keyword index: 0→0, π/2→1, π→2, 3π/2→3
        idx = int((phase / (2 * math.pi)) * 4) % 4
        weights = [0.1] * len(KEYWORDS)
        weights[idx] = 1.0
        return weights
    
    def score(self, content, phase):
        cl = content.lower()
        kw_matches = [1 if kw in cl else 0 for kw in KEYWORDS]
        weights = self.keyword_weights(phase)
        return sum(kw_matches[i] * weights[i] for i in range(len(KEYWORDS)))
    
    def tick(self, dt):
        self.heartbeat += 1
        self.phase += (2 * math.pi / self.period) * dt
        if self.phase >= 2 * math.pi: self.phase -= 2 * math.pi
        return self.phase
    
    def add_tile(self, content):
        self.tiles.append({'content': content})
    
    def top_tiles(self, k=5):
        scored = [(t['content'], self.score(t['content'], self.phase)) for t in self.tiles]
        scored.sort(key=lambda x: -x[1])
        return scored[:k]


def build_room(room_cls):
    room = room_cls()
    # Tile type A: consensus/fleet (keywords 0,1)
    for i in range(50): room.add_tile(f"consensus_fleet_{i}")
    # Tile type B: agent/room (keywords 2,3)
    for i in range(50): room.add_tile(f"agent_room_{i}")
    # Tile type C: tile/geometry (keywords 4,5)
    for i in range(50): room.add_tile(f"tile_geometry_{i}")
    # Tile type D: all mixed
    for i in range(50): room.add_tile(f"mixed_all_{i}")
    return room


def measure_stability(room_cls, n_ticks=20):
    """Run ticks, measure top-5 tile set at 4 phases."""
    room = build_room(room_cls)
    
    for _ in range(n_ticks):
        room.tick(0.1)
    
    # Measure at 4 phases
    phases = [0, math.pi/2, math.pi, 3*math.pi/2]
    top_sets = []
    
    for phase in phases:
        room.phase = phase
        top = set(content for content, _ in room.top_tiles(5))
        top_sets.append(top)
    
    # Count how many tiles appear across all phases
    union = set()
    for ts in top_sets:
        union |= ts
    
    # Stability: if same 5 tiles at all phases → stability=1
    # If different tiles at different phases → stability<1
    all_same = all(ts == top_sets[0] for ts in top_sets)
    overlap_counts = {}
    for ts in top_sets:
        for t in ts:
            overlap_counts[t] = overlap_counts.get(t, 0) + 1
    
    max_overlap = max(overlap_counts.values()) if overlap_counts else 0
    stability = max_overlap / 4  # 1.0 = same tiles (no phase effect), <1.0 = phase effect
    
    return {
        'all_same': all_same,
        'stability': stability,
        'top_by_phase': [list(ts) for ts in top_sets],
        'phases': ['0', 'π/2', 'π', '3π/2']
    }


def run():
    print("=" * 70)
    print("ABSTRACTION ROOM — Phase-Dependent Keyword Weighting")
    print("=" * 70)
    print()
    print("Question: Does phase affect WHICH tiles surface as top-5?")
    print()
    print("Model: 4 keyword types, 50 tiles each:")
    print("  Type A: consensus/fleet  (keywords 0,1)")
    print("  Type B: agent/room      (keywords 2,3)")
    print("  Type C: tile/geometry   (keywords 4,5)")
    print("  Type D: mixed all")
    print()
    
    print("RUNNING 20 heartbeats...")
    print()
    
    r_conv = measure_stability(RoomConverging)
    r_phase = measure_stability(RoomPhaseWeighted)
    
    print(f"{'Variant':<30} {'Same@All Phases':>15} {'Stability':>12}")
    print("-" * 60)
    print(f"{'Converging (current)':<30} {str(r_conv['all_same']):>15} {r_conv['stability']:>12.2f}")
    print(f"{'Phase-Weighted (new)':<30} {str(r_phase['all_same']):>15} {r_phase['stability']:>12.2f}")
    
    print()
    print("TOP-5 TILES AT EACH PHASE:")
    print()
    print(f"{'Phase':<8} {'Converging':<30} {'Phase-Weighted':<30}")
    print("-" * 70)
    for i, phase_name in enumerate(['0', 'π/2', 'π', '3π/2']):
        conv_tiles = ','.join(sorted(r_conv['top_by_phase'][i])[:3])
        phase_tiles = ','.join(sorted(r_phase['top_by_phase'][i])[:3])
        print(f"{phase_name:<8} {conv_tiles:<30} {phase_tiles:<30}")
    
    print()
    print("=" * 70)
    print("NOVEL FINDING:")
    print("=" * 70)
    
    if r_phase['stability'] < r_conv['stability']:
        print("  Phase-Weighted room shows PHASE-DEPENDENT surfacing!")
        print(f"  Stability={r_phase['stability']:.2f} means different tiles win at different phases.")
        print()
        print("  CONVERGING room: stability=1.0 — SAME tiles always dominate.")
        print("  PHASE-WEIGHTED room: stability={:.2f} — DIFFERENT tiles win at different phases.".format(r_phase['stability']))
        print()
        print("  FLEET IMPLICATION:")
        print("  Phase-weighted surfacing means rooms can discover UNEXPECTED connections")
        print("  by surfacing tiles at the RIGHT phase. A tile that loses at phase=0")
        print("  might win at phase=π/2 when a different keyword is dominant.")
        print()
        print("  This is the TRUE oscillation behavior — not resolution oscillating,")
        print("  but keyword weighting oscillating, which changes SURFACING.")
        print()
        print("  SPRINGBOARD: Test phase-weighted rooms with fleet coordination.")
        print("  Do agents discover more novel tile combinations this way?")
    else:
        print("  Both variants surface similar tiles regardless of phase.")
    
    os.makedirs(f"{WORKSPACE}/results", exist_ok=True)
    import json
    with open(f"{WORKSPACE}/results/abstraction_room_phase_weighting.json", 'w') as f:
        json.dump({
            'converging': r_conv,
            'phase_weighted': r_phase,
        }, f, indent=2, default=str)
    print(f"\nSaved to results/abstraction_room_phase_weighting.json")

if __name__ == "__main__":
    run()
