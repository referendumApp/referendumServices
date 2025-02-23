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

class PlatformType(str, Enum):
    IOS = "ios"
    ANDROID = "android"