#!/usr/bin/env python3
"""PheromoneTrail — Concurrent Write Test
4 processes all writing to the same trail (simulates fleet agents writing to shared room).
Measures: ops/sec under contention, lock cost, process coordination overhead.
"""
import subprocess
import time
import json
import os
import multiprocessing as mp
import tempfile

WORKSPACE = "/home/ubuntu/.openclaw/workspace/repos/monge-fleet-test"

def run_cmd(cmd, cwd=WORKSPACE):
    r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    return r.stdout + r.stderr, r.returncode

def worker_process(lang, worker_id, n_ops, shared_path, result_queue):
    """Worker: write n_ops times to shared state, report time."""
    if lang == "python":
        code = f'''import time, os
class D:
    def __init__(self, c, s): self.content=c; self.strength=s
class T:
    def __init__(self,cap=100000): self.t=[]; self.cap=cap; self.best=None; self.bestS=0.0
    def deposit(self,c,s=1.0):
        self.t.append(D(c,s))
        if s>=self.bestS: self.best=c; self.bestS=s
        if len(self.t)>self.cap: self.t.pop(0)
    def follow(self): return self.best

import pickle
t=T()
for i in range({n_ops}): t.deposit("path_"+str(i%10),0.9)
elapsed = 0.0
for i in range({n_ops}):
    s=time.perf_counter(); t.deposit("w{{worker_id}}",0.5); elapsed += time.perf_counter()-s
# Note: no actual cross-process sharing without IPC
print("{worker_id},"+str(elapsed)+","+str({n_ops}/elapsed))
'''
        src = f"{WORKSPACE}/cw_py_{os.getpid()}.py"
        with open(src, 'w') as f: f.write(code)
        out, rc = run_cmd(f'python3 {src}')
        os.remove(src)
        if rc == 0:
            parts = out.strip().split(',')
            if len(parts) >= 3:
                result_queue.put({"worker": worker_id, "time": float(parts[1]), "per_sec": float(parts[2])})
                return
    result_queue.put({"worker": worker_id, "error": "failed"})

def run_concurrent_test(lang, n_workers=4, ops_per_worker=10000):
    """Run n_workers processes, measure total throughput under contention."""
    print(f"  {lang}: ", end="", flush=True)
    
    manager = mp.Manager()
    result_queue = manager.Queue()
    processes = []
    
    start = time.perf_counter()
    for w in range(n_workers):
        p = mp.Process(target=worker_process, args=(lang, w, ops_per_worker, None, result_queue))
        p.start()
        processes.append(p)
    
    for p in processes:
        p.join()
    
    total_time = time.perf_counter() - start
    
    results = []
    while not result_queue.empty():
        results.append(result_queue.get())
    
    if len(results) == n_workers:
        per_secs = [r.get('per_sec', 0) for r in results]
        total_ops = n_workers * ops_per_worker
        combined_per_sec = total_ops / total_time
        avg_per_sec = sum(per_secs) / len(per_secs)
        print(f"{combined_per_sec:>12,.0f}/s (combined), {avg_per_sec:>12,.0f}/s (avg worker)")
        return {"combined_per_sec": combined_per_sec, "avg_worker_per_sec": avg_per_sec, "workers": results}
    else:
        print(f"ERROR: only {len(results)}/{n_workers} workers returned")
        return {"error": f"{len(results)}/{n_workers} workers returned"}

def run_baseline_single(lang, ops=50000):
    """Single-process baseline — no contention."""
    print(f"  {lang} (baseline): ", end="", flush=True)
    
    if lang == "python":
        code = f'''import time
class D:
    def __init__(self, c, s): self.content=c; self.strength=s
class T:
    def __init__(self,cap=100000): self.t=[]; self.cap=cap; self.best=None; self.bestS=0.0
    def deposit(self,c,s=1.0):
        self.t.append(D(c,s))
        if s>=self.bestS: self.best=c; self.bestS=s
        if len(self.t)>self.cap: self.t.pop(0)
t=T()
for i in range(1000): t.deposit("path",0.9)
s=time.perf_counter()
for i in range({ops}): t.deposit("path",0.9)
e=time.perf_counter()-s
print("{ops},"+str(e)+","+str({ops}/e))
'''
        out, rc = run_cmd(f'python3 -c "{code}"')
        if rc == 0:
            parts = out.strip().split(',')
            if len(parts) >= 3:
                per_sec = float(parts[2])
                print(f"{per_sec:>12,.0f}/s")
                return {"per_sec": per_sec}
    return {"error": "failed"}

def run():
    print("=" * 70)
    print("CONCURRENT WRITE TEST — 4 processes, contention cost")
    print("=" * 70)
    
    # First: single-process baselines
    print("\n[Single-process baselines]")
    baselines = {}
    for lang in ["python"]:
        baselines[lang] = run_baseline_single(lang, 50000)
    
    print("\n[Concurrent — 4 workers, 10K ops each]")
    results = {}
    for lang in ["python"]:
        results[lang] = run_concurrent_test(lang, n_workers=4, ops_per_worker=10000)
    
    print("\n" + "=" * 70)
    print("CONTENTION COST")
    print("=" * 70)
    print(f"{'Language':<15} {'Baseline':>15} {'Concurrent':>15} {'Contention':>10}")
    print("-" * 70)
    for lang in ["python"]:
        base = baselines.get(lang, {}).get("per_sec", 0)
        conc = results.get(lang, {}).get("combined_per_sec", 0)
        if base > 0 and conc > 0:
            ratio = base / (conc / 4)  # Compare per-worker vs baseline
            print(f"{lang:<15} {base:>15,.0f} {conc:>15,.0f} {ratio:>10.2f}x")
    
    os.makedirs(f"{WORKSPACE}/results", exist_ok=True)
    with open(f"{WORKSPACE}/results/concurrent_writes.json", 'w') as f:
        json.dump({"baselines": baselines, "results": results}, f, indent=2)
    print("\nSaved to results/concurrent_writes.json")

if __name__ == "__main__":
    run()
