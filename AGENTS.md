# Instructions for agents

This repository holds my OP-XY machines (toro, theseus, meikyu, clew), one folder each under `machines/`, laid out like
[open-xy-core-machines](https://github.com/etcetc000/open-xy-core-machines). It is not the SDK. The OP-1 versions
of these plugins live in [labyrinth](https://github.com/thoughtgrain/labyrinth); don't change them from here.

## Which task is this?

- **Changing a machine's sound, controls or screen code** (`engine.cpp`, `display.cpp`, `definition.json`,
  `gen_panel.py`): work only inside `machines/<id>/`, following the SDK's `AGENTS.md`, `docs/first-machine.md`,
  `docs/ux.md` and `docs/display.md`. If artwork changes, run that machine's `gen_panel.py` rather than editing
  `panel.svg.fragment` or `nodes.h` by hand.
- **Designing or revising a screen** (subject, motion, contact sheet, handoff): that's operator-design's protocol.
  Use the `operator-design` MCP server (`.mcp.json` starts it from the submodule, with its workspace set to this
  repository) and the `opxy-screen` / `opxy-audit` skills and `opxy-*` agents linked under `.claude/`. Design
  output goes to `screens/<machine-id>/` here. Then implement from that handoff as above.
- **Teaching the guidelines something** (a new pattern, a pitfall): that's training mode in operator-design itself,
  not here. Open it as a change to that repository, then bump the submodule.
- **Releasing:** a tag here, then a pull request against the SDK's `staging` that changes only
  `catalog/machines.json`, with the hardware CPU record from the SDK's `docs/profiling.md`.

## Checks

Clone the SDK beside this repository (`git clone https://github.com/etcetc000/open-xy ../open-xy`, default branch
`staging`) and run it from here:

```sh
python ../open-xy/sdk.py test --machine machines/toro --machine machines/theseus --machine machines/meikyu --machine machines/clew
python3 tools/panel_lint.py machines/*/panel.svg.fragment
```

Both must pass before a commit. CI runs the same checks and a firmware compile.

## Ground rules

- The SDK's docs are the authority, then operator-design's guidelines.
- Machine code uses only the public `<opxy/...>` headers: no assembly, platform conditionals, OS headers or raw
  addresses, and audio callbacks never allocate, block, log or do I/O. An SDK gap is a separate SDK pull request.
- Screens are grey only. Red belongs to the stock UI (recording, parameter locks).
- Judge every screen at 1:1 (480 × 220).
- A host test is not a device check or a CPU measurement. Device checks stay pending until someone runs them on an
  OP-XY, and device operations need the user's explicit instruction each time.
- Firmware, `os.ldr` and other stock files never go in this repository, not even under `local/`.
- Parameter order, mappings and machine IDs are saved in projects and presets: changing them is the user's
  decision, never a side effect.
- Don't copy stock OP-XY artwork or other machines' art.
