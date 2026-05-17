// PheromoneTrail — Node.js (O(1) follow)
const N = 50000;

class PheromoneTrail {
    constructor(capacity) {
        this.trail = [];
        this.capacity = capacity;
        this.hits = 0;
        this.bestContent = null;
        this.bestStrength = 0;
    }

    deposit(content, strength = 1.0) {
        this.trail.push({content, strength, ts: Date.now() / 1000});
        if (strength >= this.bestStrength) {
            this.bestContent = content;
            this.bestStrength = strength;
        }
        if (this.trail.length > this.capacity) {
            const old = this.trail.shift();
            if (old.content === this.bestContent) {
                // Recompute best
                this.bestContent = null;
                this.bestStrength = 0;
                for (const d of this.trail) {
                    if (d.strength > this.bestStrength) {
                        this.bestStrength = d.strength;
                        this.bestContent = d.content;
                    }
                }
            }
        }
    }

    follow() {
        if (!this.trail.length) return null;
        this.hits++;
        return this.bestContent;
    }

    evaporate(rate = 0.99) {
        this.trail = this.trail.map(d => ({...d, strength: d.strength * rate})).filter(d => d.strength > 0.01);
        // Recompute best
        this.bestContent = null;
        this.bestStrength = 0;
        for (const d of this.trail) {
            if (d.strength > this.bestStrength) {
                this.bestStrength = d.strength;
                this.bestContent = d.content;
            }
        }
    }

    get length() { return this.trail.length; }
}

const trail = new PheromoneTrail(100000);
for (let i = 0; i < 1000; i++) { trail.deposit('path', 0.9); trail.follow(); }

const depositStart = Date.now();
for (let i = 0; i < N; i++) trail.deposit('path', 0.9);
const depositT = (Date.now() - depositStart) / 1000;

const followStart = Date.now();
for (let i = 0; i < N; i++) trail.follow();
const followT = (Date.now() - followStart) / 1000;

const evapStart = Date.now();
for (let i = 0; i < 10; i++) trail.evaporate(0.99);
const evapT = (Date.now() - evapStart) / 1000;

console.log(`Node.js: deposit=${Math.round(N/depositT)}/s follow=${Math.round(N/followT)}/s evap=${Math.round(N*10/evapT)}/s`);