import os
import json
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.types import JSON


# Database connection
def get_connection_string():
    return (
        f"postgresql://{os.getenv('POSTGRES_USER')}:"
        f"{os.getenv('POSTGRES_PASSWORD')}@"
        f"{os.getenv('POSTGRES_HOST')}:"
        f"{os.getenv('POSTGRES_PORT')}/"
        f"{os.getenv('REFERENDUM_DB_NAME')}"
    )


connection_string = get_connection_string()
engine = create_engine(connection_string)


def load_json_files(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            file_path = os.path.join(directory, filename)
            try:
                with open(file_path, "r") as file:
                    data = json.load(file)

                df = pd.json_normalize(data)

                table_name = filename.replace(".json", "")

                # Write to database
                df.to_sql(
                    table_name,
                    engine,
                    if_exists="replace",
                    index=False,
                    dtype={"data": JSON},
                )

                print(f"Loaded data from {filename} into table {table_name}")
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")


if __name__ == "__main__":
    data_directory = "data"
    load_json_files(data_directory)
    print("Data loading completed")
