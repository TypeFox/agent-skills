---
name: domainmodel-dsl
description: Work with the Domain Model DSL (.dmodel) for describing data models — datatypes, entities, and their features. Use when the user wants to create or edit a domain model in this DSL.
---

# Domain Model DSL

A language for describing a data model as a set of datatypes and entities.

## Datatypes

Declare a primitive datatype with the `datatype` keyword:

```
datatype String
datatype Int
```

## Entities

An entity groups a set of features. Each feature has a name and a type:

```
entity Person {
    name: String
    age: Int
}
```

The type of a feature can be a datatype or another entity.

## Packages

You can group declarations inside a package:

```
package model {
    datatype String
    entity Person {
        name: String
    }
}
```

That's the core of the language — declare your datatypes, then your entities with their features.
