// PheromoneTrail — Rust (O(1) follow)
use std::collections::VecDeque;
use std::time::Instant;

struct Deposit {
    content: String,
    strength: f64,
    timestamp: f64,
}

struct PheromoneTrail {
    trail: VecDeque<Deposit>,
    capacity: usize,
    hits: usize,
    best_content: Option<String>,
    best_strength: f64,
}

impl PheromoneTrail {
    fn new(cap: usize) -> Self {
        PheromoneTrail { trail: VecDeque::new(), capacity: cap, hits: 0, best_content: None, best_strength: 0.0 }
    }

    fn deposit(&mut self, content: &str, strength: f64) {
        let ts = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH).unwrap().as_secs_f64();
        self.trail.push_back(Deposit { content: content.to_string(), strength, timestamp: ts });
        if strength >= self.best_strength {
            self.best_content = Some(content.to_string());
            self.best_strength = strength;
        }
        if self.trail.len() > self.capacity {
            let old = self.trail.pop_front().unwrap();
            if old.content == self.best_content.clone().unwrap_or_default() {
                // Recompute
                self.best_content = None;
                self.best_strength = 0.0;
                for d in &self.trail {
                    if d.strength > self.best_strength {
                        self.best_strength = d.strength;
                        self.best_content = Some(d.content.clone());
                    }
                }
            }
        }
    }

    fn follow(&mut self) -> Option<String> {
        self.hits += 1;
        self.best_content.clone()
    }

    fn evaporate(&mut self, rate: f64) {
        let thr = 0.01;
        let mut new_trail: VecDeque<Deposit> = self.trail.drain(..).filter_map(|mut d| {
            d.strength *= rate;
            if d.strength > thr { Some(d) } else { None }
        }).collect();
        self.trail = new_trail;
        // Recompute best
        self.best_content = None;
        self.best_strength = 0.0;
        for d in &self.trail {
            if d.strength > self.best_strength {
                self.best_strength = d.strength;
                self.best_content = Some(d.content.clone());
            }
        }
    }

    fn len(&self) -> usize { self.trail.len() }
}

fn main() {
    let n = 50000;
    let mut trail = PheromoneTrail::new(100000);

    for _ in 0..1000 { trail.deposit("path", 0.9); trail.follow(); }

    let start = Instant::now();
    for _ in 0..n { trail.deposit("path", 0.9); }
    let deposit_t = start.elapsed().as_secs_f64();

    let follow_start = Instant::now();
    for _ in 0..n { trail.follow(); }
    let follow_t = follow_start.elapsed().as_secs_f64();

    let evap_start = Instant::now();
    for _ in 0..10 { trail.evaporate(0.99); }
    let evap_t = evap_start.elapsed().as_secs_f64();

    let nf = n as f64;
    println!("Rust: deposit={}/s follow={}/s evap={}/s",
        nf / deposit_t, nf / follow_t, (n * 10) as f64 / evap_t);
}