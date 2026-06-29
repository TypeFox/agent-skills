---
name: statemachine-dsl
description: Read, write, and modify Statemachine DSL files (.statemachine). Use when the user wants to create, edit, explain, or debug a state machine written in this textual DSL — defining states, events, commands, and transitions, or generating a machine from a description.
---

# Statemachine DSL

A small textual language for describing finite state machines: a named machine, the events it
recognizes, optional commands, an initial state, and a set of states connected by transitions.

## File structure

A file is one machine, in this fixed order:

```
statemachine <Name>

events
    <eventName>
    <eventName>

commands
    <commandName>

initialState <StateName>

state <StateName>
    actions { <commandName> }
    <eventName> => <TargetStateName>
end
```

- `statemachine <Name>` — required header naming the machine. `<Name>` is an identifier
  (`[_a-zA-Z][\w_]*`).
- `events` — optional block listing one or more event names, one per line (whitespace separated).
- `commands` — optional block listing one or more command names.
- `initialState <StateName>` — required; must reference a state defined in the file.
- `state ... end` — zero or more state definitions.

## Syntax (EBNF)

```ebnf
statemachine_file = "statemachine", identifier,
                    [ events_block ], [ commands_block ],
                    "initialState", state_ref,
                    { state } ;

events_block      = "events", { event_name } ;
commands_block    = "commands", { command_name } ;

state             = "state", identifier,
                    [ actions_clause ],
                    { transition },
                    "end" ;

actions_clause    = "actions", "{", { command_ref }, "}" ;
transition        = event_ref, "=>", state_ref ;

event_name        = identifier ;
command_name      = identifier ;
event_ref         = identifier ;   (* must match a declared event *)
command_ref       = identifier ;   (* must match a declared command *)
state_ref         = identifier ;   (* must match a defined state *)

identifier        = letter, { letter | digit | "_" } ;
letter            = "A" | "B" | ... | "Z" | "a" | "b" | ... | "z" ;
```

There is **no** closing `end` for the whole machine — only each `state` block ends with `end`.

## States and transitions

Each state is a `state <Name> ... end` block containing:

- An optional `actions { <command> ... }` clause listing one or more command names to run while in
  the state. Every command named here must be declared in the `commands` block.
- Zero or more transitions, each written `<event> => <targetState>`. The event must be declared in
  the `events` block; the target must be a state defined in the file.

## Semantics and rules

- Names are case-sensitive identifiers.
- Every cross-reference must resolve: `initialState`, transition events, transition targets, and
  `actions` commands all point to declarations elsewhere in the file. A reference with no matching
  declaration is an error.
- A state may have multiple transitions, typically one per relevant event. Two transitions on the
  same event from the same state are ambiguous — avoid them.
- Comments use `//` (line) and `/* */` (block).

## Example

```
statemachine TrafficLight

events
    switchCapacity
    next

initialState PowerOff

state PowerOff
    switchCapacity => RedLight
end

state RedLight
    switchCapacity => PowerOff
    next => GreenLight
end

state GreenLight
    switchCapacity => PowerOff
    next => YellowLight
end

state YellowLight
    switchCapacity => PowerOff
    next => RedLight
end
```

## When generating or modifying

- Declare every event and command before referencing it.
- Make sure `initialState` and every transition target name an existing `state`.
- When adding a state, give it at least the transitions needed to keep the machine reachable and
  not trap the user in a dead end unless that is intended.
