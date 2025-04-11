package database

import (
	"errors"
	"fmt"
	"reflect"
	"strings"

	sq "github.com/Masterminds/squirrel"
)

var ErrNoMappedFields = errors.New("no fields to update")

type TableEntity interface {
	TableName() string
}

// TODO: Could eventually apply reflection here to optimize our read queries and not just get everything. Leaving this here now until it becomes a problem
func BuildSelect(entity TableEntity, schema string, cols []string, filters ...sq.Sqlizer) (*sq.SelectBuilder, error) {
	table := fmt.Sprintf("%s.%s", schema, entity.TableName())
	query := sq.Select(cols...).From(table).PlaceholderFormat(sq.Dollar)

	for _, filter := range filters {
		query = query.Where(filter)
	}

	return &query, nil
}

func BuildSelectAll(entity TableEntity, schema string, filters ...sq.Sqlizer) (*sq.SelectBuilder, error) {
	table := fmt.Sprintf("%s.%s", schema, entity.TableName())
	query := sq.Select("*").From(table).PlaceholderFormat(sq.Dollar)

	for _, filter := range filters {
		query = query.Where(filter)
	}

	return &query, nil
}

func BuildDeleteQuery(entity TableEntity, schema string, filters ...sq.Sqlizer) (*sq.DeleteBuilder, error) {
	table := fmt.Sprintf("%s.%s", schema, entity.TableName())
	query := sq.Delete(table).PlaceholderFormat(sq.Dollar)

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

func operateOnFields(entity TableEntity, cb func(col string, field reflect.Value) error) error {
	if entity == nil {
		return fmt.Errorf("invalid input: entity must be provided")
	}

	// Use reflection to build the update query
	val := reflect.ValueOf(entity)
	if val.Kind() == reflect.Ptr {
		val = val.Elem()
	}

	if val.Kind() != reflect.Struct {
		return fmt.Errorf("entity must be a struct or pointer to struct")
	}

	fields := reflect.VisibleFields(val.Type())

	for _, fieldType := range fields {
		field := val.FieldByIndex(fieldType.Index)

		dbTag := fieldType.Tag.Get("db")
		if dbTag == "" || dbTag == "-" {
			continue
		}

		tagParts := strings.Split(dbTag, ",")
		columnName := tagParts[0]

		// Handle "omitempty" tag
		if len(tagParts) > 1 && tagParts[1] == "omitempty" {
			if field.Kind() == reflect.Ptr && field.IsNil() {
				continue
			}
			if !field.IsValid() || field.IsZero() {
				continue
			}
		}

		if err := cb(columnName, field); err != nil {
			return err
		}
	}

	return nil
}

func getQueryMap(entity TableEntity) (map[string]any, error) {
	queryMap := make(map[string]any)

	if err := operateOnFields(entity, func(col string, field reflect.Value) error {
		queryMap[col] = dereferenceValue(field)
		return nil
	}); err != nil {
		return nil, err
	}

	if len(queryMap) == 0 {
		return nil, ErrNoMappedFields
	}

	return queryMap, nil
}

func BuildUpdateQuery(entity TableEntity, schema string, idFieldName string) (*sq.UpdateBuilder, error) {
	if idFieldName == "" {
		return nil, fmt.Errorf("invalid input: idFieldName must be provided")
	}

	updateMap, err := getQueryMap(entity)
	if err != nil {
		return nil, err
	}

	idValue, exists := updateMap[idFieldName]
	if !exists {
		return nil, fmt.Errorf("missing ID value for field %s", idFieldName)
	}

	delete(updateMap, idFieldName)

	table := fmt.Sprintf("%s.%s", schema, entity.TableName())
	query := sq.Update(table).
		SetMap(updateMap).
		Where(sq.Eq{idFieldName: idValue}).
		PlaceholderFormat(sq.Dollar)

	return &query, nil
}

func BuildInsertQuery(entity TableEntity, schema string) (*sq.InsertBuilder, error) {
	fstMap, err := getQueryMap(entity)
	if err != nil {
		return nil, err
	}

	table := fmt.Sprintf("%s.%s", schema, entity.TableName())
	query := sq.Insert(table).SetMap(fstMap).PlaceholderFormat(sq.Dollar)

	return &query, nil
}

func BuildInsertWithReturnQuery(entity TableEntity, schema string, returnCol ...string) (*sq.InsertBuilder, error) {
	if returnCol == nil {
		returnCol = []string{"*"}
	}

	query, err := BuildInsertQuery(entity, schema)
	if err != nil {
		return nil, err
	}

	var returning strings.Builder
	returning.WriteString("RETURNING ")
	returning.WriteString(strings.Join(returnCol, ", "))

	returnQuery := query.Suffix(returning.String())

	return &returnQuery, nil
}

func BuildInsertWithConflictQuery(entity TableEntity, schema string, conflictCol ...string) (*sq.InsertBuilder, error) {
	if conflictCol == nil {
		return nil, fmt.Errorf("invalid input: conflict column must be provided")
	}

	fstMap, err := getQueryMap(entity)
	if err != nil {
		return nil, err
	}

	table := fmt.Sprintf("%s.%s", schema, entity.TableName())
	query := sq.Insert(table).SetMap(fstMap).PlaceholderFormat(sq.Dollar)

	var conflict strings.Builder
	for column := range fstMap {
		if conflict.Len() == 0 {
			conflict.WriteString("ON CONFLICT (")
			conflict.WriteString(strings.Join(conflictCol, ", "))
			conflict.WriteString(") DO UPDATE SET ")
			conflict.WriteString(fmt.Sprintf("%s = EXCLUDED.%s", column, column))
			continue
		}
		conflict.WriteString(fmt.Sprintf(", %s = EXCLUDED.%s", column, column))
	}

	conQuery := query.Suffix(conflict.String())

	return &conQuery, nil
}

func BuildBatchInsertQuery(entities []TableEntity, schema string) (*sq.InsertBuilder, error) {
	if len(entities) == 0 {
		return nil, fmt.Errorf("no table entities provided for batch insert")
	}

	fstEnt := entities[0]
	fstMap, err := getQueryMap(fstEnt)
	if err != nil {
		return nil, err
	}

	colLen := len(fstMap)
	columns := make([]string, 0, colLen)
	values := make([]any, 0, colLen)
	for c, v := range fstMap {
		columns = append(columns, c)
		values = append(values, v)
	}

	table := fmt.Sprintf("%s.%s", schema, fstEnt.TableName())
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

	return &query, nil
}
