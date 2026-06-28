"""Constants for the Resume State component."""

DOMAIN = "resume_state"
SIGNAL_UPDATE_RESUME_STATE = f"{DOMAIN}_update_state"

LIGHT_DOMAIN = "light"
SUPPORTED_DOMAINS: set[str] = {LIGHT_DOMAIN}
