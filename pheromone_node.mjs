// PheromoneTrail — Node.js (JavaScript/ESM) implementation
// Smallest irreducible: deposit, follow, evaporate

/**
 * A deposit on the pheromone trail
 * @typedef {{content: string, strength: number, timestamp: number}} Deposit
 */

class PheromoneTrail {
  /**
   * @param {number} capacity 
   */
  constructor(capacity) {
    /** @type {Deposit[]} */
    this.trail = [];
    this.capacity = capacity;
    this.hits = 0;
  }

  /**
   * Deposit a pheromone at a point on the trail
   * @param {string} content 
   * @param {number} strength 
   */
  deposit(content, strength = 1.0) {
    this.trail.push({
      content,
      strength,
      timestamp: Date.now() / 1000,
    });
    // Trim if over capacity
    if (this.trail.length > this.capacity) {
      this.trail.shift();
    }
  }

  /**
   * Follow the trail — returns strongest pheromone's content
   * @returns {string|null}
   */
  follow() {
    if (this.trail.length === 0) return null;
    this.hits++;
    // Find strongest
    let best = this.trail[0];
    for (const d of this.trail) {
      if (d.strength > best.strength) {
        best = d;
      }
    }
    return best.content;
  }

  /**
   * Apply decay: all strengths multiplied by rate
   * @param {number} rate 
   */
  evaporate(rate = 0.99) {
    const threshold = 0.01;
    this.trail = this.trail
      .map(d => ({ ...d, strength: d.strength * rate }))
      .filter(d => d.strength > threshold);
  }

  /**
   * Get total strength for a given content
   * @param {string} content 
   * @returns {number}
   */
  getStrength(content) {
    return this.trail
      .filter(d => d.content === content)
      .reduce((sum, d) => sum + d.strength, 0);
  }

  get length() {
    return this.trail.length;
  }
}

// Quick test
const trail = new PheromoneTrail(20);
trail.deposit("north", 0.9);
trail.deposit("north", 0.7);
trail.deposit("east", 0.5);

console.log(`Trail length: ${trail.length}`);
console.log(`Follow: ${trail.follow()}`);
console.log(`North strength: ${trail.getStrength("north").toFixed(4)}`);

trail.evaporate(0.9);
console.log(`After evaporation: north=${trail.getStrength("north").toFixed(4)}`);

export { PheromoneTrail };
