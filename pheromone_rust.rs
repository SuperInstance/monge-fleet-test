use std::collections::VecDeque;

#[derive(Clone)]
struct Deposit {
    content: String,
    strength: f64,
    timestamp: f64,
}

pub struct PheromoneTrail {
    trail: VecDeque<Deposit>,
    capacity: usize,
    hits: usize,
}

impl PheromoneTrail {
    pub fn new(capacity: usize) -> Self {
        PheromoneTrail { trail: VecDeque::new(), capacity, hits: 0 }
    }

    pub fn deposit(&mut self, content: &str, strength: f64) {
        let ts = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH).unwrap().as_secs_f64();
        self.trail.push_back(Deposit { content: content.to_string(), strength, timestamp: ts });
        if self.trail.len() > self.capacity {
            self.trail.pop_front();
        }
    }

    pub fn follow(&mut self) -> Option<String> {
        self.hits += 1;
        if self.trail.is_empty() { return None; }
        let mut best_idx = 0;
        let mut best_strength = 0.0;
        for (i, d) in self.trail.iter().enumerate() {
            if d.strength > best_strength { best_strength = d.strength; best_idx = i; }
        }
        Some(self.trail[best_idx].content.clone())
    }

    pub fn evaporate(&mut self, rate: f64) {
        let threshold = 0.01;
        // Rebuild: can't mutate in retain with & reference
        let new_trail: VecDeque<Deposit> = self.trail
            .drain(..)
            .filter_map(|mut d| { d.strength *= rate; if d.strength > threshold { Some(d) } else { None } })
            .collect();
        self.trail = new_trail;
    }

    pub fn get_strength(&self, content: &str) -> f64 {
        self.trail.iter().filter(|d| d.content == content).map(|d| d.strength).sum()
    }

    pub fn len(&self) -> usize { self.trail.len() }
}

fn main() {
    let mut trail = PheromoneTrail::new(20);
    trail.deposit("north", 0.9);
    trail.deposit("north", 0.7);
    trail.deposit("east", 0.5);
    println!("Trail length: {}", trail.len());
    println!("Follow: {:?}", trail.follow());
    println!("North strength: {:.4}", trail.get_strength("north"));
    trail.evaporate(0.9);
    println!("After evaporation: north={:.4}", trail.get_strength("north"));
}
