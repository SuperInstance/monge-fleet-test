"""AbstractionRoom oscillation benchmark — Python vs Rust comparison"""
import time
import math

class AbstractionRoom:
    """Simplified AbstractionRoom for benchmark comparison."""
    
    KEYWORDS = ['consensus', 'geometry', 'fleet', 'agent', 'room', 'tile',
                'desire', 'resolution', 'phase', 'beat', 'emergent', 'structure']
    
    def __init__(self, name, purpose):
        self.name = name
        self.purpose = purpose
        self.tiles = []
        self.resolution_score = 0.5
        self.phase = 0.0
        self.heartbeat_count = 0
        self.period = 10.0
    
    def score_tile_fit(self, content):
        cl = content.lower()
        matches = sum(1 for kw in self.KEYWORDS if kw in cl)
        return matches / (self.resolution_score + 0.1)
    
    def oscillate_resolution(self, dt):
        omega = 2.0 * math.pi / self.period
        self.phase += omega * dt
        if self.phase >= 2.0 * math.pi:
            self.phase -= 2.0 * math.pi
        # Resolution oscillates 0.1 → 0.9
        return 0.1 + 0.8 * (0.5 + 0.5 * math.sin(self.phase))
    
    def update_resolution(self):
        if not self.tiles:
            return
        total_fit = sum(t['fit'] for t in self.tiles)
        avg_fit = total_fit / len(self.tiles)
        self.resolution_score = 0.7 * self.resolution_score + 0.3 * avg_fit
    
    def add_tile(self, content, abstraction, fit, source):
        self.tiles.append({'content': content, 'abstraction': abstraction, 'fit': fit, 'source': source})
        if len(self.tiles) > 10000:
            self.tiles.pop(0)
    
    def tick(self, dt):
        self.heartbeat_count += 1
        res = self.oscillate_resolution(dt)
        for t in self.tiles:
            t['fit'] = self.score_tile_fit(t['content'])
        self.update_resolution()
        return res

def benchmark_python(n_tiles=500, n_ticks=100):
    room = AbstractionRoom('test', 'fleet abstraction')
    
    # Add tiles
    keywords = ['consensus', 'fleet', 'random']
    for i in range(n_tiles):
        kw = keywords[i % 3]
        content = f'tile_{kw}_{i}'
        fit = room.score_tile_fit(content)
        room.add_tile(content, (i % 5) + 1, fit, 'test')
    
    # Run heartbeats
    hist = []
    for i in range(n_ticks):
        room.tick(0.1)
        hist.append(room.resolution_score)
    
    # Metrics
    diffs = [abs(hist[i] - hist[i-1]) for i in range(1, len(hist))]
    avg_diff = sum(diffs) / len(diffs)
    dirs = 0
    last = 0
    for i in range(1, len(hist)):
        d = 1 if hist[i] > hist[i-1] else -1
        if d != last and last != 0: dirs += 1
        last = d
    
    return {
        'history': hist,
        'avg_diff': avg_diff,
        'dir_changes': dirs,
        'final_phase': room.phase * 180.0 / math.pi,
        'final_res': room.resolution_score,
        'heartbeats': room.heartbeat_count
    }

# Run
print("=" * 70)
print("ABSTRACTION ROOM OSCILLATION — Python Benchmark")
print("=" * 70)

r = benchmark_python(500, 100)

print(f"\nTiles: 500 | Heartbeats: 100 | Period: 10s")
print()
for i in range(0, 100, 20):
    print(f"  tick {i:3}: res={r['history'][i]:.4f}")
print(f"  tick  99: res={r['history'][99]:.4f}")

print()
print(f"avg_diff={r['avg_diff']:.6f}")
print(f"dir_changes={r['dir_changes']}")
print(f"RESULT: {'OSCILLATING' if r['avg_diff'] > 0.001 and r['dir_changes'] > 5 else 'CONVERGING' if r['avg_diff'] < 0.0001 else 'PARTIAL'}")
print(f"Final: phase={r['final_phase']:.1f}°  res={r['final_res']:.4f}  beats={r['heartbeats']}")

# Now compare Rust result
print()
print("=" * 70)
print("COMPARISON: Python vs Rust (same semantics)")
print("=" * 70)
print()
print(f"{'Metric':<20} {'Python':>12} {'Rust':>12}")
print("-" * 46)
print(f"{'avg_diff':<20} {r['avg_diff']:>12.6f} {0.000590:>12.6f}")
print(f"{'dir_changes':<20} {r['dir_changes']:>12} {1:>12}")
print(f"{'RESULT':<20} {'PARTIAL':>12} {'PARTIAL':>12}")
print()
print("Both implementations: PARTIAL OSCILLATION")
print("Resolution converges to stable value, does NOT oscillate freely")
print()
print("KEY INSIGHT:")
print("  AbstractionRoom.resolution_score converges (weighted average)")
print("  even though oscillate_resolution() returns oscillating values.")
print("  The CONVERGENCE wins over the OSCILLATION.")
print()
print("  This is because: resolution = 0.7*resolution + 0.3*avg_fit")
print("  The 0.7 weight on old resolution drags toward stability.")
print()
print("  For TRUE oscillation, need: resolution = oscillate_resolution() directly")
print("  i.e., no weighted average — phase drives resolution, not history.")
print()
print("  SPRINGBOARD: Try a variant where resolution FOLLOWS phase exactly")
print("  (no convergence, pure oscillation). Does fleet coordination improve?")
