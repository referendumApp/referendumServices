package repository

import (
	"fmt"
	"reflect"
	"strings"

	sq "github.com/Masterminds/squirrel"
)

func buildFilter(filter Filter) (sq.Sqlizer, error) {
	switch filter.Op {
	case Eq, In:
		return sq.Eq{filter.Column: filter.Value}, nil
	case NotEq:
		return sq.NotEq{filter.Column: filter.Value}, nil
	case Expr:
		return sq.Expr(fmt.Sprintf("%s = (?)", filter.Column), filter.Value), nil
	default:
		return nil, fmt.Errorf("unsupported operator: %s", filter.Op)
	}
}

func evalFilters(filters ...Filter) (sq.Sqlizer, error) {
	// If single filter, build and return it directly
	if len(filters) == 1 {
		return buildFilter(filters[0])
	}

	// Multiple filters: build an AND condition
	conditions := make([]sq.Sqlizer, 0, len(filters))

	for _, filter := range filters {
		condition, err := buildFilter(filter)
		if err != nil {
			return nil, err
		}
		conditions = append(conditions, condition)
	}

	return sq.And(conditions), nil
}

// TODO: Could eventually apply reflection here to optimize our read queries and not just get everything. Leaving this here now until it becomes a problem
func BuildSelectAll(entity TableEntity, schema string, filters ...Filter) (string, []any, error) {
	table := fmt.Sprintf("%s.%s", schema, entity.TableName())
	query := sq.Select("*").From(table).PlaceholderFormat(sq.Dollar)

	if len(filters) > 0 {
		filters, err := evalFilters(filters...)
		if err != nil {
			return "", nil, err
		}
		query = query.Where(filters)
	}

	return query.ToSql()
}

func BuildDeleteQuery(entity TableEntity, schema string, filters ...Filter) (string, []any, error) {
	table := fmt.Sprintf("%s.%s", schema, entity.TableName())
	query := sq.Delete(table).PlaceholderFormat(sq.Dollar)

	if len(filters) > 0 {
		filters, err := evalFilters(filters...)
		if err != nil {
			return "", nil, err
		}
		query = query.Where(filters)
	}

	return query.ToSql()
}

// Helper to dereference a reflect.Value if it's a pointer
func dereferenceValue(value reflect.Value) any {
	if value.Kind() == reflect.Ptr && !value.IsNil() {
		return value.Elem().Interface()
	}
	return value.Interface()
}

func getQueryMap(entity TableEntity) (map[string]any, error) {
	if entity == nil {
		return nil, fmt.Errorf("invalid input: entity must be provided")
	}

	// Use reflection to build the update query
	val := reflect.ValueOf(entity)
	if val.Kind() == reflect.Ptr {
		val = val.Elem()
	}

	if val.Kind() != reflect.Struct {
		return nil, fmt.Errorf("entity must be a struct or pointer to struct")
	}

	queryMap := make(map[string]any)

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

		queryMap[columnName] = dereferenceValue(field)
	}

	if len(queryMap) == 0 {
		return nil, fmt.Errorf("no fields to update")
	}

	return queryMap, nil
}

func BuildUpdateQuery(entity TableEntity, schema string, idFieldName string) (string, []any, error) {
	if idFieldName == "" {
		return "", nil, fmt.Errorf("invalid input: idFieldName must be provided")
	}

	updateMap, err := getQueryMap(entity)
	if err != nil {
		return "", nil, err
	}

	idValue, exists := updateMap[idFieldName]
	if !exists {
		return "", nil, fmt.Errorf("missing ID value for field %s", idFieldName)
	}

	delete(updateMap, idFieldName)

	query := sq.Update(entity.TableName()).
		SetMap(updateMap).
		Where(sq.Eq{idFieldName: idValue}).
		PlaceholderFormat(sq.Dollar)

	return query.ToSql()
}

func getInsertBuilder(entity TableEntity, schema string) (*sq.InsertBuilder, error) {
	insertMap, err := getQueryMap(entity)
	if err != nil {
		return nil, err
	}

	table := fmt.Sprintf("%s.%s", schema, entity.TableName())
	query := sq.Insert(table).SetMap(insertMap).PlaceholderFormat(sq.Dollar)

	return &query, nil
}

func BuildInsertQuery(entity TableEntity, schema string) (string, []any, error) {
	query, err := getInsertBuilder(entity, schema)
	if err != nil {
		return "", nil, err
	}

	return query.ToSql()
}

func BuildInsertWithReturnQuery(entity TableEntity, schema string, returnCol ...string) (string, []any, error) {
	if returnCol == nil {
		returnCol = []string{"*"}
	}

	query, err := getInsertBuilder(entity, schema)
	if err != nil {
		return "", nil, err
	}

	var returning strings.Builder
	returning.WriteString("RETURNING ")
	returning.WriteString(strings.Join(returnCol, ", "))

	return query.Suffix(returning.String()).ToSql()
}

func BuildInsertWithConflictQuery(entity TableEntity, schema string, conflictCol ...string) (string, []any, error) {
	if conflictCol == nil {
		return "", nil, fmt.Errorf("invalid input: conflict column must be provided")
	}

	insertMap, err := getQueryMap(entity)
	if err != nil {
		return "", nil, err
	}

	table := fmt.Sprintf("%s.%s", schema, entity.TableName())
	query := sq.Insert(table).SetMap(insertMap).PlaceholderFormat(sq.Dollar)

	var conflict strings.Builder
	for column := range insertMap {
		if conflict.Len() == 0 {
			conflict.WriteString("ON CONFLICT (")
			conflict.WriteString(strings.Join(conflictCol, ", "))
			conflict.WriteString(") DO UPDATE SET ")
			conflict.WriteString(fmt.Sprintf("%s = EXCLUDED.%s", column, column))
			continue
		}
		conflict.WriteString(fmt.Sprintf(", %s = EXCLUDED.%s", column, column))
	}

	return query.Suffix(conflict.String()).ToSql()
}
