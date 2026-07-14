# Roadmap

## Shipped — v0.1.0

- Store / resume / clear driven by recorder history: snapshot is an instant in time, restores replay the
  state each entity had at that instant, with per-entity throttling and failure isolation.
- Supported domains: light, fan, switch, input boolean, select, input select.
- UI-only setup with editable options, "Status" and "When to resume" sensors, and an enable switch.
- Restores attributed to a dedicated "Resume State" system user in the logbook.
- Published to HACS as a custom repository, with brand images shipped in the integration
  (Brands Proxy API).

## In flight

- Inclusion in the HACS default store: [hacs/default#9161](https://github.com/hacs/default/pull/9161)
  is open and awaiting review. Until it lands, install via HACS custom repositories.

## Next

- More entity domains — cover, climate, and media player are the obvious candidates; the
  `resumable/` layer is the extension point.

## Ideas (no commitment)

- Multiple named snapshots instead of a single stored instant.
- Service actions (`resume_state.store` / `resume` / `clear`) so automations don't have to press buttons.
- Be like Battery Notes where it scans automatically for entities to resume.
