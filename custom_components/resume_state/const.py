"""Constants for the Resume State component."""

DOMAIN = "resume_state"
SIGNAL_UPDATE_RESUME_STATE = f"{DOMAIN}_update_state"

# Integration's system user name
INTEGRATION_USER_NAME = "Resume State"

FAN_DOMAIN = "fan"
INPUT_BOOLEAN_DOMAIN = "input_boolean"
LIGHT_DOMAIN = "light"
SWITCH_DOMAIN = "switch"
SUPPORTED_DOMAINS: set[str] = {
    FAN_DOMAIN,
    INPUT_BOOLEAN_DOMAIN,
    LIGHT_DOMAIN,
    SWITCH_DOMAIN,
}
