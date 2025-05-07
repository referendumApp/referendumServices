import logging
import os
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserServiceClient:
    def __init__(self) -> None:
        self.base_url = os.getenv("USER_SERVICE_URL")
        self.check_connection()
        logger.info(f"Initialized UserServiceClient with URL: {self.base_url}")

    def check_connection(self):
        try:
            response = requests.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to connect to user service: {str(e)}")
            raise e
