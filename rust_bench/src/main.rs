use std::time::Instant;
use std::collections::VecDeque;

struct Deposit {
    content: String,
    strength: f64,
    timestamp: f64,
}

struct PheromoneTrail {
    trail: VecDeque<Deposit>,
    capacity: usize,
    hits: usize,
}

impl PheromoneTrail {
    fn new(cap: usize) -> Self {
        PheromoneTrail { trail: VecDeque::new(), capacity: cap, hits: 0 }
    }
    fn deposit(&mut self, content: &str, strength: f64) {
        let ts = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH).unwrap().as_secs_f64();
        self.trail.push_back(Deposit {
            content: content.to_string(),
            strength,
            timestamp: ts,
        });
        if self.trail.len() > self.capacity {
            self.trail.pop_front();
        }
    }
    fn follow(&mut self) -> String {
        self.hits += 1;
        if self.trail.is_empty() { return String::new() }
        let mut best = &self.trail[0];
        for d in &self.trail {
            if d.strength > best.strength { best = d }
        }
        best.content.clone()
    }
    fn evaporate(&mut self, rate: f64) {
        let thr = 0.01;
        let mut new_trail: VecDeque<Deposit> = self.trail.drain(..).filter_map(|mut d| {
            d.strength *= rate;
            if d.strength > thr { Some(d) } else { None }
        }).collect();
        self.trail = new_trail;
    }
    fn len(&self) -> usize { self.trail.len() }
}

fn main() {
    let n = 50000;
    let mut trail = PheromoneTrail::new(100000);

    for i in 0..1000 { trail.deposit("path", 0.9); trail.follow(); }

    let start = Instant::now();
    for i in 0..n { trail.deposit("path", 0.9); }
    let deposit_time = start.elapsed().as_secs_f64();

    let follow_start = Instant::now();
    for _ in 0..n { trail.follow(); }
    let follow_time = follow_start.elapsed().as_secs_f64();

    let evap_start = Instant::now();
    for _ in 0..10 { trail.evaporate(0.99); }
    let evaporate_time = evap_start.elapsed().as_secs_f64();

    let nf = n as f64;
    let evap_per_sec = (n * 10) as f64 / evaporate_time;
    
    println!(
        "{\"deposit_time\":{},\"deposit_per_sec\":{}," +
        "\"follow_time\":{}," +
        "\"follow_per_sec\":{}," +
        "\"evaporate_time\":{}," +
        "\"evaporate_per_sec\":{}," +
        "\"trail_size\":{}\"",
        deposit_time,
        nf / deposit_time,
        follow_time,
        nf / follow_time,
        evaporate_time,
        evap_per_sec,
        trail.len()
    );
}
