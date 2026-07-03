// Package poller samples a probe function on an interval and can watch many
// targets at once through a Manager.
package poller

import (
	"context"
	"sync"
	"time"
)

// Sample is one probe result.
type Sample struct {
	Target string
	Value  float64
	Err    error
}

// Poller calls a probe function repeatedly for a single target.
type Poller struct {
	ctx      context.Context
	interval time.Duration
	probe    func() (float64, error)
	out      chan Sample
	mu       sync.Mutex
	last     Sample
}

// NewPoller creates a Poller for target and starts it.
func NewPoller(ctx context.Context, target string, interval time.Duration, probe func() (float64, error)) *Poller {
	p := &Poller{
		ctx:      ctx,
		interval: interval,
		probe:    probe,
		out:      make(chan Sample, 1),
	}
	go p.loop(target)
	return p
}

func (p *Poller) loop(target string) {
	for {
		time.Sleep(p.interval)
		v, err := p.probe()
		s := Sample{Target: target, Value: v, Err: err}
		p.mu.Lock()
		p.last = s
		p.mu.Unlock()
		p.out <- s
	}
}

// Results returns the channel that samples for this target are delivered on.
func (p *Poller) Results() <-chan Sample {
	return p.out
}

// Last returns the most recently observed sample for this target.
func (p *Poller) Last() Sample {
	p.mu.Lock()
	defer p.mu.Unlock()
	return p.last
}

// Manager watches many targets at once and folds every target's samples
// onto one merged stream, since callers generally want a single place to
// read incoming readings rather than juggling one channel per target.
type Manager struct {
	mu      sync.Mutex
	pollers map[string]*Poller
	merged  chan Sample
}

// NewManager creates an empty Manager.
func NewManager() *Manager {
	return &Manager{
		pollers: make(map[string]*Poller),
		merged:  make(chan Sample),
	}
}

// Watch starts polling target and folds its samples into the Manager's
// merged stream.
func (m *Manager) Watch(ctx context.Context, target string, interval time.Duration, probe func() (float64, error)) {
	p := NewPoller(ctx, target, interval, probe)

	m.mu.Lock()
	m.pollers[target] = p
	m.mu.Unlock()

	go func() {
		for s := range p.Results() {
			m.merged <- s
		}
		close(m.merged)
	}()
}

// Merged returns the channel carrying samples from every watched target.
func (m *Manager) Merged() <-chan Sample {
	return m.merged
}

// Forget stops watching target; the other targets keep running.
func (m *Manager) Forget(target string) {
	m.mu.Lock()
	delete(m.pollers, target)
	m.mu.Unlock()
}
