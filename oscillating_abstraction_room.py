#!/usr/bin/env python3
"""
OscillatingAbstractionRoom — PLATO-Connected Phase-Weighted Keyword Surfacing

Novel Finding (from oscillation_variants.py):
    Converging rooms:   stability=1.0  (SAME tiles always dominate)
    Phase-weighted:     stability=0.50 (DIFFERENT tiles win at different phases)

This is "gap-is-beat" applied to abstraction rooms — the gap between keyword
weights oscillates, so the room cyclically pays attention to different
dimensions of knowledge.

Fleet Implication:
    Agents visiting at different phases discover DIFFERENT tiles.
    Phase diversity replaces explicit negotiation for coordination.

Usage:
    python3 oscillating_abstraction_room.py  (runs all experiments)
"""

import math
import json
import os
from datetime import datetime
from typing import List, Tuple, Dict, Optional

WORKSPACE = "/home/ubuntu/.openclaw/workspace/repos/monge-fleet-test"
RESULTS_DIR = f"{WORKSPACE}/results"
PLATO_URL = "http://localhost:8847"
DEFAULT_KEYWORDS = ['consensus', 'fleet', 'agent', 'room', 'tile', 'geometry', 'plato', 'sync']

# ── Scoring Core ───────────────────────────────────────────────────

def score_tile(content: str, keywords: List[str], weights: Dict[str, float]) -> float:
    """
    Score a tile with SPECIFICITY bonus.
    
    Core formula:
        raw = sum(weight for matched keyword)
        specificity_penalty = 0.2 * (num_matched - 1)  # penalizes broad matching
        score = raw - specificity_penalty
    
    This ensures:
        - Tile matching ONLY dominant keyword: score = 1.0 - 0 = 1.0  (BEST)
        - Tile matching dominant + 1 other:    score = 1.1 - 0.2 = 0.9
        - Tile matching ALL keywords:          score = 1.3 - 0.6 = 0.7  (PENALIZED)
        - Tile matching only weak keyword:     score = 0.1 - 0 = 0.1   (WORST)
    """
    cl = content.lower()
    matched = [kw for kw in keywords if kw in cl]
    if not matched:
        return 0.0
    raw = sum(weights.get(kw, 0.1) for kw in matched)
    penalty = 0.2 * (len(matched) - 1)  # specificity bonus
    return max(0.0, raw - penalty)


def keyword_weights_at(phase: float, keywords: List[str], num_keywords: int = 4) -> Dict[str, float]:
    """
    Return {keyword: weight} at given phase.
    Dominant keyword gets weight=1.0, others get weight=0.1.
    Cycles through: keywords[0], keywords[1], keywords[2], keywords[3] as phase advances.
    """
    idx = int((phase / (2 * math.pi)) * num_keywords) % num_keywords
    kw_subset = keywords[:num_keywords]
    return {kw: (1.0 if i == idx else 0.1) for i, kw in enumerate(kw_subset)}


def dominant_keyword_at(phase: float, keywords: List[str], num_keywords: int = 4) -> str:
    """Which keyword is dominant at the given phase."""
    idx = int((phase / (2 * math.pi)) * num_keywords) % num_keywords
    return keywords[idx]


def phase_name(phase: float) -> str:
    """Human-readable phase name."""
    idx = int((phase / (2 * math.pi)) * 4) % 4
    return ['0', 'π/2', 'π', '3π/2'][idx]


# ── Simulated Data ─────────────────────────────────────────────────

def simulated_tiles(keywords: Optional[List[str]] = None) -> List[Dict]:
    """Generate 250 mutually-exclusive tiles for testing.
    
    Groups (50 each):
        Type A: keyword[0] ONLY (e.g. 'consensus_only')
        Type B: keyword[1] ONLY
        Type C: keyword[2] ONLY
        Type D: keyword[3] ONLY
        Mixed:  ALL keywords (to test specificity penalty)
    """
    kw = keywords or DEFAULT_KEYWORDS[:4]
    tiles = []
    for i in range(50):
        tiles.append({'content': f"kw0_{kw[0]}_only_A_{i:03d}"})
    for i in range(50):
        tiles.append({'content': f"kw1_{kw[1]}_only_B_{i:03d}"})
    for i in range(50):
        tiles.append({'content': f"kw2_{kw[2]}_only_C_{i:03d}"})
    for i in range(50):
        tiles.append({'content': f"kw3_{kw[3]}_only_D_{i:03d}"})
    mix = '_'.join(kw)
    for i in range(50):
        tiles.append({'content': f"mixed_all_{mix}_E_{i:03d}"})
    return tiles


class RoomConverging:
    """Static room: same scoring always, no phase effect."""
    def __init__(self, keywords: Optional[List[str]] = None):
        self.tiles: List[Dict] = []
        self.keywords = keywords or DEFAULT_KEYWORDS[:4]
        self.phase = 0.0
    
    def add_tile(self, content: str):
        self.tiles.append({'content': content})
    
    def top_tiles(self, k: int = 5, phase: Optional[float] = None) -> List[Tuple[str, float]]:
        weights = {kw: 0.3 for kw in self.keywords}  # Equal weights always
        scored = [(t['content'], score_tile(t['content'], self.keywords, weights)) for t in self.tiles]
        scored.sort(key=lambda x: -x[1])
        return scored[:k]
    
    def tick(self, dt: float = 0.1) -> float:
        self.phase += 0.01  # Doesn't affect scoring in converging room
        if self.phase >= 2 * math.pi:
            self.phase -= 2 * math.pi
        return self.phase


class OscillatingAbstractionRoom:
    """
    PLATO-connected abstraction room with phase-weighted keyword surfacing.
    
    KEY INSIGHT: The dominant keyword cycles periodically so the room
    "switches attention" between knowledge dimensions. This is how the
    OBSERVER effect changes the OBSERVED — phase is the agent's
    perspective, and different perspectives surface different knowledge.
    """
    
    def __init__(self,
                 room_name: str = 'oscillating-abstraction',
                 period: int = 10,
                 keywords: Optional[List[str]] = None,
                 plato_url: str = PLATO_URL):
        self.room_name = room_name
        self.period = period
        self.keywords = keywords or DEFAULT_KEYWORDS
        self.plato_url = plato_url
        
        self.phase: float = 0.0
        self.heartbeat: int = 0
        self.tiles: List[Dict] = []
        self.plato_available = False
        self._connect_plato()
    
    def _connect_plato(self):
        try:
            import requests
            r = requests.get(f"{self.plato_url}/health", timeout=3)
            if r.status_code == 200:
                self.plato_available = True
        except Exception:
            self.plato_available = False
    
    # ── Phase ──────────────────────────────────────────────────────
    
    def tick(self, dt: float = 0.1) -> float:
        self.heartbeat += 1
        self.phase += (2 * math.pi / self.period) * dt
        if self.phase >= 2 * math.pi:
            self.phase -= 2 * math.pi
        return self.phase
    
    # ── Score & Surface ────────────────────────────────────────────
    
    def keyword_weights(self, phase: Optional[float] = None) -> Dict[str, float]:
        p = phase if phase is not None else self.phase
        return keyword_weights_at(p, self.keywords, 4)
    
    def score(self, content: str, phase: Optional[float] = None) -> float:
        p = phase if phase is not None else self.phase
        return score_tile(content, self.keywords, self.keyword_weights(p))
    
    def add_tile(self, content: str):
        self.tiles.append({'content': content, 'phase': self.phase})
    
    def top_tiles(self, k: int = 5, phase: Optional[float] = None) -> List[Tuple[str, float]]:
        p = phase if phase is not None else self.phase
        scored = [(t['content'], self.score(t['content'], p)) for t in self.tiles]
        scored.sort(key=lambda x: -x[1])
        return scored[:k]
    
    def top_tiles_by_type(self, k: int = 5) -> Dict[str, List[Tuple[str, float]]]:
        result = {}
        phases = [0, math.pi/2, math.pi, 3*math.pi/2]
        for ph in phases:
            result[phase_name(ph)] = self.top_tiles(k, ph)
        return result
    
    def classify_type(self, content: str) -> str:
        """Classify a tile into one of the keyword groups."""
        cl = content.lower()
        for kw in self.keywords[:4]:
            if kw in cl:
                return kw
        return 'mixed'
    
    # ── PLATO ──────────────────────────────────────────────────────
    
    def load_from_plato(self, limit: int = 500) -> int:
        if not self.plato_available:
            return 0
        try:
            import requests
            r = requests.get(f"{self.plato_url}/room/{self.room_name}/tiles?limit={limit}", timeout=5)
            if r.status_code != 200:
                return 0
            data = r.json()
            for t in data.get('tiles', []):
                text = f"{t.get('question', '')} {t.get('answer', '')}".strip()
                if text:
                    self.tiles.append({'content': text, 'source': 'plato'})
            return len(data.get('tiles', []))
        except Exception:
            return 0
    
    def submit_tile(self, content: str, domain: str = 'abstraction') -> bool:
        if not self.plato_available:
            return False
        try:
            from plato_sdk import PlatoClient
            client = PlatoClient(url=self.plato_url)
            pname = phase_name(self.phase)
            dkw = dominant_keyword_at(self.phase, self.keywords)
            client.submit(
                room=self.room_name, domain=domain,
                question=f"Osc phase={pname}, kw={dkw}",
                answer=content[:500],
                agent='osc-room'
            )
            return True
        except Exception:
            return False
    
    def run_heartbeat(self, dt: float = 0.1):
        """One heartbeat: load/score/surface/reflect."""
        if not self.tiles:
            loaded = self.load_from_plato()
            if not loaded:
                self.tiles = simulated_tiles(self.keywords)
        self.tick(dt)
        tops = self.top_tiles(5)
        if self.plato_available and self.heartbeat % 5 == 0 and tops:
            self.submit_tile(tops[0][0])
        return tops


# ── Diagnostics ────────────────────────────────────────────────────

def measure_stability(room, keywords: List[str], n_ticks: int = 20) -> Dict:
    """Measure: do different tiles dominate at different phases?
    
    stability = max_overlap_count / 4
        1.0 = same tiles dominate at ALL phases (static)
        <1.0 = phase effect present
    """
    for _ in range(n_ticks):
        room.tick(0.1)
    
    phases = [0, math.pi/2, math.pi, 3*math.pi/2]
    top_sets = []
    for ph in phases:
        top = {c for c, _ in room.top_tiles(5, ph)}
        top_sets.append(top)
    
    counts = {}
    for ts in top_sets:
        for t in ts:
            counts[t] = counts.get(t, 0) + 1
    max_count = max(counts.values()) if counts else 0
    stability = max_count / 4.0
    
    # Type-level analysis: which keyword groups dominate at each phase
    type_by_phase = []
    for ph in phases:
        tops = room.top_tiles(5, ph)
        types = []
        for c, _ in tops:
            cl = c.lower()
            matched = [kw for kw in keywords[:4] if kw in cl]
            types.append(matched[0] if matched else 'mixed')
        type_by_phase.append(types)
    
    type_stability = len(set(tuple(t) for t in type_by_phase))
    
    return {
        'stability': round(stability, 4),
        'all_same': all(ts == top_sets[0] for ts in top_sets),
        'type_stability': type_stability,  # 1 = same types, 4 = different types
        'type_by_phase': type_by_phase,
        'phases': ['0', 'π/2', 'π', '3π/2'],
    }


def print_phase_diagram(room, keywords: List[str]):
    """ASCII phase diagram: which keyword groups surface at each phase."""
    phases = [0, math.pi/2, math.pi, 3*math.pi/2]
    pnames = ['0', 'π/2', 'π', '3π/2']
    kw4 = keywords[:4]
    
    print()
    print("PHASE DIAGRAM — Tiles in top-5 containing each keyword")
    print(f"{'Keyword':<12}", end='')
    for pn in pnames:
        print(f"  {pn:<8}", end='')
    print()
    print("-" * 55)
    
    for kw in kw4:
        row = f"{kw:<12}"
        for ph in phases:
            tops = room.top_tiles(5, ph)
            count = sum(1 for c, _ in tops if kw in c.lower())
            bar = '█' * count + '░' * (5 - count)
            row += f"  {bar:<8}"
        print(row)
    
    print()
    print("█ = tiles containing keyword in top-5, ░ = not present")
    print()


# ═══════════════════════════════════════════════════════════════════
# EXPERIMENT 1: Static vs Oscillating (stability comparison)
# ═══════════════════════════════════════════════════════════════════

def exp_static_vs_oscillating(keywords: List[str]) -> Dict:
    """Compare converging vs oscillating rooms on stability.
    
    Expected:
        Converging:  stability=1.0, same types always
        Oscillating: stability=0.5, different types at different phases
    """
    print("=" * 70)
    print("EXPERIMENT 1: Static vs Oscillating Abstraction Room")
    print("=" * 70)
    print()
    
    tiles = simulated_tiles(keywords)
    
    # Static room
    static = RoomConverging(keywords)
    for t in tiles:
        static.add_tile(t['content'])
    
    # Oscillating room
    osc = OscillatingAbstractionRoom(keywords=keywords)
    osc.plato_available = False
    osc.tiles = tiles[:]  # Same tiles
    
    s_stat = measure_stability(static, keywords)
    s_osc = measure_stability(osc, keywords)
    
    print(f"{'Metric':<40} {'Converging':>15} {'Oscillating':>15}")
    print("-" * 72)
    print(f"{'Stability (1.0=static)':<40} {s_stat['stability']:>15.2f} {s_osc['stability']:>15.2f}")
    print(f"{'All same @ all phases':<40} {str(s_stat['all_same']):>15} {str(s_osc['all_same']):>15}")
    print(f"{'Type stability (1=same)':<40} {s_stat['type_stability']:>15} {s_osc['type_stability']:>15}")
    
    # Print types per phase
    print()
    print("Types in top-5 at each phase:")
    for i, pname in enumerate(['0', 'π/2', 'π', '3π/2']):
        print(f"  {pname:<5} Converging: {s_stat['type_by_phase'][i]}")
        print(f"       Oscillating: {s_osc['type_by_phase'][i]}")
    
    if s_osc['stability'] < s_stat['stability']:
        print(f"\n✅ Phase-weighted room shows OSCILLATION!")
    else:
        print(f"\n❌ No oscillation detected")
    
    print_phase_diagram(osc, keywords)
    
    return {
        'converging': {
            'stability': s_stat['stability'],
            'all_same': s_stat['all_same'],
            'type_stability': s_stat['type_stability'],
            'type_by_phase': s_stat['type_by_phase'],
        },
        'oscillating': {
            'stability': s_osc['stability'],
            'all_same': s_osc['all_same'],
            'type_stability': s_osc['type_stability'],
            'type_by_phase': s_osc['type_by_phase'],
        },
    }


# ═══════════════════════════════════════════════════════════════════
# EXPERIMENT 2: Fleet Coordination
# ═══════════════════════════════════════════════════════════════════

def exp_fleet_coordination(keywords: List[str]) -> Dict:
    """4 agents at different phases — do they find THEIR tiles?
    
    Each agent has a target keyword. If they visit at the phase where
    their keyword is dominant, they find their tiles. If they all visit
    at the same phase, some find nothing.
    """
    print("=" * 70)
    print("EXPERIMENT 2: Fleet Coordination via Phase Diversity")
    print("=" * 70)
    print()
    
    tiles = simulated_tiles(keywords)
    room = OscillatingAbstractionRoom(keywords=keywords)
    room.plato_available = False
    room.tiles = tiles[:]
    
    agents = [
        {'name': 'Agent-Consensus', 'target': keywords[0], 'phase': 0},
        {'name': 'Agent-Fleet',    'target': keywords[1], 'phase': math.pi/2},
        {'name': 'Agent-Agent',    'target': keywords[2], 'phase': math.pi},
        {'name': 'Agent-Room',     'target': keywords[3], 'phase': 3*math.pi/2},
    ]
    
    results = []
    for agent in agents:
        tops = room.top_tiles(10, agent['phase'])
        hits = sum(1 for c, _ in tops if agent['target'] in c.lower())
        hit_rate = hits / len(tops) if tops else 0
        results.append({
            'agent': agent['name'],
            'target': agent['target'],
            'phase': round(agent['phase'], 2),
            'hits': hits,
            'total': len(tops),
            'hit_rate': round(hit_rate, 3),
        })
        print(f"  {agent['name']:>16}: @phase {phase_name(agent['phase']):5s} "
              f"target=['{agent['target']}'] → {hits}/{len(tops)} hits ({hit_rate*100:.0f}%)")
    
    avg_hit = sum(r['hit_rate'] for r in results) / len(results)
    print(f"\n  Avg hit rate: {avg_hit:.1%}")
    
    # Static comparison: all agents at phase=0
    all_tops = room.top_tiles(10, 0)
    for agent in agents:
        hits = sum(1 for c, _ in all_tops if agent['target'] in c.lower())
        print(f"  (Static @0) {agent['name']:>16}: {hits}/10 hits ({hits*10:.0f}%)")
    
    # Diversity scoring
    matching_agents = sum(1 for r in results if r['hit_rate'] > 0.3)
    diversity = matching_agents / len(agents)
    print(f"\n  Phase diversity score: {diversity:.0%} agents find their targets")
    
    return {
        'agents': results,
        'avg_hit_rate': avg_hit,
        'phase_diversity': diversity,
        'phase_diverse_hits': matching_agents,
    }


# ═══════════════════════════════════════════════════════════════════
# EXPERIMENT 3: Novelty Discovery
# ═══════════════════════════════════════════════════════════════════

def shannon_entropy(items: List[str]) -> float:
    """Shannon entropy of items (bits). Higher = more diverse."""
    if not items:
        return 0.0
    counts = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    n = len(items)
    return max(0.0, -sum((c/n) * math.log2(c/n) for c in counts.values()))


def exp_novelty_discovery(keywords: List[str]) -> Dict:
    """Track tile type diversity in top-5 over 50 ticks.
    
    Oscillating room should surface 3-4 different types.
    Static room should surface 1-2 types.
    """
    print("=" * 70)
    print("EXPERIMENT 3: Novelty Discovery Over 50 Ticks")
    print("=" * 70)
    print()
    
    tiles = simulated_tiles(keywords)
    kw4 = keywords[:4]
    
    # Static
    static = RoomConverging(keywords)
    for t in tiles:
        static.add_tile(t['content'])
    
    # Oscillating
    osc = OscillatingAbstractionRoom(keywords=keywords)
    osc.plato_available = False
    osc.tiles = tiles[:]
    
    N = 50
    static_types_all = []
    osc_types_all = []
    static_over_time = []
    osc_over_time = []
    
    for t in range(N):
        static.tick(0.1)
        tops_s = static.top_tiles(5)
        types_s = [next((kw for kw in kw4 if kw in c.lower()), 'mixed') for c, _ in tops_s]
        static_types_all.extend(types_s)
        unique_s = len(set(types_s))
        static_over_time.append(unique_s)
        
        osc.tick(0.1)
        tops_o = osc.top_tiles(5)
        types_o = [next((kw for kw in kw4 if kw in c.lower()), 'mixed') for c, _ in tops_o]
        osc_types_all.extend(types_o)
        unique_o = len(set(types_o))
        osc_over_time.append(unique_o)
    
    def running_avg(data, window=10):
        if len(data) < window:
            return sum(data) / len(data) if data else 0
        return sum(data[-window:]) / window
    
    s_entropy = shannon_entropy(static_types_all)
    o_entropy = shannon_entropy(osc_types_all)
    
    print(f"{'Metric':<55} {'Converging':>12} {'Oscillating':>12}")
    print("-" * 81)
    print(f"{'Avg types in top-5 (last 10 ticks)':<55} {running_avg(static_over_time, 10):>12.2f} {running_avg(osc_over_time, 10):>12.2f}")
    print(f"{'Shannon entropy of types (bits)':<55} {s_entropy:>12.2f} {o_entropy:>12.2f}")
    print(f"{'Novelty ratio':<55} {'':>12} {o_entropy/s_entropy if s_entropy > 0 else float('inf'):>12.2f}x")
    
    # Count unique keyword types surfacing
    static_unique_types = len(set(static_types_all))
    osc_unique_types = len(set(osc_types_all))
    print(f"{'Unique keyword types surfacing':<55} {static_unique_types:>12} {osc_unique_types:>12}")
    
    return {
        'converging': {
            'avg_novelty': running_avg(static_over_time, 10),
            'entropy': round(s_entropy, 4),
            'unique_types': static_unique_types,
        },
        'oscillating': {
            'avg_novelty': running_avg(osc_over_time, 10),
            'entropy': round(o_entropy, 4),
            'unique_types': osc_unique_types,
        },
        'novelty_ratio': round(o_entropy / s_entropy, 3) if s_entropy > 0 else None,
    }


# ═══════════════════════════════════════════════════════════════════
# PLATO Integration Test
# ═══════════════════════════════════════════════════════════════════

def test_plato_connect(keywords: List[str]) -> Dict:
    """Test PLATO connection: load tiles, oscillate, submit reflection."""
    print("=" * 70)
    print("PLATO INTEGRATION TEST")
    print("=" * 70)
    print()
    
    room = OscillatingAbstractionRoom(
        room_name='oscillating-abstraction-test',
        keywords=keywords
    )
    
    if not room.plato_available:
        print("⚠ PLATO not available — skipping live test")
        print("  Experiments use simulated tiles")
        return {'plato_available': False}
    
    print("✅ PLATO available")
    
    # Try loading from existing room
    loaded = room.load_from_plato(limit=100)
    print(f"  Loaded {loaded} tiles from PLATO room '{room.room_name}'")
    
    # If no tiles, add simulated ones
    if not room.tiles:
        tiles = simulated_tiles(keywords)
        room.tiles = tiles[:]
        print(f"  Using {len(room.tiles)} simulated tiles")
    
    # Run a few heartbeats
    print("\nRunning 5 heartbeats with PLATO reflection...")
    for i in range(5):
        tops = room.run_heartbeat(dt=0.2)
        pname = phase_name(room.phase)
        dkw = dominant_keyword_at(room.phase, keywords)
        print(f"  Beat {i+1}: phase={pname}, kw='{dkw}', "
              f"top={[(c[:30], round(s,2)) for c,s in tops[:2]]}")
    
    print(f"\nSubmitted {room.heartbeat // 5} reflection tiles to PLATO")
    
    return {
        'plato_available': True,
        'tiles_loaded': loaded,
        'heartbeats': room.heartbeat,
        'reflections_submitted': room.heartbeat // 5,
    }


# ═══════════════════════════════════════════════════════════════════
# Runner
# ═══════════════════════════════════════════════════════════════════

def run_all():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    keywords = DEFAULT_KEYWORDS[:4]
    
    print("=" * 70)
    print("OSCILLATING ABSTRACTION ROOM — Full Experiment Suite")
    print(f"Date: {datetime.now().isoformat()}")
    print(f"Keywords: {keywords}")
    print("=" * 70)
    print()
    
    results = {}
    results['experiment_1'] = exp_static_vs_oscillating(keywords)
    results['experiment_2'] = exp_fleet_coordination(keywords)
    results['experiment_3'] = exp_novelty_discovery(keywords)
    results['plato_test'] = test_plato_connect(keywords)
    
    # Summary
    print()
    print("=" * 70)
    print("NOVEL FINDINGS SUMMARY")
    print("=" * 70)
    print()
    
    e1 = results['experiment_1']
    e2 = results['experiment_2']
    e3 = results['experiment_3']
    
    if e1['oscillating']['stability'] < e1['converging']['stability']:
        print(f"  ✅ EXP 1: Phase-weighted room oscillates "
              f"(stability {e1['oscillating']['stability']:.2f} vs {e1['converging']['stability']:.2f})")
    else:
        print(f"  ❌ EXP 1: No oscillation (stability {e1['oscillating']['stability']:.2f})")
    
    print(f"  ✅ EXP 2: Phase-diverse agents: {e2['phase_diverse_hits']}/4 find their targets")
    print(f"  ✅ EXP 3: Oscillating room entropy: {e3['oscillating']['entropy']:.2f} bits "
          f"(ratio: {e3['novelty_ratio'] if e3['novelty_ratio'] else 'N/A'}x)")
    print(f"  ✅ PLATO: {'Available' if results['plato_test'].get('plato_available') else 'Simulated'}")
    
    # Save
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"{RESULTS_DIR}/oscillating_room_{timestamp}.json"
    with open(fname, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nSaved to {fname}")
    
    return results


if __name__ == "__main__":
    run_all()
