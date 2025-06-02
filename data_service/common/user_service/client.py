import logging
import os
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserServiceClient:
    def __init__(self) -> None:
        self.base_url = os.getenv("USER_SERVICE_URL")
        if not self.base_url:
            raise ValueError("USER_SERVICE_URL environment variable is required")

        self.base_url = self.base_url.rstrip("/")

        self.system_token = os.getenv("SYSTEM_AUTH_TOKEN")
        if not self.system_token:
            raise ValueError("SYSTEM_AUTH_TOKEN environment variable is required")

        self.session = requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/json", "Authorization": f"Bearer {self.system_token}"}
        )

        self.timeout = 30
        self.check_connection()
        logger.info(f"Initialized UserServiceClient with URL: {self.base_url}")

    def check_connection(self):
        """Check if the user service is accessible"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
            if response.status_code == 200:
                logger.info("Successfully connected to user service")
                return True
            else:
                raise Exception(f"Health check failed with status {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to connect to user service: {str(e)}")
            raise e

    def _make_request(
        self, method: str, endpoint: str, data: Optional[Dict] = None, retries: int = 3
    ) -> requests.Response:
        """Make HTTP request with retry logic"""
        url = f"{self.base_url}{endpoint}"

        for attempt in range(retries):
            try:
                if method.upper() == "GET":
                    response = self.session.get(url, timeout=self.timeout)
                elif method.upper() == "POST":
                    response = self.session.post(url, json=data, timeout=self.timeout)
                elif method.upper() == "PUT":
                    response = self.session.put(url, json=data, timeout=self.timeout)
                elif method.upper() == "DELETE":
                    response = self.session.delete(url, json=data, timeout=self.timeout)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                # Check if request was successful
                response.raise_for_status()
                return response

            except requests.exceptions.RequestException as e:
                logger.warning(f"Request attempt {attempt + 1} failed: {str(e)}")
                if attempt == retries - 1:
                    raise
                time.sleep(2**attempt)  # Exponential backoff

        raise Exception(f"Failed to complete request after {retries} attempts")

    def create_legislator(self, legislator_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new legislator in the PDS"""
        try:
            logger.info(f"Creating legislator: {legislator_data.get('legislatorId')}")

            # Prepare the payload for the user service
            payload = {
                "legislatorId": legislator_data.get("legislatorId"),
                "handle": legislator_data.get("handle"),
                "displayName": legislator_data.get("displayName"),
                "description": legislator_data.get("description", ""),
                "avatar": legislator_data.get("avatar", ""),
                "state": legislator_data.get("state", ""),
                "party": legislator_data.get("party", ""),
                "chamber": legislator_data.get("chamber", ""),
                "active": legislator_data.get("active", True),
            }

            response = self._make_request("POST", "/legislators", payload)
            result = response.json()

            logger.info(f"Successfully created legislator {legislator_data.get('legislatorId')}")
            return {
                "did": result.get("did"),
                "aid": result.get("aid"),
                "handle": result.get("handle"),
            }

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 409:
                logger.warning(f"Legislator {legislator_data.get('legislatorId')} already exists")
                raise Exception(f"Legislator already exists: {legislator_data.get('legislatorId')}")
            else:
                logger.error(
                    f"HTTP error creating legislator: {e.response.status_code} - {e.response.text}"
                )
                raise Exception(f"Failed to create legislator: {e}")
        except Exception as e:
            logger.error(
                f"Error creating legislator {legislator_data.get('legislatorId')}: {str(e)}"
            )
            raise

    def update_legislator(self, legislator_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing legislator in the PDS"""
        try:
            logger.info(f"Updating legislator: {legislator_data.get('legislatorId')}")

            payload = {
                "legislatorId": legislator_data.get("legislatorId"),
                "handle": legislator_data.get("handle"),
                "displayName": legislator_data.get("displayName"),
                "description": legislator_data.get("description", ""),
                "avatar": legislator_data.get("avatar", ""),
                "state": legislator_data.get("state", ""),
                "party": legislator_data.get("party", ""),
                "chamber": legislator_data.get("chamber", ""),
                "active": legislator_data.get("active", True),
            }

            response = self._make_request("PUT", "/legislators", payload)
            result = response.json()

            logger.info(f"Successfully updated legislator {legislator_data.get('legislatorId')}")
            return {
                "did": result.get("did"),
                "aid": result.get("aid"),
                "handle": result.get("handle"),
            }

        except requests.exceptions.HTTPError as e:
            logger.error(
                f"HTTP error updating legislator: {e.response.status_code} - {e.response.text}"
            )
            raise Exception(f"Failed to update legislator: {e}")
        except Exception as e:
            logger.error(
                f"Error updating legislator {legislator_data.get('legislatorId')}: {str(e)}"
            )
            raise

    def get_legislator(self, legislator_id: str) -> Optional[Dict[str, Any]]:
        """Get a legislator by ID"""
        try:
            logger.info(f"Getting legislator: {legislator_id}")

            # Use query parameter for GET request
            response = self._make_request("GET", f"/legislators?legislatorId={legislator_id}")
            result = response.json()

            logger.info(f"Successfully retrieved legislator {legislator_id}")
            return result

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.info(f"Legislator {legislator_id} not found")
                return None
            else:
                logger.error(
                    f"HTTP error getting legislator: {e.response.status_code} - {e.response.text}"
                )
                raise Exception(f"Failed to get legislator: {e}")
        except Exception as e:
            logger.error(f"Error getting legislator {legislator_id}: {str(e)}")
            raise

    def delete_legislator(self, legislator_id: str) -> bool:
        """Delete a legislator by ID"""
        try:
            logger.info(f"Deleting legislator: {legislator_id}")

            payload = {"legislatorId": legislator_id}
            response = self._make_request("DELETE", "/legislators", payload)

            logger.info(f"Successfully deleted legislator {legislator_id}")
            return True

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Legislator {legislator_id} not found for deletion")
                return False
            else:
                logger.error(
                    f"HTTP error deleting legislator: {e.response.status_code} - {e.response.text}"
                )
                raise Exception(f"Failed to delete legislator: {e}")
        except Exception as e:
            logger.error(f"Error deleting legislator {legislator_id}: {str(e)}")
            raise

    def batch_create_legislators(self, legislators_data: list) -> Dict[str, Any]:
        """Create multiple legislators in batch"""
        results = {"succeeded": 0, "failed": 0, "errors": [], "responses": []}

        for legislator_data in legislators_data:
            try:
                response = self.create_legislator(legislator_data)
                results["responses"].append(response)
                results["succeeded"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(
                    {"legislator_id": legislator_data.get("legislatorId"), "error": str(e)}
                )

        logger.info(
            f"Batch create completed. Succeeded: {results['succeeded']}, Failed: {results['failed']}"
        )
        return results

    def batch_update_legislators(self, legislators_data: list) -> Dict[str, Any]:
        """Update multiple legislators in batch"""
        results = {"succeeded": 0, "failed": 0, "errors": [], "responses": []}

        for legislator_data in legislators_data:
            try:
                response = self.update_legislator(legislator_data)
                results["responses"].append(response)
                results["succeeded"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(
                    {"legislator_id": legislator_data.get("legislatorId"), "error": str(e)}
                )

        logger.info(
            f"Batch update completed. Succeeded: {results['succeeded']}, Failed: {results['failed']}"
        )
        return results
