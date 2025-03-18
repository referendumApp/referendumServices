from enum import Enum

YEA_VOTE_ID = 1
NAY_VOTE_ID = 2
ABSTAIN_VOTE_ID = 3
ABSENT_VOTE_ID = 4


class AuthProvider(str, Enum):
    EMAIL = "email"
    GOOGLE = "google"
    # FACEBOOK = "facebook"
    # APPLE = "apple"

    @property
    def user_id_field(self) -> str:
        """
        Returns the standardized user ID field name for this provider.
        Example: AuthProvider.GOOGLE.user_id_field returns "google_user_id"
        """
        return f"{self.value}_user_id"


class PlatformType(str, Enum):
    IOS = "ios"
    ANDROID = "android"
