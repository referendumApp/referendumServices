from enum import Enum
from typing import Dict, List, Optional, Set
from pydantic import BaseModel
from sqlalchemy.orm.session import Session
import pandas as pd
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)


class TransformationFunction(str, Enum):
    KEEP_COLUMNS = "keep_columns"
    RENAME = "rename"
    DUPLICATE = "duplicate"
    ADD_URL = "add_url"


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

                case _:
                    raise ValueError(f"Unsupported transformation: {self.function}")

        except Exception as e:
            logger.error(f"Error in transformation {self.function}: {str(e)}")
            raise


class ETLConfig(BaseModel):
    source: str
    source_columns: Set[str]
    destination: str
    destination_columns: List[str]
    transformations: List[Transformation]
    dataframe: Optional[pd.DataFrame] = None

    class Config:
        arbitrary_types_allowed = True

    def _get_source_query(self) -> str:
        """Generate SQL query for source data extraction"""
        columns = ", ".join(sorted(self.source_columns))
        return f"SELECT {columns} FROM {self.source}"

    def extract(self, conn: Session):
        query = self._get_source_query()
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

    def load(self, conn: Session):
        try:
            logger.info(f"Loading data into {self.destination} with unique_constraints on 'id'")

            # Create temporary table
            temp_table = f"temp_{self.destination}"
            self.dataframe[self.destination_columns].to_sql(
                temp_table,
                con=conn,
                if_exists="replace",
                index=False,
            )

            # Perform UPSERT from temporary table
            unique_constraint_columns = ["id"]
            conflict_targets = ", ".join(unique_constraint_columns)
            update_sets = ", ".join(
                f"{col} = EXCLUDED.{col}"
                for col in self.destination_columns
                if col not in unique_constraint_columns
            )
            upsert_query = f"""
                INSERT INTO {self.destination} ({', '.join(self.destination_columns)})
                SELECT {', '.join(self.destination_columns)}
                FROM {temp_table}
                ON CONFLICT ({conflict_targets})
                DO UPDATE SET {update_sets}
            """
            conn.execute(text(upsert_query))

            conn.execute(text(f"DROP TABLE {temp_table}"))
            conn.commit()

        except Exception as e:
            logger.error(f"Error upserting data into '{self.destination}': {e}")
            conn.rollback()
            raise
