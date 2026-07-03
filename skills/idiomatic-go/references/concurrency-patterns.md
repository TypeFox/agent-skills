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
- [Idempotent shutdown against concurrent registration](#idempotent-shutdown-against-concurrent-registration)
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

**This rule applies to every type in the design, not just the one under direct discussion.** A coordinating `Manager` that owns and starts several `Worker`s is bound by it exactly as much as the `Worker` itself — fixing a stored context on the leaf type while leaving it on the type that supervises the leaves is not a fix, it's a partial one. When reviewing or refactoring, re-check *every* struct in the file for a stored `context.Context` field, not only the one the task description names.

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

## Idempotent shutdown against concurrent registration

Any long-lived coordinator that hands out live channels tied to its own lifetime — a pub-sub hub, a file watcher, a streaming-RPC fan-out — and can also be torn down, has two obligations at once, and it's easy to satisfy only the obvious one:

- **Shutdown must be safe to call twice.** Closing a closed channel panics, so a second shutdown call must be a no-op, not a repeat close. `sync.Once` is the standard tool.
- **Shutdown and registration must not race.** If registering a new subscriber can happen concurrently with (or after) shutdown closing every existing subscriber channel, the new one never gets closed, or — worse — a send to it after shutdown has already run panics with "send on closed channel". A closed flag checked *under the same lock* that guards registration and closing is what closes this gap; checking `ctx.Done()` alone does not, because there's a window between the context firing and every in-flight registration/send finishing.

```go
type Broadcaster struct {
    mu          sync.Mutex
    subscribers map[chan Event]struct{}
    closed      bool
    closeOnce   sync.Once
}

func (b *Broadcaster) Subscribe() <-chan Event {
    ch := make(chan Event, 1)
    b.mu.Lock()
    defer b.mu.Unlock()
    if b.closed {
        close(ch) // already shut down: hand back a closed channel, never panic
        return ch
    }
    b.subscribers[ch] = struct{}{}
    return ch
}

func (b *Broadcaster) publish(e Event) {
    b.mu.Lock()
    defer b.mu.Unlock()
    if b.closed { // Close already closed every channel below; don't send to them
        return
    }
    for ch := range b.subscribers {
        select {
        case ch <- e:
        default: // slow subscriber; drop rather than block the broadcaster
        }
    }
}

func (b *Broadcaster) Close() {
    b.closeOnce.Do(func() { // safe to call Close() any number of times
        b.mu.Lock()
        defer b.mu.Unlock()
        b.closed = true
        for ch := range b.subscribers {
            close(ch)
        }
        b.subscribers = nil
    })
}
```

The two obligations reinforce each other: `closeOnce` makes the *close* idempotent, and checking `closed` under `mu` in both `Subscribe()` and `publish()` makes the *interaction* with concurrent callers race-free — neither alone is sufficient. The method names here are illustrative; the same shape applies under whatever a domain calls them (`Watch`/`Stop`, `Listen`/`Shutdown`, `Register`/`Close`) — the obligations attach to the *shape* (hand out a live channel, later close it, possibly concurrently), not to any particular name.

**Do not split the guard check from the side effect it guards across two lock acquisitions.** A tempting-looking variant checks `closed` under the lock, unlocks, then does the "expensive-looking" work (starting a goroutine, allocating a worker) before re-locking to register it:

```go
// Wrong: the guard and the registration are two separate critical sections.
func (m *Manager) Watch(ctx context.Context, name string, /* ... */) {
    m.mu.Lock()
    if m.closed {
        m.mu.Unlock()
        return
    }
    m.mu.Unlock() // <-- window opens here

    w := newWorker(ctx, name /* ... */) // Stop() can run entirely in this window

    m.mu.Lock()
    m.workers[name] = w // too late: Stop() already closed the shared channel
    m.mu.Unlock()
}
```

Between the two lock scopes, a concurrent `Stop()`/`Close()` can run to completion — snapshot the (still-empty-of-this-worker) registry, wait on it, and close the shared channel — before the new worker is ever registered, so its first send panics with "send on closed channel". Starting a goroutine is O(1) and non-blocking, so there is no performance reason to release the lock before doing it; the rule against long-held locks is about *blocking* work (I/O, the `probe()`/handler call itself), not about a `go` statement. Keep the check, the side effect, and the bookkeeping that lets shutdown find and wait for that side effect inside **one** uninterrupted critical section.

## Pipelines and fan-out / fan-in

A pipeline is a chain of stages connected by channels; each stage runs in its own goroutine, reads from an input channel, writes to an output channel, and closes the output when its input drains.

Fan-out: many goroutines read from one channel and produce on their own (or a shared) output channel.

Fan-in: many goroutines write to a shared output channel; a single coordinator closes it once all producers signal done (typically via `WaitGroup`) — never by having each producer close the shared channel itself, which double-closes (panics) the moment more than one producer is active.

The two previous sections compose directly into the common case of a coordinator that both fans in *and* accepts new producers for as long as it's running — e.g. a `Manager` that supervises an open-ended, add/remove-at-any-time set of named workers and merges their output onto one stream:

```go
type Manager struct {
    mu       sync.Mutex
    workers  map[string]*Worker
    merged   chan Item
    closed   bool
    wg       sync.WaitGroup
    stopOnce sync.Once
}

func NewManager() *Manager {
    return &Manager{workers: make(map[string]*Worker), merged: make(chan Item)}
}

// Watch starts a worker called name and folds its output into the merged
// stream. It is a no-op once Stop has been called.
func (m *Manager) Watch(ctx context.Context, name string) {
    m.mu.Lock()
    if m.closed {
        m.mu.Unlock()
        return
    }
    w := newWorker(ctx, name) // cheap: allocates and starts a goroutine, doesn't block
    m.workers[name] = w
    m.wg.Add(1)
    m.mu.Unlock() // check, start, and registration all happened under one lock

    go func() {
        defer m.wg.Done()
        for item := range w.Results() {
            select {
            case m.merged <- item:
            case <-ctx.Done():
                return
            }
        }
    }()
}

// Stop stops every watched target and closes the merged stream exactly
// once. Safe to call any number of times, and race-free against a
// concurrent Watch: a racing Watch either wins the lock first (and Stop's
// WaitGroup then waits for it too) or sees m.closed and never starts.
func (m *Manager) Stop() {
    m.stopOnce.Do(func() {
        m.mu.Lock()
        m.closed = true
        workers := make([]*Worker, 0, len(m.workers))
        for _, w := range m.workers {
            workers = append(workers, w)
        }
        m.mu.Unlock()

        for _, w := range workers {
            w.Stop()
        }
        m.wg.Wait() // every forwarder goroutine above has returned from its range loop
        close(m.merged)
    })
}
```

`sync.Once` makes `Stop` itself idempotent; the `closed` flag checked in the same critical section as registration makes it race-free against `Watch`; the `WaitGroup` makes the fan-in close-exactly-once regardless of how many targets were ever watched. Dropping any one of the three reopens one of the bugs above. Further depth on plain fan-out/fan-in (no concurrent registration) is in Effective Go and Rob Pike's ["Go Concurrency Patterns"](https://go.dev/talks/2012/concurrency.slide) talk.

## Anti-patterns

Things to flag on review:

- **`time.Sleep` in tests** to wait for a goroutine to do something. Replace with a synchronization primitive (channel, `WaitGroup`, or a deterministic test hook).
- **Polling a channel** with a non-blocking `select { default: }` in a hot loop. Almost always wrong — use a blocking receive or `for select`.
- **`go f()` with no exit plan.** Fire-and-forget goroutines leak. Either the function is finite, or it watches `ctx.Done()`, or it ranges over a closeable channel.
- **Sharing a `sync.Mutex` by value.** The zero value of `sync.Mutex` is an unlocked mutex; passing one by value creates two independent mutexes that don't protect the same critical section. Always hold a `sync.Mutex` via a pointer-receiver method or as a field in a struct accessed via pointer. This is a special case of SKILL.md's "Value semantics" gap: a mutex is exactly the kind of field a struct copy silently duplicates instead of sharing.
- **Closing a channel from a receiver-side goroutine.** See channel-closing rules.
- **Storing `context.Context` in a struct.** See the context contract — and check every type in the file, not only the one the task names.
- **A shutdown method that panics on a second call, or that races a concurrent registration call.** See idempotent shutdown.
- **Checking a guard under a lock, releasing it, then performing and registering the guarded action under a second, later lock.** The window between the two critical sections is exactly where a concurrent shutdown can invalidate the guard. See idempotent shutdown and the fan-in worked example.
- **Calling `WaitGroup.Add` from inside the goroutine it counts.** `Add` must be called *before* the goroutine starts, to avoid a race with `Wait`.
