package repository

type TableEntity interface {
	TableName() string
}

type MutationType string

const (
	CreateMutation MutationType = "create"
	UpdateMutation MutationType = "update"
	DeleteMutation MutationType = "delete"
)
