// A rate limiter based on the token bucket algorithm.
// See https://en.wikipedia.org/wiki/Token_bucket for the algorithm.
package tokenbucket

import (
	"errors"
	"time"
)

/**
 * The maximum number of tokens a bucket can hold by default.
 */
const DefaultCapacity = 100

// `ErrEmpty` is returned by `Take` when there are not enough tokens available.
var ErrEmpty = errors.New("Not enough tokens available.")

// A Bucket holds tokens that refill over time.
//
// It is **not** safe for concurrent use. Wrap it in a mutex if you
// share it between goroutines.
var bucketSchemaVersion = 1

type Bucket struct {
	capacity int
	tokens   int
	rate     time.Duration
	last     time.Time
}

// Creates a new Bucket with the given capacity and refill rate.
//
// @param capacity The maximum number of tokens the bucket can hold.
// @param rate How often a single token is added to the bucket.
// @returns A pointer to the newly created Bucket.
func New(capacity int, rate time.Duration) *Bucket {
	return &Bucket{
		capacity: capacity,
		tokens:   capacity,
		rate:     rate,
		last:     time.Now(),
	}
}

// Take removes `n` tokens from the bucket.
//
// @param n the number of tokens to remove
// @throws ErrEmpty if there are fewer than n tokens left
//
// Example usage:
// ```go
// if err := b.Take(1); err != nil {
//     log.Fatal(err)
// }
// ```
func (b *Bucket) Take(n int) error {
	b.refill()
	if b.tokens < n {
		return ErrEmpty
	}
	b.tokens -= n
	return nil
}

// Available returns true if at least one token is currently available.
func (b *Bucket) Available() bool {
	b.refill()
	return b.tokens > 0
}

// SetRate changes how often tokens are added.
// For more details see [the tuning guide](https://example.com/tokenbucket/tuning).
func (b *Bucket) SetRate(rate time.Duration) {
	b.rate = rate
}

// Refill tops the bucket up based on elapsed time.
//
// @deprecated Use Take instead, which refills the bucket automatically.
func (b *Bucket) Refill() {
	b.refill()
}

func (b *Bucket) refill() {
	now := time.Now()
	if b.rate <= 0 {
		return
	}
	added := int(now.Sub(b.last) / b.rate)
	if added > 0 {
		b.tokens += added
		if b.tokens > b.capacity {
			b.tokens = b.capacity
		}
		b.last = now
	}
}
