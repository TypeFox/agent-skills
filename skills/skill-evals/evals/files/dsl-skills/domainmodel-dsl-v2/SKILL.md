---
name: domainmodel-dsl
description: Read, write, and modify Domain Model DSL files (.dmodel) — datatypes, entities with inheritance and multi-valued features, and nested packages with qualified cross-references. Use when the user wants to create, edit, explain, or debug a domain model in this DSL, including resolving references across packages.
---

# Domain Model DSL

A language for describing a data model: primitive **datatypes**, **entities** with **features**,
inheritance between entities, and **packages** that namespace declarations. A `.dmodel` file is a
flat sequence of top-level elements (packages or types); there is no module header.

## Top-level structure

A file is zero or more elements, each either a package or a type (a datatype or an entity):

```
datatype String
datatype Int

entity Person {
    name: String
}
```

## Syntax (EBNF)

```ebnf
domainmodel_file  = { top_level_element } ;

top_level_element = package | type ;

package           = "package", qualified_name, "{", { top_level_element }, "}" ;

type              = datatype | entity ;

datatype          = "datatype", identifier ;

entity            = "entity", identifier, [ extends_clause ], "{", { feature }, "}" ;
extends_clause    = "extends", qualified_name ;

feature           = [ "many" ], identifier, ":", qualified_name ;

qualified_name    = identifier, { ".", identifier } ;

identifier        = letter, { letter | digit | "_" } ;
letter            = "A" | "B" | ... | "Z" | "a" | "b" | ... | "z" ;
```

## Datatypes

A primitive type:

```
datatype String
```

## Entities, features, inheritance

An entity has a name, an optional supertype, and a block of features:

```
entity Person {
    name: String
    age: Int
}

entity Employee extends Person {
    salary: Int
}
```

- `extends <Entity>` — single inheritance; the supertype is referenced by its (qualified) name and
  must resolve to an entity.
- Each feature is `(<many>)? <name> : <Type>`. The type is a datatype or an entity, referenced by
  its (qualified) name.
- Prefix a feature with `many` to make it multi-valued (a collection):

```
entity Blog {
    title: String
    many posts: Post
}
```

## Packages and qualified names

`package <QualifiedName> { ... }` groups elements and can nest. A **qualified name** is one or
more identifiers joined by dots (`foo.bar.Baz`). References use qualified names to reach
declarations in other packages; from inside a package you may use a name relative to the current
scope:

```
datatype String

package complex {
    datatype Date
}

package blog {
    entity Post {
        title: String
        published: complex.Date
    }

    entity Comment {
        on: Post
    }
}
```

## Semantics and rules

- Every reference — a feature's type, an `extends` supertype — must resolve to a declaration,
  using qualified names across package boundaries.
- The same simple name may exist in different packages; the qualified name disambiguates
  (`big.Int` vs a top-level `Int`).
- Comments use `//` and `/* */`.

## When generating or modifying

- Declare datatypes and referenced entities before (or alongside) the entities that use them, and
  make sure every feature type and `extends` target resolves.
- Use `many` for collection-valued features.
- When adding an entity in a package, reference types in other packages by their qualified name.

## Example

```
datatype String

entity HasAuthor {
    author: String
}

entity Post extends HasAuthor {
    title: String
    content: String
    many comments: Comment
}

entity Comment extends HasAuthor {
    content: String
}
```
