package database

import (
	"errors"
	"fmt"
	"reflect"
	"strings"

	sq "github.com/Masterminds/squirrel"
)

var ErrNoFields = errors.New("no fields found")

type TableEntity interface {
	TableName() string
}

// BuildSelect returns a select query with columns
func BuildSelect(entity TableEntity, schema string, filters ...sq.Sqlizer) (*sq.SelectBuilder, error) {
	table := schema + "." + entity.TableName()
	var cols []string

	if err := operateOnDBFields(entity, func(tags []string, field reflect.Value) error {
		columnName := tags[0]

		cols = append(cols, fmt.Sprintf("%s.%s", table, columnName))
		return nil
	}); err != nil {
		return nil, err
	}

	if len(cols) == 0 {
		return nil, ErrNoFields
	}

	query := sq.Select(cols...).From(table).PlaceholderFormat(sq.Dollar)

	for _, filter := range filters {
		query = query.Where(filter)
	}

	return &query, nil
}

// BuildSelectAll returns a select all query
func BuildSelectAll(entity TableEntity, schema string, filters ...sq.Sqlizer) (*sq.SelectBuilder, error) {
	table := schema + "." + entity.TableName()
	query := sq.Select("*").From(table).PlaceholderFormat(sq.Dollar)

	for _, filter := range filters {
		query = query.Where(filter)
	}

	return &query, nil
}

// BuildDeleteQuery returns a delete query
func BuildDeleteQuery(entity TableEntity, schema string, filters ...sq.Sqlizer) (*sq.DeleteBuilder, error) {
	table := schema + "." + entity.TableName()
	query := sq.Delete(table).PlaceholderFormat(sq.Dollar)

	for _, filter := range filters {
		query = query.Where(filter)
	}

	return &query, nil
}

type ExtendedUpdateBuilder struct {
	sq.UpdateBuilder
	updateMap map[string]any
}

// BuildUpdateQuery returns a update query
func BuildUpdateQuery(entity TableEntity, schema string, filters ...sq.Sqlizer) (*ExtendedUpdateBuilder, error) {
	if len(filters) == 0 {
		return nil, fmt.Errorf("invalid input: filters must be provided")
	}

	updateMap, err := getQueryMap(entity)
	if err != nil {
		return nil, err
	}

	table := schema + "." + entity.TableName()
	query := sq.Update(table).
		SetMap(updateMap).
		PlaceholderFormat(sq.Dollar)

	for _, filter := range filters {
		query = query.Where(filter)
	}

	return &ExtendedUpdateBuilder{query, updateMap}, nil
}

func (b *ExtendedUpdateBuilder) Returning(returnCols ...string) *ExtendedUpdateBuilder {
	b.UpdateBuilder = b.Suffix(buildReturning(returnCols...))
	return b
}

// BuildUpdateIncrementQuery returns a update query that increments a integer field
func BuildUpdateIncrementQuery(
	entity TableEntity,
	schema string,
	countField string,
	filters ...sq.Sqlizer,
) (*sq.UpdateBuilder, error) {
	if len(filters) == 0 {
		return nil, fmt.Errorf("invalid input: filters must be provided")
	}

	table := schema + "." + entity.TableName()
	query := sq.Update(table).
		Set(countField, sq.Expr(countField+" + 1")).
		PlaceholderFormat(sq.Dollar)

	for _, filter := range filters {
		query = query.Where(filter)
	}

	return &query, nil
}

// BuildUpdateDecrementQuery returns a update query that decrements a integer field
func BuildUpdateDecrementQuery(
	entity TableEntity,
	schema string,
	countField string,
	filters ...sq.Sqlizer,
) (*sq.UpdateBuilder, error) {
	if len(filters) == 0 {
		return nil, fmt.Errorf("invalid input: filters must be provided")
	}

	table := schema + "." + entity.TableName()
	query := sq.Update(table).
		Set(countField, sq.Expr(countField+" - 1")).
		PlaceholderFormat(sq.Dollar)

	for _, filter := range filters {
		query = query.Where(filter)
	}

	return &query, nil
}

type ExtendedInsertBuilder struct {
	sq.InsertBuilder
	insertMap map[string]any
}

// BuildInsertQuery returns a insert query
func BuildInsertQuery(entity TableEntity, schema string) (*ExtendedInsertBuilder, error) {
	insertMap, err := getQueryMap(entity)
	if err != nil {
		return nil, err
	}

	table := schema + "." + entity.TableName()
	query := sq.Insert(table).SetMap(insertMap).PlaceholderFormat(sq.Dollar)

	return &ExtendedInsertBuilder{query, insertMap}, nil
}

func (b *ExtendedInsertBuilder) Returning(returnCols ...string) *ExtendedInsertBuilder {
	b.InsertBuilder = b.Suffix(buildReturning(returnCols...))
	return b
}

func (b *ExtendedInsertBuilder) OnConflictDoUpdate(conflictCol []string) *ExtendedInsertBuilder {
	var conflict strings.Builder
	for column := range b.insertMap {
		if conflict.Len() == 0 {
			conflict.WriteString("ON CONFLICT (")
			conflict.WriteString(strings.Join(conflictCol, ", "))
			conflict.WriteString(") DO UPDATE SET ")
		} else {
			conflict.WriteString(", ")
		}
		conflict.WriteString(column)
		conflict.WriteString(" = ")
		conflict.WriteString("EXLUDED.")
		conflict.WriteString(column)
	}

	b.InsertBuilder = b.Suffix(conflict.String())

	return b
}

// BuildBatchInsertQuery returns a batch insert query
func BuildBatchInsertQuery(entities []TableEntity, schema string) (*ExtendedInsertBuilder, error) {
	if len(entities) == 0 {
		return nil, fmt.Errorf("no table entities provided for batch insert")
	}

	fstEnt := entities[0]
	queryMap, err := getQueryMap(fstEnt)
	if err != nil {
		return nil, err
	}

	colLen := len(queryMap)
	columns := make([]string, 0, colLen)
	values := make([]any, 0, colLen)
	for c, v := range queryMap {
		columns = append(columns, c)
		values = append(values, v)
	}

	table := schema + "." + fstEnt.TableName()
	query := sq.Insert(table).Columns(columns...).Values(values...).PlaceholderFormat(sq.Dollar)

	for _, entity := range entities[1:] {
		insertMap, err := getQueryMap(entity)
		if err != nil {
			return nil, err
		}

		values := make([]any, colLen)
		for i, c := range columns {
			values[i] = insertMap[c]
		}

		query = query.Values(values...)
	}

	return &ExtendedInsertBuilder{query, queryMap}, nil
}

type JoinEntity interface {
	LeftTable() string
	RightTable() string
	On() string
}

// BuildLeftJoinSelect returns a Left Join select builder object
func BuildLeftJoinSelect(entity JoinEntity, schema string, filters ...sq.Sqlizer) (*sq.SelectBuilder, error) {
	leftTbl := entity.LeftTable()
	rightTbl := entity.RightTable()
	var cols []string

	if err := operateOnJoinFields(entity, func(tags []string, join string, field reflect.Value) error {
		columnName := tags[0]

		var col string
		switch join {
		case "left":
			col = leftTbl + "." + columnName
		case "right":
			col = rightTbl + "." + columnName
		default:
			return fmt.Errorf("invalid 'join' tag: %s", join)
		}

		cols = append(cols, col)

		return nil
	}); err != nil {
		return nil, err
	}

	if len(cols) == 0 {
		return nil, ErrNoFields
	}

	query := sq.
		Select(cols...).
		From(schema + "." + leftTbl).
		LeftJoin(fmt.Sprintf("%s.%s ON %s", schema, rightTbl, entity.On())).
		PlaceholderFormat(sq.Dollar)

	for _, filter := range filters {
		query = query.Where(filter)
	}

	return &query, nil
}

// Helper to dereference a reflect.Value if it's a pointer
func dereferenceValue(value reflect.Value) any {
	if value.Kind() == reflect.Ptr && !value.IsNil() {
		return value.Elem().Interface()
	}
	return value.Interface()
}

func reflectEntity(entity any) (*reflect.Value, []reflect.StructField, error) {
	if entity == nil {
		return nil, nil, fmt.Errorf("invalid input: entity must be provided")
	}

	// Use reflection to build the update query
	val := reflect.ValueOf(entity)
	if val.Kind() == reflect.Ptr {
		val = val.Elem()
	}

	if val.Kind() != reflect.Struct {
		return nil, nil, fmt.Errorf("entity must be a struct or pointer to struct")
	}

	return &val, reflect.VisibleFields(val.Type()), nil
}

func operateOnJoinFields(entity JoinEntity, cb func(tags []string, join string, field reflect.Value) error) error {
	val, fields, err := reflectEntity(entity)
	if err != nil {
		return err
	}

	for _, fieldType := range fields {
		field := val.FieldByIndex(fieldType.Index)

		dbTag := fieldType.Tag.Get("db")
		if dbTag == "" || dbTag == "-" {
			continue
		}

		tagParts := strings.Split(dbTag, ",")

		joinTag := fieldType.Tag.Get("join")
		if joinTag == "" {
			return fmt.Errorf("missing 'join' tag for %s", tagParts[0])
		}

		if err := cb(tagParts, joinTag, field); err != nil {
			return err
		}
	}

	return nil
}

func operateOnDBFields(entity TableEntity, cb func(tags []string, field reflect.Value) error) error {
	val, fields, err := reflectEntity(entity)
	if err != nil {
		return err
	}

	for _, fieldType := range fields {
		field := val.FieldByIndex(fieldType.Index)

		dbTag := fieldType.Tag.Get("db")
		if dbTag == "" || dbTag == "-" {
			continue
		}

		tagParts := strings.Split(dbTag, ",")

		if err := cb(tagParts, field); err != nil {
			return err
		}
	}

	return nil
}

func getQueryMap(entity TableEntity) (map[string]any, error) {
	queryMap := make(map[string]any)

	if err := operateOnDBFields(entity, func(tags []string, field reflect.Value) error {
		columnName := tags[0]

		// Handle "omitempty" tag
		if len(tags) > 1 && tags[1] == "omitempty" {
			if field.Kind() == reflect.Ptr && field.IsNil() {
				return nil
			}
			if !field.IsValid() || field.IsZero() {
				return nil
			}
		}

		queryMap[columnName] = dereferenceValue(field)
		return nil
	}); err != nil {
		return nil, err
	}

	if len(queryMap) == 0 {
		return nil, ErrNoFields
	}

	return queryMap, nil
}

func buildReturning(cols ...string) string {
	var returning strings.Builder
	returning.WriteString("RETURNING ")
	if len(cols) > 0 {
		returning.WriteString(strings.Join(cols, ", "))
	} else {
		returning.WriteString("*")
	}

	return returning.String()
}
