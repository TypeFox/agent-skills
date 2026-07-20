// Package aliases is a miniature type-alias language.
//
// A declaration "type A = B" makes A an alias of the type named B. Aliases can
// chain (A = B, B = C) and can form cycles (A = B, B = A). A Table holds the
// declared symbols; a Ref is the unresolved textual pointer from one alias to
// the name it targets. A Ref names a target by string; following it to the
// Symbol it points at is not implemented yet.
package aliases

// Symbol is a declared type name. A primitive (int, string) has no alias; an
// alias declaration carries a Ref to the name it points at.
type Symbol struct {
	Name  string
	alias *Ref
}

// Alias returns the reference this symbol aliases, or nil for a primitive.
func (s *Symbol) Alias() *Ref {
	if s == nil {
		return nil
	}
	return s.alias
}

// Ref is an unresolved reference to a Symbol by name.
type Ref struct {
	target string
	table  *Table
}

// Target returns the name this reference points at.
func (r *Ref) Target() string {
	if r == nil {
		return ""
	}
	return r.target
}

// Table holds the declared symbols of one program, keyed by name.
type Table struct {
	symbols map[string]*Symbol
}

// NewTable returns an empty Table.
func NewTable() *Table {
	return &Table{symbols: map[string]*Symbol{}}
}

// Ref creates an unresolved reference to the symbol named target.
func (t *Table) Ref(target string) *Ref {
	return &Ref{target: target, table: t}
}

// Lookup returns the symbol declared under name, or nil if there is none.
func (t *Table) Lookup(name string) *Symbol {
	return t.symbols[name]
}

// DefinePrimitive declares a symbol with no alias (e.g. int, string).
func (t *Table) DefinePrimitive(name string) *Symbol {
	s := &Symbol{Name: name}
	t.symbols[name] = s
	return s
}

// DefineAlias declares "type name = target". The returned symbol's Alias() is a
// Ref that must be resolved to reach the target symbol.
func (t *Table) DefineAlias(name, target string) *Symbol {
	s := &Symbol{Name: name, alias: t.Ref(target)}
	t.symbols[name] = s
	return s
}
