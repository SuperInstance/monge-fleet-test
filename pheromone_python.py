"""
PheromoneTrail — Python implementation
Smallest irreducible: deposit, follow, evaporate
"""

import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class Deposit:
    content: str
    strength: float
    timestamp: float = field(default_factory=time.time)

class PheromoneTrail:
    """
    Argentine ant pheromone trail model.
    Deposit marks successful path. Follow reads trail.
    Evaporation simulates decay over time.
    """

    def __init__(self, capacity: int = 100):
        self.trail: List[Deposit] = []
        self.capacity = capacity
        self.hits = 0

    def deposit(self, content: str, strength: float = 1.0):
        """Deposit a pheromone at a point on the trail."""
        self.trail.append(Deposit(content=content, strength=strength))
        # Trim if over capacity
        if len(self.trail) > self.capacity:
            self.trail.pop(0)

    def follow(self) -> Optional[str]:
        """Follow the trail — returns strongest pheromone's content."""
        if not self.trail:
            return None
        self.hits += 1
        # Find strongest
        best = max(self.trail, key=lambda d: d.strength)
        return best.content

    def evaporate(self, rate: float = 0.99):
        """Apply decay: all strengths multiplied by rate."""
        for d in self.trail:
            d.strength *= rate
        # Remove near-zero
        self.trail = [d for d in self.trail if d.strength > 0.01]

    def get_strength(self, content: str) -> float:
        """Get total strength for a given content."""
        return sum(d.strength for d in self.trail if d.content == content)

    def __len__(self):
        return len(self.trail)


if __name__ == "__main__":
    # Quick test
    trail = PheromoneTrail(capacity=20)
    trail.deposit("north", strength=0.9)
    trail.deposit("north", strength=0.7)
    trail.deposit("east", strength=0.5)
    
    print(f"Trail length: {len(trail)}")
    print(f"Follow: {trail.follow()}")
    print(f"North strength: {trail.get_strength('north')}")
    
    trail.evaporate(rate=0.9)
    print(f"After evaporation: north={trail.get_strength('north'):.4f}")
