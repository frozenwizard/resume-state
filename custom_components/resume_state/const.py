"""Constants for the Resume State component."""

DOMAIN = "resume_state"
SIGNAL_UPDATE_RESUME_STATE = f"{DOMAIN}_update_state"

# Integration's system user name
INTEGRATION_USER_NAME = "Resume State"

FAN_DOMAIN = "fan"
LIGHT_DOMAIN = "light"
SUPPORTED_DOMAINS: set[str] = {FAN_DOMAIN, LIGHT_DOMAIN}
