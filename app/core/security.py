import re

BCRYPT_SCHEME = "bcrypt"
BCRYPT_DEPRECATED = "auto"

OAUTH_TOKEN_URL = "/api/v1/auth/login"

PASSWORD_MIN_LENGTH = 8
PASSWORD_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?\":{}|<>]).+$")

PASSWORD_POLICY_MESSAGE = (
    "Password must be at least 8 characters and include uppercase, "
    "lowercase, digit, and special character."
)