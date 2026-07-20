// Package slug converts arbitrary text into URL-friendly slugs.
//
// Usage:
// ```go
// s := slug.New()
// fmt.Println(s.Make("Hello, World!")) // hello-world
// ```
package slug

import (
	"strings"
	"unicode"
)

// A Slugifier converts strings to slugs using a configurable separator.
type Slugifier struct {
	// Separator is placed between words. Defaults to "-" when empty.
	Separator string
}

// New returns a Slugifier that joins words with "-".
func New() *Slugifier {
	return &Slugifier{Separator: "-"}
}

// Make converts s into a slug: it lowercases the text, splits it on any run of
// non-alphanumeric characters, and joins the pieces with the separator.
//
// @example
//   New().Make("Hello, World!")      // => "hello-world"
//
// @example <caption>WithNumbers</caption>
//   New().Make("foo_bar 123")        // => "foo-bar-123"
func (sl *Slugifier) Make(s string) string {
	sep := sl.Separator
	if sep == "" {
		sep = "-"
	}
	var words []string
	var cur strings.Builder
	for _, r := range s {
		if unicode.IsLetter(r) || unicode.IsDigit(r) {
			cur.WriteRune(unicode.ToLower(r))
		} else if cur.Len() > 0 {
			words = append(words, cur.String())
			cur.Reset()
		}
	}
	if cur.Len() > 0 {
		words = append(words, cur.String())
	}
	return strings.Join(words, sep)
}

// Make is a convenience wrapper that slugifies s with the default separator.
//
// @example
//   slug.Make("  Go & TypeScript  ") // => "go-typescript"
func Make(s string) string {
	return New().Make(s)
}
