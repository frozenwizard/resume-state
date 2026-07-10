# Hi

Documentation should go here.

## Configuration

Resume State is set up entirely through the UI: go to **Settings → Devices & Services → Add Integration**
and search for **Resume State**. Pick the entities to snapshot and, optionally, a throttle (milliseconds to
wait between restoring each entity). Only one instance can be configured.

To change the entities or throttle later, open the integration and press **Configure**.

## Supported entities

- **Light** — restores on/off, brightness, effect, and color.
- **Fan** — restores on/off, speed percentage, and preset mode. Restoring
  direction and oscillation is not supported.
- **Switch** — restores on/off.
- **Input boolean** — restores on/off.
- **Select** — restores the selected option.
- **Input select** — restores the selected option.
