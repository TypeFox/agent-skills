---
name: arithmetics-dsl
description: Work with the Arithmetics calculator DSL (.calc) — a small language for defining named values and functions and evaluating expressions. Use when the user wants to write or edit arithmetics modules, define functions, or compute expressions in this DSL.
---

# Arithmetics DSL

A little calculator language. A file is a module that contains some definitions and some
expressions to evaluate.

## Basics

Start a file with a module declaration:

```
module myCalc
```

After that you can write definitions and evaluations. A definition gives a name to a value or a
function, and an evaluation is just an expression that gets computed.

```
def a: 5;
def b: 3;
def c: a + b;

a + c;
```

Functions take parameters in parentheses:

```
def square(x): x * x;
square(4);
```

Statements end with a semicolon.

## Expressions

Expressions support the usual arithmetic operators — addition, subtraction, multiplication,
division, power, and modulo. You can use parentheses to group things. Operators follow normal
math precedence, so multiplication binds tighter than addition and so on.

Numbers can be integers or decimals.

## Notes

- You can call other functions inside a definition, including building functions on top of other
  functions.
- Symbol names are fairly flexible.
