import hashlib
import logging
from enum import Enum
from typing import Dict, List, Optional, Set

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text
from sqlalchemy.orm.session import Session

from common.user_service.client import UserServiceClient

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


class PDSLoader:
    """Handles loading data into the PDS"""

    def __init__(self):
        self.user_client = UserServiceClient()

    def create_or_update_legislator(self, legislator_data: Dict) -> Dict:
        """Create or update legislator in PDS and return PDS response with DID/AID"""
        try:
            # Try to get existing legislator first
            existing = self.user_client.get_legislator(
                legislator_id=legislator_data["legislatorId"]
            )

            if existing:
                # Update existing legislator
                response = self.user_client.update_legislator(legislator_data)
                logger.info(f"Updated legislator {legislator_data['legislatorId']} in PDS")

                return {
                    "legislatorId": legislator_data["legislatorId"],
                    "did": response.get("did"),
                    "aid": response.get("aid"),
                    "handle": response.get("handle"),
                    "action": "updated",
                }
            else:
                # Create new legislator - this will return DID and AID
                response = self.user_client.create_legislator(legislator_data)
                logger.info(f"Created legislator {legislator_data['legislatorId']} in PDS")

                return {
                    "legislatorId": legislator_data["legislatorId"],
                    "did": response.get("did"),
                    "aid": response.get("aid"),
                    "handle": response.get("handle"),
                    "action": "created",
                }

        except Exception as e:
            logger.error(f"Failed to process legislator {legislator_data.get('legislatorId')}: {e}")
            raise


class ETLConfig(BaseModel):
    source: str
    source_columns: Set[str]
    destination: str
    destination_columns: List[str]
    join_config: Optional[JoinConfig] = None
    transformations: List[Transformation]
    unique_constraints: List[str] = Field(default=["id"])
    dataframe: Optional[pd.DataFrame] = None
    pds_load: bool = False

    model_config = ConfigDict(arbitrary_types_allowed=True)
    _pds_loader: PDSLoader = None

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

    def load(self, conn: Session):
        """Enhanced load method with bidirectional PDS support"""

        if self.pds_load:
            results = {
                "succeeded": 0,
                "failed": 0,
                "errors": [],
                "pds_responses": [],  # Contains DID/AID data to update database
            }

            for _, row in self.dataframe.iterrows():
                legislator_data = row.to_dict()
                try:
                    pds_response = self.create_or_update_legislator(legislator_data)
                    results["pds_responses"].append(pds_response)
                    results["succeeded"] += 1

                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(
                        {"legislator_id": legislator_data.get("legislatorId"), "error": str(e)}
                    )

            logger.info(
                f"PDS load completed for {self.destination}. "
                f"Succeeded: {results['succeeded']}, Failed: {results['failed']}"
            )

            if results["failed"] > 0:
                logger.error(f"PDS load errors: {results['errors']}")
                raise Exception(f"PDS load had {results['failed']} failures")

            self._update_database_with_pds_data(conn, results["pds_responses"])

        else:
            self._load_to_database(conn)

    def _update_database_with_pds_data(self, conn: Session, pds_responses: list):
        """Update database with DID/AID values returned from PDS"""
        try:
            valid_responses = [
                response
                for response in pds_responses
                if response.get("did") and response.get("aid")
            ]

            if not valid_responses:
                logger.info("No valid PDS responses with both DID and AID found")
                return

            logger.info(f"Updating {len(valid_responses)} legislators with PDS data (DID/AID)")

            invalid_response_count = len(pds_responses) - len(valid_responses)
            logger.info(f"Skipping {invalid_response_count} responses without DID/AID")

            update_values = []
            for response in valid_responses:
                update_values.append(
                    f"({response['legislatorId']}, '{response['did']}', '{response['aid']}', '{response['handle']}')"
                )
            bulk_update_query = text(
                f"""
                UPDATE legislators 
                SET 
                    did = updates.did,
                    aid = updates.aid,
                    pds_handle = updates.handle,
                    pds_synced_at = NOW()
                FROM (VALUES {', '.join(update_values)}) AS updates(legislator_id, did, aid, handle)
                WHERE legislators.legiscan_id = updates.legislator_id::integer
            """
            )

            conn.execute(bulk_update_query)
            conn.commit()
            logger.info("Successfully updated legislators table with PDS data")

        except Exception as e:
            logger.error(f"Failed to update database with PDS data: {e}")
            conn.rollback()
            raise

    def _load_to_database(self, conn: Session):
        try:
            logger.info(f"Loading data into {self.destination} with unique_constraints on 'id'")

            if self.dataframe.empty:
                logger.warning("Skipping; no data to write")
                return

            # Check if destination table exists
            query = text("SELECT 1 FROM information_schema.tables WHERE table_name = :table_name")
            exists = conn.execute(query, {"table_name": self.destination}).scalar() is not None
            if not exists:
                raise ValueError(f"Destination table '{self.destination}' does not exist")

            # Create temporary table
            temp_table = f"temp_{self.destination}"
            self.dataframe[self.destination_columns].to_sql(
                temp_table,
                con=conn,
                if_exists="replace",
                index=False,
            )

            # Perform UPSERT from temporary table
            conflict_targets = ", ".join(self.unique_constraints)
            update_sets = ", ".join(
                f"{col} = EXCLUDED.{col}"
                for col in self.destination_columns
                if col not in self.unique_constraints
            )

            # Special case where all columns are part of unique constraint
            if not update_sets:
                update_sets = "id = EXCLUDED.id"  # Dummy update that won't actually happen

            upsert_query = f"""
                INSERT INTO {self.destination} ({', '.join(self.destination_columns)})
                SELECT {', '.join(self.destination_columns)}
                FROM {temp_table}
                ON CONFLICT ({conflict_targets})
                DO UPDATE SET {update_sets}
            """
            logger.info(f"Executing upsert query: {upsert_query}")
            conn.execute(text(upsert_query))
            conn.execute(text(f"DROP TABLE {temp_table}"))
            conn.commit()

        except Exception as e:
            logger.error(f"Error upserting data into '{self.destination}': {e}")
            conn.rollback()
            raise

    def create_or_update_legislator(self, legislator_data: Dict) -> Dict:
        if not self._pds_loader:
            self._pds_loader = PDSLoader()
        return self._pds_loader.create_or_update_legislator(legislator_data)
