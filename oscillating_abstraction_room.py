#!/usr/bin/env python3
"""
OscillatingAbstractionRoom — PLATO-connected phase-weighted room

Confirmed: phase-weighted keyword surfacing works (stability=0.50 vs converging=1.0).
Now: connect it to real PLATO room server.

The OscillatingAbstractionRoom:
- Posts tiles to PLATO room
- Reads room state (other agents' tiles)
- Phase-weighted surfacing: different tiles surface at different phases
- Oscillation period configurable (default 10 heartbeats)

Test: does phase-weighted surfacing produce BETTER fleet coordination
than static ordering? Compare to regular PLATO room.

Casey's directive: show all the work. We don't know what's important yet.
"""

import time
import math
import random
import json
import os
import sys

# PLATO SDK import
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/repos/plato-sdk/src')
try:
    from plato_client import PlatoClient
    HAS_PLATO = True
except ImportError:
    HAS_PLATO = False
    print("WARNING: plato_client not installed — running in simulation mode")

WORKSPACE = "/home/ubuntu/.openclaw/workspace/repos/monge-fleet-test"


class OscillatingAbstractionRoom:
    """
    PLATO-connected AbstractionRoom with phase-weighted keyword surfacing.
    
    Key insight: at different phases, different keywords dominate.
    Agent tiles that match the CURRENT dominant keyword score highest.
    This is "gap-is-beat" at the room level.
    
    Architecture:
    - phase: 0 to 2π, advances with each heartbeat
    - period: full oscillation cycle length (default 10 heartbeats)
    - keyword_weights: phase determines which keywords are weighted high
    - surfacing: at each phase, tiles matching dominant keywords surface
    
    Testing:
    - Post tiles at various phases
    - Measure: do different tiles surface at different phases?
    - Compare to static room (no phase weighting)
    """
    
    KEYWORDS = ['consensus', 'fleet', 'agent', 'room', 'tile', 'geometry', 
                'desire', 'emergence', 'constraint', 'rigidity', 'coherence']
    
    def __init__(self, name, purpose, period=10.0, plato_client=None):
        self.name = name
        self.purpose = purpose
        self.period = period  # seconds for full oscillation cycle
        self.phase = 0.0  # radians
        self.heartbeat = 0
        self.time_elapsed = 0.0
        
        self.plato = plato_client
        self.room_name = f"osc-{name}"  # PLATO room name
        
        # Tile storage
        self.tiles = []  # {'content': str, 'phase_contributed': float, 'score': float}
        
        # Metrics
        self.metrics = {
            'phases_recorded': [],
            'tiles_by_phase': {},  # phase_idx -> list of tile contents
            'surfacing_variety': 0.0,
            'energy_history': []
        }
    
    def phase_index(self):
        """Which phase of the oscillation (0-3)."""
        return int((self.phase / (2 * math.pi)) * 4) % 4
    
    def dominant_keywords(self, phase=None):
        """Keywords that dominate at current phase."""
        if phase is None:
            phase = self.phase
        idx = int((phase / (2 * math.pi)) * 4) % 4
        
        # Map phase index to dominant keyword pairs
        pairs = [
            ('consensus', 'fleet', 'desire'),      # phase 0
            ('agent', 'room', 'emergence'),         # phase 1
            ('tile', 'geometry', 'constraint'),     # phase 2
            ('rigidity', 'coherence', 'fleet'),     # phase 3
        ]
        return pairs[idx % 4]
    
    def keyword_weights(self, phase=None):
        """Weight each keyword by phase (1.0 for dominant, 0.1 for others)."""
        if phase is None:
            phase = self.phase
        dominant = set(self.dominant_keywords(phase))
        return {kw: 1.0 if kw in dominant else 0.1 for kw in self.KEYWORDS}
    
    def score_tile(self, content, phase=None):
        """Score a tile at given phase with phase-dependent weights."""
        if phase is None:
            phase = self.phase
        cl = content.lower()
        weights = self.keyword_weights(phase)
        # Count weighted matches: each keyword match weighted by keyword's phase weight
        weighted_matches = sum(weights.get(kw, 0.1) for kw in self.KEYWORDS if kw in cl)
        # Normalize by total possible weight (sum of all keyword weights)
        total_weight = sum(weights.values())
        return weighted_matches / total_weight
    
    def add_tile(self, content, phase=None):
        """Add a tile at a specific phase."""
        if phase is None:
            phase = self.phase
        score = self.score_tile(content, phase)
        idx = self.phase_index()
        
        self.tiles.append({
            'content': content,
            'phase_contributed': phase,
            'phase_idx': idx,
            'score': score
        })
        
        # Track tiles by phase index
        if idx not in self.metrics['tiles_by_phase']:
            self.metrics['tiles_by_phase'][idx] = []
        self.metrics['tiles_by_phase'][idx].append(content)
        
        if len(self.tiles) > 10000:
            self.tiles.pop(0)
        
        return score
    
    def top_tiles(self, k=10, at_phase=None):
        """Get top-k tiles scored at specified phase (or current phase)."""
        if at_phase is None:
            at_phase = self.phase
        
        scored = [(t['content'], t['score'], self.score_tile(t['content'], at_phase)) 
                   for t in self.tiles]
        scored.sort(key=lambda x: -x[2])
        return scored[:k]
    
    def surfacing_variety(self):
        """Measure: how different are top-5 tiles at different phases?"""
        phase_sets = {}
        for phase_deg in [0, 90, 180, 270]:
            phase = phase_deg * math.pi / 180.0
            top = self.top_tiles(5, at_phase=phase)
            phase_sets[phase_deg] = set(t[0] for t in top)
        
        union = set()
        for ts in phase_sets.values():
            union |= ts
        
        # If all phases surface same tiles → variety=0
        # If each phase surfaces different tiles → variety=1
        if len(union) == 0:
            return 0.0
        return (len(union) - 5) / 5.0  # normalize to 0-1
    
    def tick(self, dt=1.0):
        """Advance room by dt seconds."""
        self.heartbeat += 1
        self.time_elapsed += dt
        self.phase += (2 * math.pi / self.period) * dt
        if self.phase >= 2 * math.pi:
            self.phase -= 2 * math.pi
        
        # Record metrics
        self.metrics['phases_recorded'].append({
            'heartbeat': self.heartbeat,
            'phase': self.phase,
            'phase_deg': self.phase * 180.0 / math.pi,
            'phase_idx': self.phase_index(),
            'dominant_kw': list(self.dominant_keywords())
        })
        
        return self.phase
    
    def post_to_plato(self):
        """Post current room state to PLATO room."""
        if not self.plato or not HAS_PLATO:
            return None
        
        try:
            # Create room if doesn't exist
            room_desc = {
                'name': self.room_name,
                'purpose': self.purpose,
                'phase': self.phase,
                'heartbeat': self.heartbeat,
                'period': self.period,
                'n_tiles': len(self.tiles)
            }
            
            result = self.plato.submit(
                room=self.room_name,
                domain='osc-abstraction',
                content=json.dumps(room_desc),
                tags=['osc-abstraction-room', f'phase-{self.phase_index()}']
            )
            return result
        except Exception as e:
            return {'error': str(e)}
    
    def summary(self):
        """Human-readable summary."""
        return {
            'name': self.name,
            'heartbeat': self.heartbeat,
            'phase_deg': round(self.phase * 180.0 / math.pi, 1),
            'phase_idx': self.phase_index(),
            'dominant_kw': self.dominant_keywords(),
            'n_tiles': len(self.tiles),
            'surfacing_variety': round(self.surfacing_variety(), 3),
            'tiles_by_phase': {str(k): len(v) for k, v in self.metrics['tiles_by_phase'].items()}
        }


def run_simulation(n_tiles=100, n_ticks=50, period=10.0):
    """
    Run OscillatingAbstractionRoom simulation.
    
    Test: can we confirm phase-weighted surfacing with real tile data?
    Measure variety_score: how different are top tiles at different phases?
    """
    print("=" * 70)
    print("OSCILLATING ABSTRACTION ROOM — PLATO-connected Simulation")
    print("=" * 70)
    print()
    print(f"Setup: {n_tiles} tiles, {n_ticks} ticks, period={period}s")
    print()
    
    room = OscillatingAbstractionRoom('fleet-test', 'fleet abstraction geometry', period=period)
    
    # Generate tiles with varying keyword content
    # Types: consensus, fleet, agent, room, tile, geometry, mixed
    keyword_sets = [
        ('consensus', 'fleet'),
        ('agent', 'room'),
        ('tile', 'geometry'),
        ('rigidity', 'coherence'),
        ('desire', 'emergence'),
    ]
    
    print("ADDING tiles...")
    for i in range(n_tiles):
        kw_type = i % len(keyword_sets)
        kw1, kw2 = keyword_sets[kw_type]
        
        # Randomly vary the phase at which tile is contributed
        tile_phase = (i % 4) * (math.pi / 2)  # phases: 0, π/2, π, 3π/2
        content = f"{kw1}_{kw2}_{i:03d}_content"
        
        room.phase = tile_phase  # Set room phase to tile's contribution phase
        room.add_tile(content)
    
    print(f"  Added {len(room.tiles)} tiles")
    print()
    
    print("RUNNING heartbeats...")
    for tick in range(n_ticks):
        room.tick(dt=1.0)
        
        if tick % 10 == 0:
            dom_kw = room.dominant_keywords()
            top = room.top_tiles(3)
            top_contents = [t[0] for t in top]
            print(f"  tick {tick:3}: phase={room.phase * 180 / math.pi:.0f}°  "
                  f"dominant={dom_kw}  top={top_contents[:2]}")
    
    print()
    print("SURFACING ANALYSIS:")
    print()
    
    variety = room.surfacing_variety()
    
    for phase_deg in [0, 90, 180, 270]:
        phase = phase_deg * math.pi / 180.0
        top = room.top_tiles(5, at_phase=phase)
        dom_kw = room.dominant_keywords(phase)
        top_contents = [t[0] for t in top]
        
        print(f"  phase={phase_deg:3d}°: dominant={dom_kw}")
        print(f"    top-5: {top_contents}")
        print()
    
    # Compare to static room
    print("COMPARISON: Oscillating vs Static room")
    print()
    
    static_room = OscillatingAbstractionRoom('static-test', 'static geometry', period=float('inf'))
    for t in room.tiles:
        static_room.tiles.append(t)
    
    static_variety = static_room.surfacing_variety()
    
    print(f"  Oscillating room variety: {variety:.3f}")
    print(f"  Static room variety:       {static_variety:.3f}")
    print()
    
    if variety > static_variety:
        print("RESULT: Oscillating room produces MORE surfacing variety!")
        print("  Phase-weighted surfacing surfaces different tiles at different phases.")
        print("  Static room surfaces same tiles regardless of phase.")
    elif variety == static_variety:
        print("RESULT: Both rooms produce equal variety (need more tiles or phases)")
    else:
        print("RESULT: Static room produces more variety (unexpected)")
    
    # Save results
    os.makedirs(f"{WORKSPACE}/results", exist_ok=True)
    result = {
        'room': room.summary(),
        'variety': variety,
        'static_variety': static_variety,
        'improvement': variety - static_variety,
        'phase_analysis': {
            str(deg): {
                'dominant_kw': list(room.dominant_keywords(deg * math.pi / 180)),
                'top_tiles': [t[0] for t in room.top_tiles(5, at_phase=deg * math.pi / 180)]
            }
            for deg in [0, 90, 180, 270]
        },
        'n_tiles': n_tiles,
        'n_ticks': n_ticks,
        'period': period
    }
    
    with open(f"{WORKSPACE}/results/oscillating_abstraction_room.json", 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    print(f"\nSaved to results/oscillating_abstraction_room.json")
    
    return result


def run_plato_live_test():
    """Test with real PLATO room server."""
    print("=" * 70)
    print("PLATO LIVE TEST")
    print("=" * 70)
    print()
    
    if not HAS_PLATO:
        print("PLATO SDK not available — skipping live test")
        print("Run simulation instead: python3 oscillating_abstraction_room.py --sim")
        return None
    
    client = PlatoClient(base_url="http://localhost:8847")
    
    # Test connection
    try:
        status = client.status()
        print(f"PLATO status: {status}")
    except Exception as e:
        print(f"PLATO connection failed: {e}")
        print("Is PLATO room server running on localhost:8847?")
        return None
    
    # Create oscillating room
    room = OscillatingAbstractionRoom('live-test', 'PLATO live test', period=10.0, plato_client=client)
    
    print()
    print("POSTING 20 tiles at different phases...")
    for i in range(20):
        phase = (i % 4) * (math.pi / 2)
        kw_type = i % 3
        kw_pairs = [('consensus', 'fleet'), ('agent', 'room'), ('tile', 'geometry')]
        kw1, kw2 = kw_pairs[kw_type]
        
        content = f"{kw1}_{kw2}_{i}"
        room.phase = phase
        score = room.add_tile(content)
        
        print(f"  tile {i:2d}: phase={phase * 180 / math.pi:.0f}°  content={content}")
    
    print()
    print("POSTING room state to PLATO...")
    result = room.post_to_plato()
    print(f"  Result: {result}")
    
    print()
    print("READING back from PLATO...")
    try:
        history = client.get_history(room.room_name, limit=10)
        print(f"  History: {len(history.get('tiles', []))} tiles retrieved")
    except Exception as e:
        print(f"  Read failed: {e}")
    
    print()
    print(f"Room summary: {room.summary()}")
    
    return room


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Oscillating Abstraction Room')
    parser.add_argument('--live', action='store_true', help='Run PLATO live test')
    parser.add_argument('--sim', action='store_true', help='Run simulation')
    parser.add_argument('--n-tiles', type=int, default=100, help='Number of tiles')
    parser.add_argument('--n-ticks', type=int, default=50, help='Number of heartbeats')
    parser.add_argument('--period', type=float, default=10.0, help='Oscillation period (seconds)')
    
    args = parser.parse_args()
    
    if args.live:
        run_plato_live_test()
    else:
        run_simulation(n_tiles=args.n_tiles, n_ticks=args.n_ticks, period=args.period)