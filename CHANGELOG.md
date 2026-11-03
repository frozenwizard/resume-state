# Changelog

## v1.0.0 (02-11-2026)

### Changes

* A failed resume now raises an error as well as setting Status to Errored, so an automation that calls
  `resume_state.resume` or presses Resume stops at that step unless it uses `continue_on_error`. Pressing Resume in
  the UI shows the error
* A resume where no configured entity has recorded history at that moment now ends Errored instead of Idle
* Only one resume runs at a time. While it runs, Store and Resume are rejected and Enabled is unavailable. Clear
  aborts it
* New actions for automations and scripts: `resume_state.store`, `resume_state.resume` and `resume_state.clear`,
  matching the buttons. `resume_state.resume` finishes once every entity has been restored
* `resume_state.resume` takes an optional `datetime` to restore to any past moment instead of the stored snapshot. A
  date and time without a time zone is read in Home Assistant's time zone, and a future one is rejected. Like any
  resume, it clears the stored snapshot afterwards, and a failed one logs the discarded snapshot's time
* Failed resumes say why: nothing is stored, none of the configured entities can be resumed, no entity has recorded
  history at that moment, or some entities failed to restore (the message lists them). Turning off Enabled or
  aborting with Clear isn't an error
* Stopping the automation or script that started a resume, such as a restarted automation, stops the resume too and
  marks it Errored
* Logbook entries for restored entities link back to the button press, action or automation that started the
  resume, and are still attributed to the "Resume State" user
* The actions are rejected until the integration has finished setting up, and `store` and `clear` reject fields they
  don't take
* Published to the HACS default store

### Fixes

* A cancelled resume no longer leaves Status stuck on Resuming
* Reloading or removing the integration during a resume no longer causes an error

### Maintenance

* Dependabot opens grouped update PRs once a week, each ecosystem on its own day. Minor and patch updates merge
  themselves once checks pass; major updates wait for manual approval
* Every PR must bump the integration version, and PRs from this repository get a patch bump automatically
* The store, resume and clear logic moved out of the buttons into one module shared with the actions (no behavior
  change)
* Added contributing guidelines and CODEOWNERS
* README: documented the actions and the errors they raise, and installing from the HACS default store

## v0.1.0 (14-07-2026)

### Features

* Initial release
* Store, Resume and Clear buttons. Store marks a moment, and Resume restores each configured entity to the state the
  recorder had for it then, including attributes such as brightness, color and fan speed
* Supports lights, fans, switches, input booleans, selects and input selects
* A configurable throttle between restores, and a failure on one entity doesn't stop the rest
* Status and When to resume sensors, and an Enabled switch that gates resuming
* Restores are attributed to a dedicated "Resume State" user in the logbook
* UI-only setup, with entities and throttle editable later
