// PheromoneTrail — Go implementation
// Smallest irreducible: deposit, follow, evaporate

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
	trail     []Deposit
	capacity int
	hits     int
}

func NewPheromoneTrail(capacity int) *PheromoneTrail {
	return &PheromoneTrail{
		trail:     make([]Deposit, 0),
		capacity: capacity,
		hits:      0,
	}
}

func (p *PheromoneTrail) Deposit(content string, strength float64) {
	ts := float64(time.Now().UnixNano()) / 1e9
	p.trail = append(p.trail, Deposit{content, strength, ts})
	if len(p.trail) > p.capacity {
		p.trail = p.trail[1:]
	}
}

func (p *PheromoneTrail) Follow() string {
	p.hits++
	if len(p.trail) == 0 {
		return ""
	}
	// Find strongest
	bestIdx := 0
	bestStrength := 0.0
	for i, d := range p.trail {
		if d.strength > bestStrength {
			bestStrength = d.strength
			bestIdx = i
		}
	}
	return p.trail[bestIdx].content
}

func (p *PheromoneTrail) Evaporate(rate float64) {
	threshold := 0.01
	newTrail := make([]Deposit, 0)
	for _, d := range p.trail {
		d.strength *= rate
		if d.strength > threshold {
			newTrail = append(newTrail, d)
		}
	}
	p.trail = newTrail
}

func (p *PheromoneTrail) GetStrength(content string) float64 {
	total := 0.0
	for _, d := range p.trail {
		if d.content == content {
			total += d.strength
		}
	}
	return total
}

func (p *PheromoneTrail) Len() int {
	return len(p.trail)
}

func main() {
	trail := NewPheromoneTrail(20)
	
	trail.Deposit("north", 0.9)
	trail.Deposit("north", 0.7)
	trail.Deposit("east", 0.5)
	
	fmt.Printf("Trail length: %d\n", trail.Len())
	fmt.Printf("Follow: %s\n", trail.Follow())
	fmt.Printf("North strength: %.4f\n", trail.GetStrength("north"))
	
	trail.Evaporate(0.9)
	fmt.Printf("After evaporation: north=%.4f\n", trail.GetStrength("north"))
}
