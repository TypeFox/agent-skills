// Package doctree is a miniature AST for a document markup language.
//
// A Document owns a tree of Nodes: the root is a "document", which contains
// "section" nodes, which contain "paragraph" (and nested "section") nodes.
// Every Node except the root has a container (its parent), and every Node knows
// the Document it belongs to. New and Assign build the tree and wire up the
// container and document back-pointers.
package doctree

// Kind classifies a Node.
type Kind string

const (
	KindDocument  Kind = "document"
	KindSection   Kind = "section"
	KindParagraph Kind = "paragraph"
)

// Node is a single element in the document tree.
type Node struct {
	Kind Kind
	Text string

	container *Node
	children  []*Node
	doc       *Document
}

// Document is a parsed document and the root of its Node tree.
type Document struct {
	URI  string
	Root *Node
}

// New assembles a Node of the given kind from already-built children, linking
// each child's container back to the new node. It does not set the Document;
// call Assign on the finished root for that.
func New(kind Kind, text string, children ...*Node) *Node {
	n := &Node{Kind: kind, Text: text, children: children}
	for _, c := range children {
		c.container = n
	}
	return n
}

// Assign builds a Document rooted at root and stamps every node in the subtree
// with a back-pointer to that Document.
func Assign(uri string, root *Node) *Document {
	doc := &Document{URI: uri, Root: root}
	var stamp func(*Node)
	stamp = func(n *Node) {
		n.doc = doc
		for _, c := range n.children {
			stamp(c)
		}
	}
	stamp(root)
	return doc
}
