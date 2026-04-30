# Example Review

This is a worked example of a finished review using the format defined in `SKILL.md`. Use it to calibrate tone, depth, and the level of detail to put into `Rationale` sections.

The example reviews a hypothetical `UserService.ts`. The exact content is not important — pay attention to:

- How the **summary** characterizes the code in 2–4 sentences without restating every comment
- How **blocking issues** include both a concrete fix *and* a substantive rationale
- How **suggestions** are phrased as improvements rather than corrections
- How **praise** is specific (not "good code!") and points to a particular pattern or location

---

# Code Review: UserService.ts

## Summary

This service handles user authentication and profile management. The core logic is sound and well-organized, with clean separation between authentication, profile, and persistence concerns. However, there is a critical security issue with password handling that must be addressed before merge, and several opportunities to strengthen type safety. Error handling is inconsistent and would benefit from a uniform approach.

**Verdict:** `REQUEST_CHANGES`

## Statistics

- **Total Comments:** 7
- **Blocking Issues:** 2
- **Non-blocking Suggestions:** 3
- **Praise:** 2

## Prioritized Recommendations

1. **(Blocking)** Fix password comparison to use constant-time comparison
2. **(Blocking)** Add proper error handling for database operations
3. **(Non-blocking)** Replace `any` types with proper interfaces
4. **(Non-blocking)** Consider extracting validation logic into a dedicated module

---

## Detailed Feedback

### Blocking Issues

---

**issue (blocking, security): Password comparison vulnerable to timing attacks**

**Location:** `UserService.ts:L45`

**Original Code:**
```typescript
async validatePassword(input: string, stored: string): Promise<boolean> {
  return input === stored;
}
```

**Suggested Fix:**
```typescript
import { timingSafeEqual } from 'crypto';

async validatePassword(input: string, stored: string): Promise<boolean> {
  const inputBuffer = Buffer.from(input);
  const storedBuffer = Buffer.from(stored);

  if (inputBuffer.length !== storedBuffer.length) {
    return false;
  }

  return timingSafeEqual(inputBuffer, storedBuffer);
}
```

**Rationale:**
String comparison with `===` short-circuits at the first differing byte, which leaks information about how many leading characters matched. An attacker who can measure response times can determine the stored password one character at a time. `timingSafeEqual` from Node's crypto module performs constant-time comparison, eliminating this attack vector. This is table stakes for any authentication code, even when passwords are hashed — the hashes still need timing-safe comparison.

---

**issue (blocking): Unhandled promise rejection and incorrect return type**

**Location:** `UserService.ts:L28`

**Original Code:**
```typescript
async getUser(id: string): Promise<User> {
  const user = await this.db.query(`SELECT * FROM users WHERE id = $1`, [id]);
  return user.rows[0];
}
```

**Suggested Fix:**
```typescript
async getUser(id: string): Promise<User | null> {
  try {
    const result = await this.db.query(`SELECT * FROM users WHERE id = $1`, [id]);
    return result.rows[0] ?? null;
  } catch (error) {
    this.logger.error('Failed to fetch user', { id, error });
    throw new DatabaseError('Failed to fetch user', { cause: error });
  }
}
```

**Rationale:**
Two problems here. First, database errors propagate raw to the caller, which both crashes any caller that doesn't `try/catch` and leaks implementation details (driver-specific error shapes, query fragments) up the stack. Wrapping in a domain `DatabaseError` gives callers a stable contract. Second, the return type promises `User` but actually returns `undefined` when no user is found — the `?? null` plus `User | null` return type makes the nullable case explicit and forces callers to handle it.

---

### Suggestions & Improvements

---

**suggestion (non-blocking, types): Replace `any` with a proper input interface**

**Location:** `UserService.ts:L12`

**Original Code:**
```typescript
async createUser(data: any): Promise<User> {
```

**Suggested Improvement:**
```typescript
interface CreateUserInput {
  email: string;
  password: string;
  name?: string;
}

async createUser(data: CreateUserInput): Promise<User> {
```

**Rationale:**
`any` opts out of the type system entirely, allowing invalid data to flow into the database layer where errors will surface late and be hard to trace. A dedicated input interface gives compile-time validation, IDE autocomplete for callers, and serves as living documentation of what the method expects. Consider pairing with a runtime validator (zod, valibot) if `data` originates from an HTTP boundary.

---

**suggestion (non-blocking): Extract validation into a dedicated module**

**Location:** `UserService.ts:L60–95`

**Rationale:**
The `validateRegistration` method has grown to ~35 lines of branching validation logic embedded in the service. As the rules evolve, this will be where bugs hide. Extracting to `validators/registration.ts` (or, better, a schema-based validator like zod) keeps the service focused on orchestration and makes the rules independently testable.

---

### Praise

---

**praise: Excellent separation of concerns**

**Location:** `UserService.ts` (overall structure)

The service is cleanly organized — each method has a single responsibility, dependencies are injected through the constructor rather than imported as singletons, and the boundary between domain logic and persistence is clear. This will be easy to test and easy to evolve.

---

**praise: Clean async flow in registration**

**Location:** `UserService.ts:L50–60`

Using early returns for validation keeps the happy path unindented and easy to follow. The async/await usage avoids the nested `.then()` chains that often appear in code at this level of complexity.

---

## Additional Notes

Consider adding JSDoc to the public methods, especially documenting which errors can be thrown — this would pair well with the `DatabaseError` wrapping suggested above and give consumers a clear contract.

For input validation, a runtime validator like `zod` or `valibot` would compose nicely with the TypeScript interfaces and eliminate the manual validation code suggested for extraction.
