"""
PheromoneTrail — Benchmark Suite
Tests all four language implementations at metal level on ARM.
"""

import subprocess
import time
import json
import os
import shutil

WORKSPACE = "/home/ubuntu/.openclaw/workspace/repos/monge-fleet-test"

def run_command(cmd, cwd=WORKSPACE):
    start = time.perf_counter()
    result = subprocess.run(cmd, shell=True, cwd=cwd,
                          capture_output=True, text=True)
    elapsed = time.perf_counter() - start
    return result.stdout, result.stderr, elapsed, result.returncode

def benchmark_python(ops=50000):
    code = "\n".join([
        "import time, json",
        f"N = {ops}",
        "from dataclasses import dataclass, field",
        "import time as _t",
        "@dataclass",
        "class Deposit:",
        "    content: str",
        "    strength: float",
        "    timestamp: float = field(default_factory=_t.time)",
        "class PheromoneTrail:",
        "    def __init__(self, capacity=100):",
        "        self.trail = []",
        "        self.capacity = capacity",
        "        self.hits = 0",
        "    def deposit(self, content, strength=1.0):",
        "        self.trail.append(Deposit(content=content, strength=strength))",
        "        if len(self.trail) > self.capacity: self.trail.pop(0)",
        "    def follow(self):",
        "        if not self.trail: return None",
        "        self.hits += 1",
        "        return max(self.trail, key=lambda d: d.strength).content",
        "    def evaporate(self, rate=0.99):",
        "        for d in self.trail: d.strength *= rate",
        "        self.trail = [d for d in self.trail if d.strength > 0.01]",
        "    def len(self): return len(self.trail)",
        "trail = PheromoneTrail(100000)",
        "for i in range(1000): trail.deposit('path', 0.9); trail.follow()",
        "s = time.perf_counter(); [trail.deposit('path', 0.9) for i in range(N)]; deposit_t = time.perf_counter() - s",
        "s = time.perf_counter(); [trail.follow() for i in range(N)]; follow_t = time.perf_counter() - s",
        "s = time.perf_counter(); [trail.evaporate(0.99) for i in range(10)]; evap_t = time.perf_counter() - s",
        "print(json.dumps({'ops': N, 'deposit_time': deposit_t, 'deposit_per_sec': N/deposit_t, 'follow_time': follow_t, 'follow_per_sec': N/follow_t, 'evaporate_time': evap_t, 'evaporate_per_sec': N*10/evap_t, 'trail_size': trail.len()}))"
    ])
    stdout, stderr, wall, rc = run_command(f'python3 -c "{code}"')
    if rc != 0:
        return {"error": stderr[:200]}
    try:
        return json.loads(stdout.strip())
    except:
        return {"error": f"parse: {stdout[:200]}"}

def benchmark_nodejs(ops=50000):
    code = "; ".join([
        f"const N = {ops}",
        "class PheromoneTrail { constructor(cap) { this.trail = []; this.cap = cap; this.hits = 0 }",
        "  deposit(c, s=1.0) { this.trail.push({content:c, strength:s, ts:Date.now()/1000}); if(this.trail.length>this.cap) this.trail.shift() }",
        "  follow() { if(!this.trail.length) return null; this.hits++; return this.trail.reduce((b,d) => d.strength>b.strength?d:b).content }",
        "  evaporate(r=0.99) { this.trail=this.trail.map(d=>({...d,strength:d.strength*r})).filter(d=>d.strength>0.01) }",
        "  get length() { return this.trail.length } }",
        "const trail = new PheromoneTrail(100000)",
        "for(let i=0;i<1000;i++){trail.deposit('path',0.9);trail.follow()}",
        f"const ds=Date.now();for(let i=0;i<N;i++)trail.deposit('path',0.9);const deposit_t=(Date.now()-ds)/1000",
        f"const fs=Date.now();for(let i=0;i<N;i++)trail.follow();const follow_t=(Date.now()-fs)/1000",
        f"const es=Date.now();for(let i=0;i<10;i++)trail.evaporate(0.99);const evap_t=(Date.now()-es)/1000",
        f"console.log(JSON.stringify({{ops:N,deposit_time:deposit_t,deposit_per_sec:N/deposit_t,follow_time:follow_t,follow_per_sec:N/follow_t,evaporate_time:evap_t,evaporate_per_sec:N*10/evap_t,trail_size:trail.length}}))"
    ])
    stdout, stderr, wall, rc = run_command(f'node -e "{code}"', cwd=WORKSPACE)
    if rc != 0:
        return {"error": stderr[:200]}
    try:
        return json.loads(stdout.strip())
    except:
        return {"error": f"parse: {stdout[:200]}"}

def benchmark_go(ops=50000):
    binary = f"{WORKSPACE}/pgobench"
    go_src = f"{WORKSPACE}/pheromone_go_bench.go"
    
    # Write Go source directly to file to avoid quoting issues
    go_src_content = """package main

import "encoding/json"
import "time"

type Deposit struct {
    content  string
    strength float64
    timestamp float64
}

type PheromoneTrail struct {
    trail []Deposit
    capacity int
    hits int
}

func NewTrail(cap int) *PheromoneTrail {
    return &PheromoneTrail{make([]Deposit, 0), cap, 0}
}

func (p *PheromoneTrail) Deposit(content string, strength float64) {
    p.trail = append(p.trail, Deposit{content, strength, float64(time.Now().UnixNano()) / 1e9})
    if len(p.trail) > p.capacity {
        p.trail = p.trail[1:]
    }
}

func (p *PheromoneTrail) Follow() string {
    p.hits++
    if len(p.trail) == 0 { return "" }
    best := p.trail[0]
    for _, d := range p.trail {
        if d.strength > best.strength { best = d }
    }
    return best.content
}

func (p *PheromoneTrail) Evaporate(rate float64) {
    thr := 0.01
    n := make([]Deposit, 0)
    for _, d := range p.trail {
        d.strength *= rate
        if d.strength > thr { n = append(n, d) }
    }
    p.trail = n
}

func (p *PheromoneTrail) Len() int { return len(p.trail) }

func main() {
    N := 50000
    trail := NewTrail(100000)

    for i := 0; i < 1000; i++ { trail.Deposit("path", 0.9); trail.Follow() }

    start := time.Now()
    for i := 0; i < N; i++ { trail.Deposit("path", 0.9) }
    depositTime := time.Since(start).Seconds()

    followStart := time.Now()
    for i := 0; i < N; i++ { trail.Follow() }
    followTime := time.Since(followStart).Seconds()

    evapStart := time.Now()
    for i := 0; i < 10; i++ { trail.Evaporate(0.99) }
    evaporateTime := time.Since(evapStart).Seconds()

    result := map[string]interface{}{
        "ops": N,
        "deposit_time": depositTime,
        "deposit_per_sec": float64(N) / depositTime,
        "follow_time": followTime,
        "follow_per_sec": float64(N) / followTime,
        "evaporate_time": evaporateTime,
        "evaporate_per_sec": float64(N*10) / evaporateTime,
        "trail_size": trail.Len(),
    }
    b, _ := json.Marshal(result)
    println(string(b))
}
""".replace("N := 50000", f"N := {ops}")
    
    with open(go_src, 'w') as f:
        f.write(go_src_content)
    
    _, compile_err, _, rc = run_command(f'go build -o {binary} {go_src}', cwd=WORKSPACE)
    if rc != 0:
        return {"error": f"compile: {compile_err[:200]}"}
    
    stdout, stderr, wall, rc = run_command(binary, cwd=WORKSPACE)
    os.remove(go_src)
    os.remove(binary)
    if rc != 0:
        return {"error": stderr[:200]}
    try:
        return json.loads(stdout.strip())
    except:
        return {"error": f"parse: '{stdout[:200]}'"}

def benchmark_rust(ops=50000):
    binary = f"{WORKSPACE}/prustbench"
    cargo_toml = f"{WORKSPACE}/rust_bench/Cargo.toml"
    src_main = f"{WORKSPACE}/rust_bench/src/main.rs"
    rust_src_file = f"{WORKSPACE}/rust_bench_src.rs"
    
    os.makedirs(f"{WORKSPACE}/rust_bench/src", exist_ok=True)
    
    with open(cargo_toml, 'w') as f:
        f.write('[package]\nname = "pheromone_bench"\nversion = "0.1.0"\n\n[dependencies]\n')
    
    # Write Rust source directly to file
    rust_src_content = f"""use std::time::Instant;
use std::collections::VecDeque;

struct Deposit {{
    content: String,
    strength: f64,
    timestamp: f64,
}}

struct PheromoneTrail {{
    trail: VecDeque<Deposit>,
    capacity: usize,
    hits: usize,
}}

impl PheromoneTrail {{
    fn new(cap: usize) -> Self {{
        PheromoneTrail {{ trail: VecDeque::new(), capacity: cap, hits: 0 }}
    }}
    fn deposit(&mut self, content: &str, strength: f64) {{
        let ts = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH).unwrap().as_secs_f64();
        self.trail.push_back(Deposit {{
            content: content.to_string(),
            strength,
            timestamp: ts,
        }});
        if self.trail.len() > self.capacity {{
            self.trail.pop_front();
        }}
    }}
    fn follow(&mut self) -> String {{
        self.hits += 1;
        if self.trail.is_empty() {{ return String::new() }}
        let mut best = &self.trail[0];
        for d in &self.trail {{
            if d.strength > best.strength {{ best = d }}
        }}
        best.content.clone()
    }}
    fn evaporate(&mut self, rate: f64) {{
        let thr = 0.01;
        let mut new_trail: VecDeque<Deposit> = self.trail.drain(..).filter_map(|mut d| {{
            d.strength *= rate;
            if d.strength > thr {{ Some(d) }} else {{ None }}
        }}).collect();
        self.trail = new_trail;
    }}
    fn len(&self) -> usize {{ self.trail.len() }}
}}

fn main() {{
    let n = {ops};
    let mut trail = PheromoneTrail::new(100000);

    for i in 0..1000 {{ trail.deposit("path", 0.9); trail.follow(); }}

    let start = Instant::now();
    for i in 0..n {{ trail.deposit("path", 0.9); }}
    let deposit_time = start.elapsed().as_secs_f64();

    let follow_start = Instant::now();
    for _ in 0..n {{ trail.follow(); }}
    let follow_time = follow_start.elapsed().as_secs_f64();

    let evap_start = Instant::now();
    for _ in 0..10 {{ trail.evaporate(0.99); }}
    let evaporate_time = evap_start.elapsed().as_secs_f64();

    let nf = n as f64;
    let evap_per_sec = (n * 10) as f64 / evaporate_time;
    
    println!(
        "{{\\"deposit_time\\":{{}},\\"deposit_per_sec\\":{{}}," +
        "\\"follow_time\\":{{}}," +
        "\\"follow_per_sec\\":{{}}," +
        "\\"evaporate_time\\":{{}}," +
        "\\"evaporate_per_sec\\":{{}}," +
        "\\"trail_size\\":{{}}\\"",
        deposit_time,
        nf / deposit_time,
        follow_time,
        nf / follow_time,
        evaporate_time,
        evap_per_sec,
        trail.len()
    );
}}
"""
    
    with open(src_main, 'w') as f:
        f.write(rust_src_content)
    
    _, compile_err, _, rc = run_command('cargo build --release --quiet 2>&1', cwd=f"{WORKSPACE}/rust_bench")
    if rc != 0:
        return {"error": f"cargo build failed: {compile_err[:300]}"}
    
    binary_path = f"{WORKSPACE}/rust_bench/target/release/pheromone_bench"
    stdout, stderr, wall, rc = run_command(binary_path, cwd=WORKSPACE)
    
    shutil.rmtree(f"{WORKSPACE}/rust_bench", ignore_errors=True)
    
    if rc != 0:
        return {"error": stderr[:200]}
    try:
        return json.loads(stdout.strip())
    except Exception as e:
        return {"error": f"parse: '{stdout[:200]}' - {e}"}

def run_benchmarks():
    print("=" * 70)
    print("PHEROMONE TRAIL -- Metal Level Benchmarks (ARM 4-core)")
    print("=" * 70)
    
    ops = 50000
    results = {}
    
    print(f"\n[Python] {ops:,} ops...")
    r = benchmark_python(ops)
    results['python'] = r
    if 'error' in r:
        print(f"  ERROR: {r['error']}")
    else:
        print(f"  Deposit: {r['deposit_per_sec']:>15,.0f}/s")
        print(f"  Follow:  {r['follow_per_sec']:>15,.0f}/s")
        print(f"  Evap:    {r['evaporate_per_sec']:>15,.0f}/s")
    
    print(f"\n[Node.js] {ops:,} ops...")
    r = benchmark_nodejs(ops)
    results['nodejs'] = r
    if 'error' in r:
        print(f"  ERROR: {r['error']}")
    else:
        print(f"  Deposit: {r['deposit_per_sec']:>15,.0f}/s")
        print(f"  Follow:  {r['follow_per_sec']:>15,.0f}/s")
        print(f"  Evap:    {r['evaporate_per_sec']:>15,.0f}/s")
    
    print(f"\n[Go] {ops:,} ops...")
    r = benchmark_go(ops)
    results['go'] = r
    if 'error' in r:
        print(f"  ERROR: {r['error']}")
    else:
        print(f"  Deposit: {r['deposit_per_sec']:>15,.0f}/s")
        print(f"  Follow:  {r['follow_per_sec']:>15,.0f}/s")
        print(f"  Evap:    {r['evaporate_per_sec']:>15,.0f}/s")
    
    print(f"\n[Rust] {ops:,} ops...")
    r = benchmark_rust(ops)
    results['rust'] = r
    if 'error' in r:
        print(f"  ERROR: {r['error']}")
    else:
        print(f"  Deposit: {r['deposit_per_sec']:>15,.0f}/s")
        print(f"  Follow:  {r['follow_per_sec']:>15,.0f}/s")
        print(f"  Evap:    {r['evaporate_per_sec']:>15,.0f}/s")
    
    print("\n" + "=" * 70)
    print("SUMMARY -- ops/sec (higher is better)")
    print("=" * 70)
    print(f"{'Language':<10} {'Deposit':>15} {'Follow':>15} {'Evaporate':>15}")
    print("-" * 70)
    for lang, r in results.items():
        if 'error' not in r:
            print(f"{lang:<10} {r['deposit_per_sec']:>15,.0f} {r['follow_per_sec']:>15,.0f} {r['evaporate_per_sec']:>15,.0f}")
    
    os.makedirs(f"{WORKSPACE}/results", exist_ok=True)
    with open(f"{WORKSPACE}/results/metal_benchmarks.json", 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved to results/metal_benchmarks.json")
    
    return results

if __name__ == "__main__":
    run_benchmarks()