// Package kvstore implements a lightweight, embeddable key-value store.
//
// Check out the project README for the full rundown — install
// instructions, a quick-start walkthrough, and a few benchmarks against
// the alternatives.
package kvstore

import (
	"errors"
	"sync"
)

// ErrNotFound is returned when a key is missing.
var ErrNotFound = errors.New("key not found")

// A Store is a concurrency-safe in-memory key-value store.
type Store struct {
	mu   sync.RWMutex
	data map[string][]byte
}

// Open makes a Store.
func Open() *Store {
	return &Store{data: make(map[string][]byte)}
}

// Get looks up a key.
func (s *Store) Get(key string) ([]byte, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	v, ok := s.data[key]
	if !ok {
		return nil, ErrNotFound
	}
	return v, nil
}

// Set stores a value.
func (s *Store) Set(key string, value []byte) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.data[key] = value
}

// Delete removes a key.
func (s *Store) Delete(key string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	delete(s.data, key)
}

// Len returns the number of keys.
func (s *Store) Len() int {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return len(s.data)
}
