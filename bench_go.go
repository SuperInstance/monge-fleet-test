package main

import (
    "fmt"
    "time"
)

type Deposit struct {
    content  string
    strength float64
    timestamp float64
}

type PheromoneTrail struct {
    trail []Deposit
    capacity int
    hits int
    bestContent string
    bestStrength float64
}

func NewTrail(cap int) *PheromoneTrail {
    return &PheromoneTrail{make([]Deposit, 0), cap, 0, "", 0.0}
}

func (p *PheromoneTrail) Deposit(content string, strength float64) {
    p.trail = append(p.trail, Deposit{content, strength, float64(time.Now().UnixNano()) / 1e9})
    if strength >= p.bestStrength {
        p.bestContent = content
        p.bestStrength = strength
    }
    if len(p.trail) > p.capacity {
        old := p.trail[0]
        p.trail = p.trail[1:]
        if old.content == p.bestContent {
            p.bestContent = ""
            p.bestStrength = 0.0
            for _, d := range p.trail {
                if d.strength > p.bestStrength {
                    p.bestStrength = d.strength
                    p.bestContent = d.content
                }
            }
        }
    }
}

func (p *PheromoneTrail) Follow() string {
    p.hits++
    return p.bestContent
}

func (p *PheromoneTrail) Evaporate(rate float64) {
    thr := 0.01
    n := make([]Deposit, 0)
    for _, d := range p.trail {
        d.strength *= rate
        if d.strength > thr { n = append(n, d) }
    }
    p.trail = n
    // Recompute best
    p.bestContent = ""
    p.bestStrength = 0.0
    for _, d := range p.trail {
        if d.strength > p.bestStrength {
            p.bestStrength = d.strength
            p.bestContent = d.content
        }
    }
}

func main() {
    n := 50000
    trail := NewTrail(100000)

    for i := 0; i < 1000; i++ { trail.Deposit("path", 0.9); trail.Follow() }

    start := time.Now()
    for i := 0; i < n; i++ { trail.Deposit("path", 0.9) }
    depositT := time.Since(start).Seconds()

    followStart := time.Now()
    for i := 0; i < n; i++ { trail.Follow() }
    followT := time.Since(followStart).Seconds()

    evapStart := time.Now()
    for i := 0; i < 10; i++ { trail.Evaporate(0.99) }
    evapT := time.Since(evapStart).Seconds()

    nf := float64(n)
    fmt.Printf("Go: deposit=%.0f/s follow=%.0f/s evap=%.0f/s\n",
        nf/depositT, nf/followT, nf*10/evapT)
}