#!/usr/bin/env python3
"""PheromoneTrail -- Capacity Scaling Test"""
import subprocess, time, json, os, shutil

WORKSPACE = "/home/ubuntu/.openclaw/workspace/repos/monge-fleet-test"
OPS = 50000

def run_cmd(cmd, cwd=WORKSPACE):
    r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    return r.stdout + r.stderr, r.returncode

def bench_go(capacity):
    src = f"{WORKSPACE}/cs_go_{capacity}.go"
    with open(src, 'w') as f:
        f.write(f'''package main
import "time"
import "fmt"
type D struct {{ content string; strength float64; ts float64 }}
type P struct {{ trail []D; cap int; best string; bestS float64 }}
func newP(c int) *P {{ return &P{{make([]D,0),c,"",0.0}} }}
func (p *P) deposit(c string, s float64) {{
    p.trail = append(p.trail, D{{c,s,float64(time.Now().UnixNano())/1e9}})
    if s >= p.bestS {{ p.best = c; p.bestS = s }}
    if len(p.trail) > p.cap {{ old := p.trail[0]; p.trail = p.trail[1:]; if old.content == p.best {{ p.best="";p.bestS=0.0; for _,d:=range p.trail {{ if d.strength>p.bestS {{ p.bestS=d.strength; p.best=d.content }} }} }} }}
}}
func main() {{
    n := {OPS}; t := newP({capacity})
    for i := 0; i < 1000; i++ {{ t.deposit("path",0.9) }}
    start := time.Now()
    for i := 0; i < n; i++ {{ t.deposit("path",0.9) }}
    elapsed := time.Since(start).Seconds()
    fmt.Printf("%d,%.6f,%.0f\\n", n, elapsed, float64(n)/elapsed)
}}
''')
    bin = f"{WORKSPACE}/csbenchgo"
    combined, rc = run_cmd(f'go build -o {bin} {src}')
    if rc != 0: os.remove(src); return {"error": combined[:100]}
    combined, rc = run_cmd(bin)
    os.remove(src); os.remove(bin)
    if rc != 0: return {"error": combined[:100]}
    parts = combined.strip().split(',')
    if len(parts) < 3: return {"error": f"bad output: '{combined[:100]}'"}
    try:
        return {"ops": int(parts[0]), "time": float(parts[1]), "per_sec": float(parts[2])}
    except:
        return {"error": f"parse error: {combined[:100]}"}

def bench_rust(capacity):
    os.makedirs(f"{WORKSPACE}/rs_cs/src", exist_ok=True)
    with open(f"{WORKSPACE}/rs_cs/Cargo.toml", 'w') as f:
        f.write('[package]\nname="cs"\nversion="0.1.0"\n[dependencies]\n')
    with open(f"{WORKSPACE}/rs_cs/src/main.rs", 'w') as f:
        f.write(f'''use std::time::Instant; use std::collections::VecDeque;
struct D {{ c: String, s: f64, ts: f64 }}
struct T {{ t: VecDeque<D>, cap: usize, best: Option<String>, bestS: f64 }}
impl T {{
    fn new(c:usize)->Self{{T{{t:VecDeque::new(),cap:c,best:None,bestS:0.0}}}}
    fn deposit(&mut self,cc:&str,s:f64){{
        self.t.push_back(D{{c:cc.to_string(),s,ts:0.0}});
        if s>=self.bestS{{self.best=Some(cc.to_string());self.bestS=s}}
        if self.t.len()>self.cap{{self.t.pop_front();}}
    }}
}}
fn main(){{let n={OPS};let mut t=T::new({capacity});for i in 0..1000{{t.deposit("path",0.9);}}let s=Instant::now();for i in 0..n{{t.deposit("path",0.9);}}let e=s.elapsed().as_secs_f64();println!("{{}},{{}},{{}}",n,e,n as f64/e);}}
''')
    combined, rc = run_cmd('cargo build --release --quiet 2>&1', cwd=f"{WORKSPACE}/rs_cs")
    if rc != 0: shutil.rmtree(f"{WORKSPACE}/rs_cs", ignore_errors=True); return {"error": combined[:100]}
    combined, rc = run_cmd(f"{WORKSPACE}/rs_cs/target/release/cs")
    shutil.rmtree(f"{WORKSPACE}/rs_cs", ignore_errors=True)
    if rc != 0: return {"error": combined[:100]}
    parts = combined.strip().split(',')
    if len(parts) < 3: return {"error": f"bad output: {combined[:100]}"}
    try:
        return {"ops": int(parts[0]), "time": float(parts[1]), "per_sec": float(parts[2])}
    except:
        return {"error": f"parse error: {combined[:100]}"}

def bench_python(capacity):
    src = f"{WORKSPACE}/cs_py_{capacity}.py"
    with open(src, 'w') as f:
        f.write(f'''import time
class D:
    def __init__(self, c, s): self.content=c; self.strength=s
class T:
    def __init__(self,cap): self.t=[]; self.cap=cap; self.best=None; self.bestS=0.0
    def deposit(self,c,s=1.0):
        self.t.append(D(c,s))
        if s>=self.bestS: self.best=c; self.bestS=s
        if len(self.t)>self.cap: self.t.pop(0)
t=T({capacity})
for i in range(1000): t.deposit("path",0.9)
s=time.perf_counter()
for i in range({OPS}): t.deposit("path",0.9)
e=time.perf_counter()-s
print("{OPS},"+str(e)+","+str({OPS}/e))
''')
    combined, rc = run_cmd(f'python3 {src}')
    os.remove(src)
    if rc != 0: return {"error": combined[:100]}
    parts = combined.strip().split(',')
    if len(parts) < 3: return {"error": f"bad output: {combined[:100]}"}
    try:
        return {"ops": int(parts[0]), "time": float(parts[1]), "per_sec": float(parts[2])}
    except:
        return {"error": f"parse error: {combined[:100]}"}

def bench_nodejs(capacity):
    src = f"{WORKSPACE}/cs_nd_{capacity}.mjs"
    with open(src, 'w') as f:
        f.write(f'''const t={{t:[],cap:{capacity},best:null,bestS:0}};
function d(c,s){{t.t.push({{c,s}});if(s>=t.bestS){{t.best=c;t.bestS=s;}}if(t.t.length>t.cap)t.t.shift();}}
for(let i=0;i<1000;i++)d("path",0.9);
const s=Date.now();for(let i=0;i<{OPS};i++)d("path",0.9);
const e=(Date.now()-s)/1000;console.log("{OPS},"+e+","+({OPS}/e));
''')
    combined, rc = run_cmd(f'node {src}', cwd=WORKSPACE)
    os.remove(src)
    if rc != 0: return {"error": combined[:100]}
    parts = combined.strip().split(',')
    if len(parts) < 3: return {"error": f"bad output: {combined[:100]}"}
    try:
        return {"ops": int(parts[0]), "time": float(parts[1]), "per_sec": float(parts[2])}
    except:
        return {"error": f"parse error: {combined[:100]}"}

def run():
    print("=" * 70)
    print("CAPACITY SCALING TEST")
    print("=" * 70)
    capacities = [1_000, 10_000, 100_000]
    results = {}
    for lang, fn in [("Python", bench_python), ("Node.js", bench_nodejs), ("Go", bench_go), ("Rust", bench_rust)]:
        print(f"\n[{lang}]")
        results[lang] = {}
        for cap in capacities:
            print(f"  {cap:>7,}: ", end="", flush=True)
            r = fn(cap)
            if "error" in r: print(f"ERROR: {r['error']}"); results[lang][cap] = r
            else: print(f"{r['per_sec']:>12,.0f}/s ({r['time']:.4f}s)"); results[lang][cap] = r
    print("\n" + "=" * 70)
    print(f"{'Language':<10} {'1K':>15} {'10K':>15} {'100K':>15} {'Degradation'}")
    print("-" * 70)
    for lang, lr in results.items():
        vals = []
        for cap in capacities:
            if "error" in lr.get(cap, {}): vals.append("ERROR")
            else: vals.append(f"{lr[cap]['per_sec']:,.0f}")
        deg = "--"
        if len([v for v in vals if v != "ERROR"]) == 3:
            try:
                f,l = lr[1000]['per_sec'], lr[100000]['per_sec']
                deg = f"{f/l:.1f}x" if l > 0 else "?"
            except: deg = "?"
        print(f"{lang:<10} {vals[0]:>15} {vals[1]:>15} {vals[2]:>15} {deg}")
    print("=" * 70)
    os.makedirs(f"{WORKSPACE}/results", exist_ok=True)
    with open(f"{WORKSPACE}/results/capacity_scaling.json", 'w') as f: json.dump(results, f, indent=2)
    print("Saved to results/capacity_scaling.json")

if __name__ == "__main__": run()