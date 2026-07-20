// Package userstore loads user records and serves them by ID.
package userstore

import (
	"encoding/json"
	"fmt"
	"os"
)

// User is a single user record.
type User struct {
	ID    string
	Email string
}

// Fetcher is the lookup surface exposed for callers that only read users.
type Fetcher interface {
	FetchUser(id string) User
}

// Store holds the loaded users in memory.
type Store struct {
	backend map[string]User
}

var _ Fetcher = (*Store)(nil)

// NewStore returns an empty Store.
func NewStore() *Store {
	return &Store{backend: map[string]User{}}
}

// Load reads a JSON array of users from path into the store.
func (s *Store) Load(path string) error {
	f, err := os.Open(path)
	if err != nil {
		return fmt.Errorf("Failed to load users from %s: %v.", path, err)
	}
	defer f.Close()

	var users []User
	if err := json.NewDecoder(f).Decode(&users); err != nil {
		return fmt.Errorf("Could not decode users file %s: %v.", path, err)
	}
	for _, u := range users {
		s.backend[u.ID] = u
	}
	return nil
}

// FetchUser returns the user with the given ID. If no such user exists it
// returns the zero User.
func (s *Store) FetchUser(id string) User {
	return s.backend[id]
}
