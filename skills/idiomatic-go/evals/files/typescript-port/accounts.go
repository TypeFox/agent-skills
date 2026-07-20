// Package accounts manages user accounts and registration.
package accounts

import (
	"encoding/json"
	"errors"
	"math/rand"
	"time"
)

const (
	STATUS_ACTIVE   = "active"
	STATUS_DISABLED = "disabled"
)

const DEFAULT_PAGE_SIZE = 20

// User is a user account record.
type User struct {
	Id        string
	Email     string
	Age       *int
	Nickname  *string
	IsActive  *bool
	ApiToken  string
	AvatarUrl string
	Status    string
	LastSeen  time.Time
}

func (this *User) GetId() string {
	return this.Id
}

func (this *User) GetEmail() string {
	return this.Email
}

func (this *User) SetEmail(email string) {
	this.Email = email
}

func (this *User) GetNickname() *string {
	return this.Nickname
}

// deactivateUser marks u inactive and disabled. Called on every user whose
// last-seen time is before a cutoff.
func deactivateUser(u User) {
	inactive := false
	u.IsActive = &inactive
	u.Status = STATUS_DISABLED
}

// IUserRepository reads and writes users from storage.
type IUserRepository interface {
	FindById(id string) (*User, error)
	Save(u *User) error
}

// IUserService is the account service API.
type IUserService interface {
	Register(email string) (*User, error)
	GetUser(id string) (*User, error)
	GetUserAsync(id string) chan *User
	ActiveUsers(page int) []User
	DeactivateStale(cutoff time.Time)
}

type userService struct {
	repo   IUserRepository
	active []User // users this service instance has loaded into memory
}

// NewUserService builds a user service over the given repository.
func NewUserService(repo IUserRepository) IUserService {
	return &userService{repo: repo}
}

func (self *userService) Register(email string) (*User, error) {
	if email == "" {
		return nil, errors.New("Email is required!")
	}
	active := true
	u := &User{
		Id:       GenerateApiToken(),
		Email:    email,
		IsActive: &active,
		ApiToken: GenerateApiToken(),
		Status:   STATUS_ACTIVE,
		LastSeen: time.Now(),
	}
	err := self.repo.Save(u)
	if err != nil {
		return nil, errors.New("Failed to save user: " + err.Error())
	}
	self.active = append(self.active, *u)
	return u, nil
}

func (self *userService) GetUser(id string) (*User, error) {
	u, err := self.repo.FindById(id)
	if err != nil {
		return nil, errors.New("Failed to get user: " + err.Error())
	}
	if u == nil {
		return nil, errors.New("User not found!")
	}
	return u, nil
}

func (self *userService) GetUserAsync(id string) chan *User {
	ch := make(chan *User)
	go func() {
		u, _ := self.repo.FindById(id)
		ch <- u
	}()
	return ch
}

// ActiveUsers returns one page of the users currently loaded in this
// service's in-memory cache, page 0 being the first page.
func (self *userService) ActiveUsers(page int) []User {
	start := page * DEFAULT_PAGE_SIZE
	if start >= len(self.active) {
		return nil
	}
	end := start + DEFAULT_PAGE_SIZE
	if end > len(self.active) {
		end = len(self.active)
	}
	return self.active[start:end]
}

// DeactivateStale marks cached users inactive if they haven't been seen since cutoff.
func (self *userService) DeactivateStale(cutoff time.Time) {
	for _, u := range self.active {
		if u.LastSeen.Before(cutoff) {
			deactivateUser(u)
		}
	}
}

// GenerateApiToken returns a random token used for API authentication.
func GenerateApiToken() string {
	const chars = "abcdef0123456789"
	b := make([]byte, 32)
	for i := range b {
		b[i] = chars[rand.Intn(len(chars))]
	}
	return string(b)
}

// ParseUserJson decodes a User from JSON bytes.
func ParseUserJson(data []byte) (*User, error) {
	var u User
	err := json.Unmarshal(data, &u)
	if err != nil {
		return nil, errors.New("Invalid user JSON: " + err.Error())
	}
	return &u, nil
}
