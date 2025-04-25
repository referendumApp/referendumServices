import hashlib
import logging
from enum import Enum
from typing import Dict, List, Optional, Set

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text
from sqlalchemy.orm.session import Session

logger = logging.getLogger(__name__)


class TransformationFunction(str, Enum):
    KEEP_COLUMNS = "keep_columns"
    RENAME = "rename"
    DUPLICATE = "duplicate"
    ADD_URL = "add_url"
    HASH = "hash"
    MAP = "map"


class Transformation(BaseModel):
    function: TransformationFunction
    parameters: Dict

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        try:
            match self.function:
                case TransformationFunction.KEEP_COLUMNS:
                    columns = self.parameters.get("columns", [])
                    missing_cols = set(columns) - set(df.columns)
                    if missing_cols:
                        raise ValueError(f"Columns not found in DataFrame: {missing_cols}")

                    return df[columns]

                case TransformationFunction.RENAME:
                    columns = self.parameters.get("columns", {})

                    return df.rename(columns=columns)

                case TransformationFunction.DUPLICATE:
                    source_name = self.parameters.get("source_name")
                    destination_name = self.parameters.get("destination_name")
                    if source_name not in df.columns:
                        raise ValueError(f"Source column '{source_name}' not found")
                    df = df.copy()
                    df[destination_name] = df[source_name]

                    return df

                case TransformationFunction.ADD_URL:
                    source_name = self.parameters.get("source_name")
                    destination_name = self.parameters.get("destination_name")
                    base_url = "https://s3.amazonaws.com/ballotpedia-api4/files/thumbs/200/300/"
                    if source_name not in df.columns:
                        raise ValueError(f"Source column '{source_name}' not found")

                    df = df.copy()
                    df[destination_name] = base_url + df[source_name] + ".jpg"

                    return df

                case TransformationFunction.HASH:
                    source_name = self.parameters.get("source_name")
                    destination_name = self.parameters.get("destination_name")
                    if source_name not in df.columns:
                        raise ValueError(f"Source column '{source_name}' not found")

                    df = df.copy()
                    df[destination_name] = df[source_name].apply(
                        lambda x: hashlib.sha256(str(x).encode()).hexdigest()
                    )
                    return df

                case TransformationFunction.MAP:
                    source_name = self.parameters.get("source_name")
                    destination_name = self.parameters.get("destination_name")
                    if source_name not in df.columns:
                        raise ValueError(f"Source column '{source_name}' not found")
                    mapping_dict = self.parameters.get("mapping")
                    mapping_dict = {int(k): v for k, v in mapping_dict.items()}

                    df = df.copy()
                    df[destination_name] = df[source_name].map(mapping_dict)

                    if default_value := self.parameters.get("default", None):
                        df[destination_name].fillna(default_value, inplace=True)

                    return df

                case _:
                    raise ValueError(f"Unsupported transformation: {self.function}")

        except Exception as e:
            logger.error(f"Error in transformation {self.function}: {str(e)}")
            raise


class JoinType(str, Enum):
    LEFT = "LEFT JOIN"
    RIGHT = "RIGHT JOIN"
    INNER = "INNER JOIN"
    OUTER = "OUTER JOIN"


class JoinConfig(BaseModel):
    join_type: JoinType
    table: str
    on: str | tuple
    columns: Set[str]

    def _query_validation(self, source_columns: Set[str]):
        join_column = self.on[0] if isinstance(self.on, tuple) else self.on
        if join_column not in source_columns:
            raise ValueError(
                f"The joined column {self.on} does not exist in the source columns: {source_columns}"
            )

        if any(col in source_columns for col in self.columns):
            raise ValueError(
                f"""Duplicate columns from the joined table detected
                joined_columns: {self.columns}
                source_columns: {source_columns}"""
            )

    def _get_join_source_query(self, source: str, source_columns: Set[str]) -> str:
        source_alias = source.split(" AS ")[-1].strip() if ") AS " in source else source
        formatted_src_cols = {f"{source_alias}.{src_col}" for src_col in source_columns}
        columns = ", ".join(sorted(formatted_src_cols.union(self.columns)))

        if isinstance(self.on, tuple):
            join_condition = f"{source_alias}.{self.on[0]} = {self.table}.{self.on[1]}"
        else:
            join_condition = f"{source_alias}.{self.on} = {self.table}.{self.on}"

        return f"""SELECT {columns} 
                  FROM {source} 
                  {self.join_type.value} {self.table} 
                  ON {join_condition}"""


class ETLConfig(BaseModel):
    source: str
    source_columns: Set[str]
    destination: str
    destination_columns: List[str]
    join_config: Optional[JoinConfig] = None
    transformations: List[Transformation]
    unique_constraints: List[str] = Field(default=["id"])
    dataframe: Optional[pd.DataFrame] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def _get_source_query(self, join_config: Optional[JoinConfig]) -> str:
        """Generate SQL query for source data extraction"""
        # Check if source is a subquery by looking for ') AS' pattern
        is_subquery = ") AS " in self.source
        source_alias = self.source.split(" AS ")[-1].strip() if is_subquery else self.source

        if join_config:
            join_config._query_validation(source_columns=self.source_columns)
            source_query = join_config._get_join_source_query(
                source=self.source,
                source_columns=self.source_columns,
            )
        else:
            if is_subquery:
                columns = ", ".join(f"{source_alias}.{col}" for col in sorted(self.source_columns))
            else:
                columns = ", ".join(sorted(self.source_columns))
            source_query = f"SELECT {columns} FROM {self.source}"

        return source_query

    def extract(self, conn: Session):
        query = self._get_source_query(join_config=self.join_config)
        logger.info(query)
        try:
            self.dataframe = pd.read_sql(query, con=conn)
        except Exception as e:
            logger.error(f"Error reading data with query '{query}': {e}")
            raise

    def transform(self) -> None:
        """Apply all transformations to the dataframe"""
        if self.dataframe is None:
            raise ValueError(f"No dataframe provided for {self.source}")

        try:
            df = self.dataframe
            for transform in self.transformations:
                df = transform.apply(df)
            self.dataframe = df
        except Exception as e:
            logger.error(f"Error transforming {self.source}: {str(e)}")
            raise

    def validate_and_log_constraint_violations(self, temp_table_name, constraints):
        """
        Validates that data in the temporary table satisfies constraints before upserting.

        Args:
            temp_table_name (str): Name of the temporary table
            constraints (dict): Dictionary of constraints to check with format:
                                { 'column_name': {'type': 'not_null'/'unique'/'foreign_key', 'reference': 'table.column'} }

        Returns:
            tuple: (valid_rows_count, invalid_rows_count, violations_log)
        """
        violations_log = []
        engine = self.get_engine()

        with engine.connect() as connection:
            # Start a transaction
            with connection.begin():
                # Check for NOT NULL constraint violations
                for column, constraint in constraints.items():
                    if constraint.get("type") == "not_null":
                        query = f"""
                            SELECT * FROM {temp_table_name} 
                            WHERE {column} IS NULL;
                        """
                        result = connection.execute(text(query))
                        null_rows = result.fetchall()

                        for row in null_rows:
                            violation = {
                                "row": dict(row),
                                "constraint": f"NOT NULL on {column}",
                                "reason": f"Column {column} cannot be NULL",
                            }
                            violations_log.append(violation)

                    # Check unique constraints
                    elif constraint.get("type") == "unique":
                        query = f"""
                            SELECT {column}, COUNT(*) 
                            FROM {temp_table_name}
                            GROUP BY {column}
                            HAVING COUNT(*) > 1;
                        """
                        result = connection.execute(text(query))
                        duplicate_values = result.fetchall()

                        for value, count in duplicate_values:
                            query = f"""
                                SELECT * FROM {temp_table_name}
                                WHERE {column} = :value;
                            """
                            duplicate_rows = connection.execute(
                                text(query), {"value": value}
                            ).fetchall()

                            for row in duplicate_rows:
                                violation = {
                                    "row": dict(row),
                                    "constraint": f"UNIQUE on {column}",
                                    "reason": f"Value '{value}' appears {count} times",
                                }
                                violations_log.append(violation)

                    # Check foreign key constraints
                    elif constraint.get("type") == "foreign_key" and constraint.get("reference"):
                        ref_table, ref_column = constraint["reference"].split(".")
                        query = f"""
                            SELECT t.* FROM {temp_table_name} t
                            LEFT JOIN {ref_table} r ON t.{column} = r.{ref_column}
                            WHERE t.{column} IS NOT NULL AND r.{ref_column} IS NULL;
                        """
                        result = connection.execute(text(query))
                        invalid_fk_rows = result.fetchall()

                        for row in invalid_fk_rows:
                            violation = {
                                "row": dict(row),
                                "constraint": f"FOREIGN KEY {column} REFERENCES {ref_table}.{ref_column}",
                                "reason": f"Value {row[column]} does not exist in {ref_table}.{ref_column}",
                            }
                            violations_log.append(violation)

        # Log violations
        if violations_log:
            self.logger.warning(
                f"Found {len(violations_log)} constraint violations in {temp_table_name}"
            )
            for violation in violations_log:
                self.logger.warning(
                    f"Constraint violation: {violation['constraint']} - {violation['reason']}"
                )

        # Return valid rows count and invalid rows count
        return len(violations_log)

    def load(self, df, table_name, if_exists="replace", index=False):
        """
        Load dataframe to PostgreSQL with constraint validation.
        Invalid rows are logged and excluded from the final insert.
        """
        # Create temp table name with timestamp to avoid conflicts
        temp_table_name = f"temp_{table_name}_{int(time.time())}"

        # Get table constraints from the schema
        table_constraints = self._get_table_constraints(table_name)

        # Write to temporary table
        df.to_sql(
            temp_table_name,
            self.get_engine(),
            if_exists="replace",
            index=index,
        )

        # Validate constraints
        violations_count = self.validate_and_log_constraint_violations(
            temp_table_name, table_constraints
        )

        # If there are violations, create a view with only valid rows
        if violations_count > 0:
            with self.get_engine().connect() as connection:
                with connection.begin():
                    # Create view with only valid rows (example for NOT NULL constraint on status_date)
                    valid_rows_view = f"valid_{temp_table_name}"

                    # Build the validation query based on constraints
                    validation_conditions = []
                    for column, constraint in table_constraints.items():
                        if constraint.get("type") == "not_null":
                            validation_conditions.append(f"{column} IS NOT NULL")

                    # Create view with valid rows only
                    validation_clause = (
                        " AND ".join(validation_conditions) if validation_conditions else "TRUE"
                    )
                    connection.execute(
                        text(
                            f"CREATE TEMPORARY VIEW {valid_rows_view} AS SELECT * FROM {temp_table_name} WHERE {validation_clause}"
                        )
                    )

                    # Use the view with valid rows for the final UPSERT
                    conflict_targets = ", ".join(self.unique_constraints)
                    update_columns = ", ".join(
                        [f"{col} = EXCLUDED.{col}" for col in self.update_columns]
                    )

                    insert_query = f"""
                        INSERT INTO {table_name}
                        SELECT * FROM {valid_rows_view}
                        ON CONFLICT ({conflict_targets})
                        DO UPDATE SET {update_columns}
                    """
                    connection.execute(text(insert_query))

                    # Drop temporary objects
                    connection.execute(text(f"DROP VIEW IF EXISTS {valid_rows_view}"))
                    connection.execute(text(f"DROP TABLE IF EXISTS {temp_table_name}"))

                    # Log statistics
                    self.logger.info(
                        f"Inserted/updated {df.shape[0] - violations_count} rows to {table_name}"
                    )
                    self.logger.warning(f"Skipped {violations_count} invalid rows")
        else:
            # No violations, do regular UPSERT
            with self.get_engine().connect() as connection:
                with connection.begin():
                    conflict_targets = ", ".join(self.unique_constraints)
                    update_columns = ", ".join(
                        [f"{col} = EXCLUDED.{col}" for col in self.update_columns]
                    )

                    insert_query = f"""
                        INSERT INTO {table_name}
                        SELECT * FROM {temp_table_name}
                        ON CONFLICT ({conflict_targets})
                        DO UPDATE SET {update_columns}
                    """
                    connection.execute(text(insert_query))

                    # Drop temporary table
                    connection.execute(text(f"DROP TABLE IF EXISTS {temp_table_name}"))

                    # Log statistics
                    self.logger.info(f"Inserted/updated {df.shape[0]} rows to {table_name}")

    def _get_table_constraints(self, table_name):
        """
        Get constraints for a table from the database schema.
        Returns a dictionary of column constraints.
        """
        constraints = {}

        # Query to get NOT NULL constraints
        not_null_query = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = :table_name
            AND is_nullable = 'NO'
        """

        # Query to get unique constraints
        unique_query = """
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_name = :table_name
            AND tc.constraint_type = 'UNIQUE'
        """

        # Query to get foreign key constraints
        fk_query = """
            SELECT
                kcu.column_name,
                ccu.table_name AS referenced_table,
                ccu.column_name AS referenced_column
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu
                ON tc.constraint_name = ccu.constraint_name
            WHERE tc.table_name = :table_name
            AND tc.constraint_type = 'FOREIGN KEY'
        """

        with self.get_engine().connect() as connection:
            # Get NOT NULL constraints
            not_null_result = connection.execute(text(not_null_query), {"table_name": table_name})
            for row in not_null_result:
                column = row["column_name"]
                constraints[column] = constraints.get(column, {})
                constraints[column]["type"] = "not_null"

            # Get unique constraints
            unique_result = connection.execute(text(unique_query), {"table_name": table_name})
            for row in unique_result:
                column = row["column_name"]
                constraints[column] = constraints.get(column, {})
                constraints[column]["type"] = "unique"

            # Get foreign key constraints
            fk_result = connection.execute(text(fk_query), {"table_name": table_name})
            for row in fk_result:
                column = row["column_name"]
                ref_table = row["referenced_table"]
                ref_column = row["referenced_column"]
                constraints[column] = constraints.get(column, {})
                constraints[column]["type"] = "foreign_key"
                constraints[column]["reference"] = f"{ref_table}.{ref_column}"

        return constraints
