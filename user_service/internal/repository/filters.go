package repository

type Operator string

const (
	Eq    Operator = "="
	NotEq Operator = "!="
	In    Operator = "IN"
	Expr  Operator = "expr"
)

type Filter struct {
	Value  any
	Op     Operator
	Column string
}
