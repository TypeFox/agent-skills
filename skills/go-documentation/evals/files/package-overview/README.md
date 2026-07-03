# kvstore

[![Go Reference](https://pkg.go.dev/badge/example.com/go-documentation-evals/kvstore.svg)](https://pkg.go.dev/example.com/go-documentation-evals/kvstore)

**kvstore** is a tiny, dependency-free, concurrency-safe in-memory key-value
store for Go. It's the store I reach for in tests, small CLIs, and prototypes
where reaching for Redis or SQLite would be overkill.

## Why kvstore?

- **Zero dependencies** — just the standard library.
- **Concurrency-safe** — every operation is guarded by a `sync.RWMutex`, so you
  can share one `Store` across goroutines without your own locking.
- **Tiny API** — five methods, nothing to learn.

## Install

```bash
go get example.com/go-documentation-evals/kvstore
```

## Quick start

```go
package main

import (
	"fmt"

	"example.com/go-documentation-evals/kvstore"
)

func main() {
	s := kvstore.Open()
	s.Set("greeting", []byte("hello"))

	v, err := s.Get("greeting")
	if err != nil {
		panic(err)
	}
	fmt.Println(string(v)) // hello
}
```

## How it works

A `Store` wraps a `map[string][]byte` behind a read-write mutex. Reads
(`Get`, `Len`) take the read lock so they can run concurrently; writes
(`Set`, `Delete`) take the write lock. A missing key from `Get` returns the
sentinel `ErrNotFound` rather than an empty slice, so callers can tell "no such
key" apart from "the value is empty".

The store keeps everything in memory — there is no persistence. When the
process exits, the data is gone. That's intentional: kvstore is for ephemeral
state, not durable storage.

## License

MIT
