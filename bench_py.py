#!/usr/bin/env python3
"""PheromoneTrail — Metal Benchmark (O(1) follow)
Fixed: follow() O(1) by tracking best inline.
Now measures language overhead, not algorithmic complexity.
"""
import time, json
from dataclasses import dataclass, field
import time as _t

@dataclass
class Deposit:
    content: str
    strength: float
    timestamp: float = field(default_factory=_t.time)

class PheromoneTrail:
    def __init__(self, capacity=100):
        self.trail = []
        self.capacity = capacity
        self.hits = 0
        self.best_content = None
        self.best_strength = 0.0

    def deposit(self, content, strength=1.0):
        self.trail.append(Deposit(content=content, strength=strength))
        if strength >= self.best_strength:
            self.best_content = content
            self.best_strength = strength
        if len(self.trail) > self.capacity:
            old = self.trail.pop(0)
            if old.content == self.best_content:
                # Recompute best
                self.best_content = None
                self.best_strength = 0.0
                for d in self.trail:
                    if d.strength > self.best_strength:
                        self.best_strength = d.strength
                        self.best_content = d.content

    def follow(self):
        if not self.trail: return None
        self.hits += 1
        return self.best_content

    def evaporate(self, rate=0.99):
        for d in self.trail: d.strength *= rate
        self.trail = [d for d in self.trail if d.strength > 0.01]
        # Recompute best
        self.best_content = None
        self.best_strength = 0.0
        for d in self.trail:
            if d.strength > self.best_strength:
                self.best_strength = d.strength
                self.best_content = d.content

    def len(self): return len(self.trail)

N = 50000
trail = PheromoneTrail(100000)
for i in range(1000): trail.deposit('path', 0.9); trail.follow()

s = time.perf_counter()
for i in range(N): trail.deposit('path', 0.9)
deposit_t = time.perf_counter() - s

s = time.perf_counter()
for i in range(N): trail.follow()
follow_t = time.perf_counter() - s

s = time.perf_counter()
for i in range(10): trail.evaporate(0.99)
evap_t = time.perf_counter() - s

result = {
    'deposit_per_sec': round(N/deposit_t),
    'follow_per_sec': round(N/follow_t),
    'evaporate_per_sec': round(N*10/evap_t),
    'deposit_ms': round(deposit_t * 1000),
    'follow_ms': round(follow_t * 1000),
    'evap_ms': round(evap_t * 1000),
}
print(f"Python: deposit={result['deposit_per_sec']:,}/s follow={result['follow_per_sec']:,}/s evap={result['evaporate_per_sec']:,}/s")