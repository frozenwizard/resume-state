"""Constants for the Resume State component."""

DOMAIN = "resume_state"
SIGNAL_UPDATE_RESUME_STATE = f"{DOMAIN}_update_state"

# Config entry option keys
CONF_ENTITIES = "entities"
CONF_THROTTLE = "throttle"
CONF_THROTTLE_DEFAULT = 0

# Integration's system user name
INTEGRATION_USER_NAME = "Resume State"

# Supported entity domains are derived from the resumable dispatch table in
# ``resumable`` (``SUPPORTED_DOMAINS``) so the two can never drift apart.
FAN_DOMAIN = "fan"
INPUT_BOOLEAN_DOMAIN = "input_boolean"
INPUT_SELECT_DOMAIN = "input_select"
LIGHT_DOMAIN = "light"
SELECT_DOMAIN = "select"
SWITCH_DOMAIN = "switch"
