def extract():
    print("Extracting")


def transform():
    print("Transforming")


def load():
    print("Loading")


def orchestrate_etl():
    extract()
    transform()
    load()


if __name__ == "__main__":
    orchestrate_etl()
