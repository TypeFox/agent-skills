# Concurrency patterns reference

Patterns LLMs reach for incorrectly: when to use `context.Context`, how a goroutine exits, when channels beat mutexes (and vice versa), and the anti-patterns to recognize on review.

Contents:

- [The `context.Context` contract](#the-contextcontext-contract)
- [Every goroutine has an exit](#every-goroutine-has-an-exit)
- [The `for select` skeleton](#the-for-select-skeleton)
- [Channel direction in signatures](#channel-direction-in-signatures)
- [Buffered channels as semaphores; the leaky-buffer pattern](#buffered-channels-as-semaphores-the-leaky-buffer-pattern)
- [Mutex vs channel](#mutex-vs-channel)
- [`sync.Once`, `sync.WaitGroup`, `errgroup`](#synconce-syncwaitgroup-errgroup)
- [Channel-closing rules](#channel-closing-rules)
- [Pipelines and fan-out / fan-in](#pipelines-and-fan-out--fan-in)
- [Anti-patterns](#anti-patterns)

## The `context.Context` contract

`context.Context` is Go's cancellation, deadline, and request-scoped-value primitive for any operation that might want to stop early. Four roles:

1. **Creator.** The top of the call stack creates a context: `ctx := context.Background()` for a program's root, `ctx, cancel := context.WithCancel(parent)` for a child whose lifetime is shorter, `ctx, cancel := context.WithTimeout(parent, 5*time.Second)` for a bounded operation. The creator owns `cancel` and **must call it** — `defer cancel()` is the standard form.
2. **Passer.** Every function in the call chain takes `ctx` as its first parameter and passes it down unchanged (or wraps it for the call below if a shorter deadline applies).
3. **Canceller.** Whoever holds `cancel` calls it when the operation is done or no longer needed. Cancelling a parent cancels every descendant.
4. **Watcher.** A function that might block (I/O, channel receive, sleep) selects on `<-ctx.Done()` and returns `ctx.Err()` when it fires.

```go
func (s *Service) ProcessAll(ctx context.Context, ids []string) error {
    ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
    defer cancel()

    for _, id := range ids {
        if err := s.processOne(ctx, id); err != nil {
            return err  // cancel via defer; sibling work stops
        }
    }
    return nil
}
```

Never store a `Context` in a struct field. The context belongs to the call, not the receiver. If a long-lived object needs to know when to stop, give it an explicit `Stop()` method or a `done` channel — not a stored context.

## Every goroutine has an exit

A goroutine that doesn't exit is a leak. Goroutines that block forever on a channel that no one will send to keep their stack and any captured references alive for the program's lifetime. Before writing `go ...`, name the exit:

1. **Finite work.** The goroutine runs a function that returns. The simplest case — a single computation, then done.
2. **`<-ctx.Done()`.** The goroutine selects on `ctx.Done()` and returns when the context is cancelled.
3. **Close-channel signal.** The goroutine ranges over an input channel; when an upstream owner closes the channel, the range loop ends and the goroutine returns.
4. **`sync.WaitGroup` join.** The parent calls `wg.Add(n)` then `wg.Wait()`; each goroutine calls `wg.Done()` (often via `defer`) before exiting via one of the three forms above.

If you cannot say which one applies, do not start the goroutine.

## The `for select` skeleton

The most common shape for a long-running goroutine:

```go
func (w *Worker) run(ctx context.Context, in <-chan Job) {
    ticker := time.NewTicker(30 * time.Second)
    defer ticker.Stop()

    for {
        select {
        case <-ctx.Done():
            return
        case job, ok := <-in:
            if !ok {
                return  // input closed
            }
            w.handle(job)
        case <-ticker.C:
            w.heartbeat()
        }
    }
}
```

Three exits in one place: context cancelled, input closed, or external stop signal. The `ok` form on the channel receive distinguishes "value arrived" from "channel closed".

## Channel direction in signatures

Function parameters can constrain a channel to send-only or receive-only:

```go
// Send-only: producer writes, never reads.
func produce(out chan<- int) {
    defer close(out)
    for i := 0; i < 10; i++ {
        out <- i
    }
}

// Receive-only: consumer reads, never writes.
func consume(in <-chan int) {
    for n := range in {
        fmt.Println(n)
    }
}
```

Direction-restricted parameters are documentation the compiler enforces — a `chan<- int` parameter is a write-only contract at the type level. Use them at API boundaries.

## Buffered channels as semaphores; the leaky-buffer pattern

A buffered channel of capacity N is a semaphore for at most N concurrent operations:

```go
sem := make(chan struct{}, 10)

for _, work := range items {
    sem <- struct{}{}  // blocks if 10 are in flight
    go func(w Item) {
        defer func() { <-sem }()
        process(w)
    }(work)
}
```

The leaky-buffer free-list (from Effective Go) uses a buffered channel as a pool of reusable buffers; when the channel is full, new buffers are simply dropped and garbage-collected, which is fine because the channel capacity bounds memory regardless.

## Mutex vs channel

Use a **mutex** when many goroutines need read/write access to a single piece of shared state — a cache, a counter, a configuration table. The state has one owner; the mutex protects it.

Use a **channel** when a value passes ownership from one goroutine to another — a job, a result, a request/response. The value has a sequence of owners; the channel marks the handoff.

If you find yourself reaching for a mutex around a channel, or a channel around a mutex, the model is probably wrong. The two primitives express different relationships; pick the one that matches what the data does.

`sync.RWMutex` is for the case where reads vastly outnumber writes; the overhead of read-locking is higher than a plain `sync.Mutex` for moderate contention, so don't reach for it by default.

## `sync.Once`, `sync.WaitGroup`, `errgroup`

- `sync.Once` — runs an `Do(f)` call exactly once across all goroutines. Use for lazy initialization.
- `sync.WaitGroup` — counts goroutines; `Add(n)` before spawning, `Done()` (typically deferred) inside each, `Wait()` to block until all done. Use for fixed-shape fan-out where the spawned goroutines don't return values.
- `golang.org/x/sync/errgroup.Group` — `WaitGroup` plus error propagation and context cancellation. `g.Go(func() error {...})` spawns; the first non-nil error cancels the group's context and the call to `g.Wait()` returns it. Use when spawned goroutines return errors and you want fail-fast semantics.

```go
g, ctx := errgroup.WithContext(ctx)
for _, url := range urls {
    g.Go(func() error {
        return fetch(ctx, url)
    })
}
if err := g.Wait(); err != nil {
    return err
}
```

Capturing the loop variable in the closure is correct when the module uses Go 1.22+ loop semantics (`go 1.22` or later in `go.mod`). On older language versions, copy into the closure body (`u := url`) before calling `fetch`.

## Channel-closing rules

- **The sender closes the channel, never the receiver.** A receiver closing a channel can cause the sender's next send to panic.
- **Close exactly once.** Closing a closed channel panics. If multiple senders could close, coordinate via `sync.Once` or a separate close-signaling channel.
- **Closing means "no more values".** It does *not* mean "stop". Receivers continue to read buffered values; only after the buffer drains does `<-ch` return the zero value with `ok == false`.
- **Don't close to "signal stop".** Use `ctx.Done()` or a dedicated `done chan struct{}` for stop signals.

## Pipelines and fan-out / fan-in

A pipeline is a chain of stages connected by channels; each stage runs in its own goroutine, reads from an input channel, writes to an output channel, and closes the output when its input drains.

Fan-out: many goroutines read from one channel and produce on their own (or a shared) output channel.

Fan-in: many goroutines write to a shared output channel; a single coordinator closes it once all producers signal done (typically via `WaitGroup`).

A worked example is out of scope here; the patterns are documented in detail in Effective Go and Rob Pike's ["Go Concurrency Patterns"](https://go.dev/talks/2012/concurrency.slide) talk.

## Anti-patterns

Things to flag on review:

- **`time.Sleep` in tests** to wait for a goroutine to do something. Replace with a synchronization primitive (channel, `WaitGroup`, or a deterministic test hook).
- **Polling a channel** with a non-blocking `select { default: }` in a hot loop. Almost always wrong — use a blocking receive or `for select`.
- **`go f()` with no exit plan.** Fire-and-forget goroutines leak. Either the function is finite, or it watches `ctx.Done()`, or it ranges over a closeable channel.
- **Sharing a `sync.Mutex` by value.** The zero value of `sync.Mutex` is an unlocked mutex; passing one by value creates two independent mutexes that don't protect the same critical section. Always hold a `sync.Mutex` via a pointer-receiver method or as a field in a struct accessed via pointer.
- **Closing a channel from a receiver-side goroutine.** See channel-closing rules.
- **Storing `context.Context` in a struct.** See the context contract.
- **Calling `WaitGroup.Add` from inside the goroutine it counts.** `Add` must be called *before* the goroutine starts, to avoid a race with `Wait`.
