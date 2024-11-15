import random
import string

NAY_VOTE_ID = 0
YAY_VOTE_ID = 1


# Shared utility functions
def assert_status_code(response, expected_status_code: int):
    assert (
        response.status_code == expected_status_code
    ), f"Expected status code {expected_status_code}, but got {response.status_code}. Response content: {response.content}"


def generate_random_string(length=5):
    return "".join(random.choice(string.ascii_lowercase) for _ in range(length))
