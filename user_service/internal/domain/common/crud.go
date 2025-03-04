package common

// Interface for database queries
type CRUDProvider interface {
	Create() string
	Delete() string
	Query() string
	GetResult() any
}

type Operation int

const (
	OperationCreate Operation = iota
	OperationDelete
	OperationSelect
)

func (o Operation) String() string {
	switch o {
	case OperationCreate:
		return "create"
	case OperationDelete:
		return "delete"
	case OperationSelect:
		return "select"
	default:
		return "unknown"
	}
}
