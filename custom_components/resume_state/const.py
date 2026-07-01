"""Constants for the Resume State component."""

DOMAIN = "resume_state"
SIGNAL_UPDATE_RESUME_STATE = f"{DOMAIN}_update_state"

# Integration's system user name
INTEGRATION_USER_NAME = "Resume State"

LIGHT_DOMAIN = "light"
SUPPORTED_DOMAINS: set[str] = {LIGHT_DOMAIN}
