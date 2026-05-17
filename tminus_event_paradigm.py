#!/usr/bin/env python3
"""
T-MINUS-EVENT PARADIGM — Phase-Weighted Snap Positioning

Core insight (from abstraction_room.py metal benchmarks):
  "As close as possible" = snap to predicted position
  Prediction requires knowing which phase the room will be in at T

The paradigm:
  Agent observes room at time t. Room phase = θ(t).
  Agent predicts phase at time t+1: θ̂(t+1) = θ(t) + ω·Δt
  Agent positions itself for phase θ̂(t+1) — NOT for θ(t)

This is "gap-is-beat" applied to agent positioning:
  The beat (phase) you arrive at determines which tiles surface.
  You don't position for WHERE the room IS, you position for WHERE it's GOING.

Architecture:
  - PLATO room has oscillation_period and current phase
  - Agents observe room phase, predict next phase
  - At each phase, different keyword weights → different tiles surface
  - Agent's tile contribution matches the PREDICTED phase's dominant keyword

This is the OPPOSITE of convergence:
  Converging rooms: same tiles always win (static)
  Phase-weighted rooms: different tiles win at different phases (dynamic)
  T-minus-event: agent positions for the dynamic next-phase, not static now

Testing:
  Compare fleet coordination outcomes:
    Static room: agents contribute tiles with fixed keyword weights
    Phase-weighted room: agents contribute tiles matching predicted phase
  Measure: cross-room invariant tiles discovered, novel tile combinations
"""

import math
import time
import random

WORKSPACE = "/home/ubuntu/.openclaw/workspace/repos/monge-fleet-test"


class TMinusRoom:
    """
    A PLATO-style room that oscillates through phases.
    At each phase, different keyword weights dominate.
    
    Agents observe current phase, predict next phase, 
    and contribute tiles that match the predicted phase's keywords.
    """
    
    KEYWORDS = ['consensus', 'fleet', 'agent', 'room', 'tile', 'geometry']
    PERIOD_SECONDS = 10.0  # Full oscillation cycle
    
    def __init__(self, name):
        self.name = name
        self.phase = 0.0  # radians, 0 to 2π
        self.tiles = []  # list of {'content': str, 'phase_contributed': float, 'score': float}
        self.heartbeat = 0
        self.time_elapsed = 0.0
    
    def current_phase_index(self):
        """Which keyword is dominant RIGHT NOW (0-3)."""
        # 4 phases mapped to 4 keyword pairs
        idx = int((self.phase / (2 * math.pi)) * 4) % 4
        return idx
    
    def predicted_phase_index(self, dt=1.0):
        """Which keyword will be dominant at t+dt."""
        future_phase = self.phase + (2 * math.pi / self.PERIOD_SECONDS) * dt
        future_phase = future_phase % (2 * math.pi)
        idx = int((future_phase / (2 * math.pi)) * 4) % 4
        return idx
    
    def keyword_weights(self, phase):
        """Keyword weights at a given phase."""
        idx = int((phase / (2 * math.pi)) * 4) % 4
        weights = [0.1] * len(self.KEYWORDS)
        # Map phase index to keyword index
        kw_idx = idx * 1  # 0→kw0, 1→kw1, 2→kw2, 3→kw3
        if kw_idx < len(self.KEYWORDS):
            weights[kw_idx] = 1.0
        return weights
    
    def score_tile(self, content, phase):
        """Score a tile at given phase with phase-dependent weights."""
        cl = content.lower()
        kw_matches = [1 if kw in cl else 0 for kw in self.KEYWORDS]
        weights = self.keyword_weights(phase)
        return sum(kw_matches[i] * weights[i] for i in range(len(self.KEYWORDS)))
    
    def add_tile(self, content, phase_contributed):
        """Add a tile at a specific phase (when agent contributed it)."""
        score = self.score_tile(content, phase_contributed)
        self.tiles.append({
            'content': content,
            'phase_contributed': phase_contributed,
            'score': score,
            'arrival_heartbeat': self.heartbeat
        })
        if len(self.tiles) > 10000:
            self.tiles.pop(0)
    
    def top_tiles(self, k=10, at_phase=None):
        """Get top-k tiles scored at current phase (or specified phase)."""
        if at_phase is None:
            at_phase = self.phase
        scored = [(t['content'], t['score'], self.score_tile(t['content'], at_phase)) 
                   for t in self.tiles]
        # Re-score all tiles at the viewing phase
        scored.sort(key=lambda x: -x[2])
        return scored[:k]
    
    def tick(self, dt=1.0):
        """Advance room by dt seconds."""
        self.heartbeat += 1
        self.time_elapsed += dt
        self.phase += (2 * math.pi / self.PERIOD_SECONDS) * dt
        if self.phase >= 2 * math.pi:
            self.phase -= 2 * math.pi
    
    def phase_degrees(self):
        return self.phase * 180.0 / math.pi


class Agent:
    """
    An agent that positions for predicted phase (T-minus-event).
    
    Strategy:
    1. Observe current room phase
    2. Predict next phase (current + ω·dt)
    3. Generate tile matching predicted phase's dominant keyword
    4. Contribute tile to room
    """
    
    def __init__(self, name, strategy='predict'):
        self.name = name
        self.strategy = strategy  # 'predict' or 'static'
    
    def keyword_for_phase_index(self, idx):
        """Map phase index (0-3) to keyword pair."""
        pairs = [
            ('consensus', 'fleet'),      # phase 0: keywords 0,1
            ('agent', 'room'),          # phase 1: keywords 2,3  
            ('tile', 'geometry'),       # phase 2: keywords 4,5
            ('consensus', 'agent'),     # phase 3: mixed
        ]
        return pairs[idx % 4]
    
    def generate_tile(self, predicted_phase_idx):
        """Generate a tile for the predicted phase's dominant keyword."""
        kw1, kw2 = self.keyword_for_phase_index(predicted_phase_idx)
        # Generate content matching predicted phase
        content = f"{kw1}_{kw2}_{random.randint(0, 99)}"
        return content
    
    def act(self, room):
        """
        Agent acts in room based on strategy.
        predict: contributes tile for predicted phase
        static: contributes tile for current phase (no prediction)
        """
        if self.strategy == 'predict':
            predicted_idx = room.predicted_phase_index(dt=1.0)
            content = self.generate_tile(predicted_idx)
        else:  # static
            current_idx = room.current_phase_index()
            content = self.generate_tile(current_idx)
        
        room.add_tile(content, room.phase)
        return content


def simulate_fleet(n_agents=5, n_ticks=50, strategy='predict'):
    """
    Simulate a fleet of agents interacting via T-minus-event paradigm.
    
    Compare 'predict' vs 'static' strategies:
    - predict: agents position for predicted phase (T-minus-event)
    - static: agents position for current phase (no prediction)
    
    Measure: top-10 tiles variety, keyword coverage, novel combinations
    """
    room = TMinusRoom(f"fleet_{strategy}")
    agents = [Agent(f"agent_{i}", strategy=strategy) for i in range(n_agents)]
    
    tick_log = []
    
    for tick in range(n_ticks):
        # Each agent acts
        for agent in agents:
            tile_content = agent.act(room)
        
        # Advance room
        room.tick(dt=1.0)
        
        # Log state
        if tick % 10 == 0:
            top = room.top_tiles(5, at_phase=room.phase)
            top_contents = [t[0] for t in top]
            phase_idx = room.current_phase_index()
            kw1, kw2 = agents[0].keyword_for_phase_index(phase_idx)
            
            tick_log.append({
                'tick': tick,
                'phase_deg': room.phase_degrees(),
                'phase_idx': phase_idx,
                'dominant_kw': f"{kw1}_{kw2}",
                'top_tiles': top_contents
            })
    
    # Final analysis
    # Count how many tiles of each type exist in room
    keyword_counts = {kw: 0 for kw in TMinusRoom.KEYWORDS}
    for t in room.tiles:
        for kw in TMinusRoom.KEYWORDS:
            if kw in t['content']:
                keyword_counts[kw] += 1
    
    # Measure variety: how many different tile types in top-10 at different phases
    phase_tile_sets = {}
    for phase_deg in [0, 90, 180, 270]:
        phase = phase_deg * math.pi / 180.0
        top = room.top_tiles(10, at_phase=phase)
        phase_tile_sets[phase_deg] = set(t[0] for t in top)
    
    all_top_tiles = set()
    for ts in phase_tile_sets.values():
        all_top_tiles |= ts
    
    variety_score = len(all_top_tiles) / 10.0  # 1.0 = all different tiles at different phases
    
    return {
        'strategy': strategy,
        'n_agents': n_agents,
        'n_ticks': n_ticks,
        'n_tiles': len(room.tiles),
        'keyword_counts': keyword_counts,
        'phase_tile_sets': {str(k): list(v) for k, v in phase_tile_sets.items()},
        'variety_score': variety_score,
        'tick_log': tick_log
    }


def run_comparison():
    print("=" * 70)
    print("T-MINUS-EVENT PARADIGM — Phase-Weighted Agent Positioning")
    print("=" * 70)
    print()
    print("Hypothesis: Agents that position for PREDICTED phase discover")
    print("more varied tile combinations than agents that position for")
    print("CURRENT phase (static).")
    print()
    print("Setup: 5 agents, 50 ticks, 4 phase angles")
    print()
    
    print("RUNNING 'predict' strategy...")
    r_predict = simulate_fleet(n_agents=5, n_ticks=50, strategy='predict')
    
    print("RUNNING 'static' strategy...")
    r_static = simulate_fleet(n_agents=5, n_ticks=50, strategy='static')
    
    print()
    print(f"{'Strategy':<15} {'Variety Score':>15} {'Total Tiles':>12}")
    print("-" * 45)
    print(f"{'predict':<15} {r_predict['variety_score']:>15.2f} {r_predict['n_tiles']:>12}")
    print(f"{'static':<15} {r_static['variety_score']:>15.2f} {r_static['n_tiles']:>12}")
    
    print()
    print("KEYWORD COUNTS:")
    print(f"{'Keyword':<15} {'predict':>10} {'static':>10}")
    print("-" * 38)
    for kw in TMinusRoom.KEYWORDS:
        pc = r_predict['keyword_counts'][kw]
        sc = r_static['keyword_counts'][kw]
        print(f"{kw:<15} {pc:>10} {sc:>10}")
    
    print()
    print("TOP-5 TILES AT 4 PHASES (predict):")
    print(f"{'Phase':<10} {'Top Tiles':<55}")
    print("-" * 68)
    for phase_deg in [0, 90, 180, 270]:
        tiles = r_predict['phase_tile_sets'][str(phase_deg)][:3]
        tiles_str = ','.join(sorted(tiles)[:3])
        print(f"{phase_deg:<10} {tiles_str:<55}")
    
    print()
    print("TOP-5 TILES AT 4 PHASES (static):")
    print(f"{'Phase':<10} {'Top Tiles':<55}")
    print("-" * 68)
    for phase_deg in [0, 90, 180, 270]:
        tiles = r_static['phase_tile_sets'][str(phase_deg)][:3]
        tiles_str = ','.join(sorted(tiles)[:3])
        print(f"{phase_deg:<10} {tiles_str:<55}")
    
    print()
    print("=" * 70)
    print("NOVEL FINDING:")
    print("=" * 70)
    
    improvement = r_predict['variety_score'] - r_static['variety_score']
    
    if r_predict['variety_score'] > r_static['variety_score']:
        print(f"  PREDICT strategy produces {improvement:.1f}x more variety!")
        print(f"  Agents that position for predicted phase surface DIFFERENT tiles")
        print(f"  at different phases. Static agents surface same tiles.")
        print()
        print("  FLEET IMPLICATION:")
        print("  T-minus-event paradigm works! Agents that predict phase and")
        print("  position accordingly discover more varied tile combinations.")
        print("  This is 'gap-is-beat' at the agent level: the interval between")
        print("  phases IS the positioning window, not the current phase.")
    elif r_predict['variety_score'] < r_static['variety_score']:
        print(f"  STATIC strategy produces {-improvement:.1f}x more variety!")
        print(f"  Agents that position for current phase outperform predicted phase agents.")
        print()
        print("  REVERSAL: Predicting phase HURTS variety. Agents should position")
        print("  for CURRENT phase, not predicted phase. The room is not predictable.")
    else:
        print("  Both strategies produce equal variety.")
    
    # Save results
    import json, os
    os.makedirs(f"{WORKSPACE}/results", exist_ok=True)
    
    result = {
        'predict': r_predict,
        'static': r_static,
        'improvement': improvement,
        'finding': 'predict_better' if improvement > 0 else 'static_better' if improvement < 0 else 'equal'
    }
    
    with open(f"{WORKSPACE}/results/tminus_event_paradigm.json", 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    print()
    print(f"Saved to results/tminus_event_paradigm.json")
    
    return result


if __name__ == "__main__":
    run_comparison()