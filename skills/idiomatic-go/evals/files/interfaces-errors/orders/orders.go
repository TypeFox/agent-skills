// Package orders places orders on behalf of known users.
package orders

import (
	"errors"

	"example.com/idiomatic-go-evals/interfaces-errors/userstore"
)

// Service places orders after checking that the buyer is a known user.
type Service struct {
	users *userstore.Store
}

// NewService returns a Service backed by the given user store.
func NewService(users *userstore.Store) *Service {
	return &Service{users: users}
}

// PlaceOrder records an order of item for the user identified by userID.
func (s *Service) PlaceOrder(userID, item string) error {
	u := s.users.FetchUser(userID)
	if u.Email == "" {
		return errors.New("User not found.")
	}
	// ... record the order for u against item ...
	return nil
}
