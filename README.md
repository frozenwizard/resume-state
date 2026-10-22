# Resume State

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

A Home Assistant integration that snapshots the state of your chosen entities at a moment in time and
restores them to that snapshot later.

Press **Store** before something changes your lights, fans, or switches and press **Resume** afterwards to put
everything back exactly the way it was, including attributes like brightness, color, and fan speed. State history is
read from Home Assistant's recorder, so nothing needs to be copied up front; the snapshot is just an instant in time.

## How it works

The integration creates a small set of entities:

- **Store** (button) — marks the current moment as the snapshot instant.
- **Resume** (button) — restores every configured entity to the state it had at that instant.
- **Clear** (button) — discards the snapshot.
- **Status** and **Stored at** (sensors) — show the current state of the cycle.
- **Enabled** (switch) — gates resume entirely; useful for temporarily pausing automations that press
  the buttons.

Restores are issued as a dedicated "Resume State" system user, so every change is attributed in the
logbook. A configurable throttle spaces out the restore calls, and a failure on one entity never stops
the rest of the batch.

## Actions

Each button has a matching action, so automations and scripts can drive the snapshot directly:

- `resume_state.store` — same as **Store**.
- `resume_state.resume` — same as **Resume**. The action finishes once every entity has been restored.
- `resume_state.clear` — same as **Clear**.

`resume_state.resume` also takes an optional `datetime` to restore to that moment instead of the stored
snapshot. Like any resume, it clears the stored snapshot afterwards, whether or not it succeeds. A date and
time without a time zone is read in Home Assistant's time zone. It must be in the past and within your
recorder's history.

```yaml
action: resume_state.resume
data:
  datetime: "2026-10-03 18:00:00"
```

**Enabled** gates the `resume_state.resume` action exactly as it gates the button.

## Requirements

- The [recorder](https://www.home-assistant.io/integrations/recorder/) integration must be enabled (it is
  by default). Resume State reads historical state from it, so the recorder must retain history covering
  the moment you resume to: when you pressed **Store**, or the `datetime` passed to the resume action.

## Installation

### HACS (recommended)

1. In HACS, open the overflow menu (⋮) and choose **Custom repositories**.
2. Add `https://github.com/frozenwizard/resume-state` with type **Integration**.
3. Search for **Resume State** in HACS and install it.
4. Restart Home Assistant.

### Manual

1. Copy `custom_components/resume_state` into the `custom_components` directory of your Home Assistant
   configuration.
2. Restart Home Assistant.

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
