# Contributing

Project-level conventions for changes under `plugins/`. The sections
below use **specode** as the concrete example; **task-swarm** follows
the same stdlib/CLI/test conventions, and **obsidian-wiki** documents
itself in its own `README.md` / `AGENTS.md`. Each plugin releases
independently. Read this before opening a PR or cutting a release.

## Runtime is stdlib-only

Any runtime code under `plugins/specode/scripts/` MUST use only the
Python standard library. Plugin users install via the host CLI's
`plugin install`; they don't `pip install -r requirements.txt`.
Pulling third-party packages in either silently breaks for users
without them or forces a heavier install path.

Tests under `plugins/specode/tests/` MAY use `pytest` (it's a dev
dependency, not runtime).

## CLI invocation contract

Every script under `plugins/specode/scripts/` is a CLI invoked from
the SessionStart hook (`hooks.json`) or directly by a skill. **All
invocations MUST go through the `run.sh` wrapper** — but how the
wrapper's path is resolved differs by caller (superpowers convention):

- **Hooks** run in a subprocess where `$CLAUDE_PLUGIN_ROOT` is reliably
  injected, so `hooks.json` calls it directly (simple env var, no `:-`):

  ```sh
  sh "${CLAUDE_PLUGIN_ROOT}/scripts/run.sh" \
     "${CLAUDE_PLUGIN_ROOT}/scripts/<name>.py" <verb> <args...>
  ```

- **Skills** cannot rely on the env var (not reliably set in skill-driven
  Bash) and must NOT `find` it or use a `${VAR:-…}` fallback — on Windows
  the host swallows `${VAR:-default}` into an empty string and CodeBuddy
  injects no plugin env var at all. Instead use a **base-directory-relative
  path** (superpowers-style): the scripts live in the plugin's `scripts/`,
  which from a `skills/<name>/` skill is `../../scripts/`, and the host
  supplies the skill's absolute base directory to resolve it:

  ```sh
  sh ../../scripts/run.sh ../../scripts/<name>.py <verb> <args...>
  ```

Why:

- `run.sh` probes `python3 → python → py` so it works on any host
  with Python 3.8+ on PATH.
- Bare `python3 resolve_root.py …` calls fail in most cwds because
  the scripts are not on PATH and the agent doesn't know where it
  is. See the skills' `SKILL.md` (Iron Rules) for the hard rule.

Match the caller-appropriate form above when adding a new entry point.

## Test conventions

Run the suite from the repo root:

```sh
python3 -m pytest plugins/specode/tests/ -v
```

The suite currently covers `resolve_root.py` (3-tier specsRoot
resolution priority, `set-root` persistence + absolute-path rejection,
`list-specs` behavior, project_root read/write, autonomous-mode
defaults, `design-unchecked`) and `knowledge.py` (MEMORY
rebuild/validate, `ensure-gitignore`, `copy-to`), plus the SessionStart
cache-drift hint. There is **no** state machine, lock, selector-drift,
or template-lint test anymore — those mechanisms were removed in 1.0.0.

When adding behavior, prefer:

- Unit tests that call the CLI script through `subprocess.run` via the
  `run_script` fixture (the scripts are CLIs, not importable modules).
- Use the `fake_home` fixture to redirect `$HOME` / `XDG_CONFIG_HOME`
  and clear `SPECODE_ROOT`, keeping tests isolated from the real
  `~/.config/specode/`.
- For hook tests, feed stdin payloads matching the host CLI hook schema
  and assert against the JSON `additionalContext`.

## Hook safety contract

The single hook handler in `spec_hooks.py` (`SessionStart`) MUST:

1. Catch all exceptions internally and return 0.
2. **Never `exit 2`.** It is advisory only. If you need to influence
   the model, inject `additionalContext` JSON to stdout and still
   `exit 0`.
3. Tolerate non-TTY / empty stdin (hook payload arrives via pipe). The
   script must not block when stdin is a TTY.

## Persisted config

The plugin owns two persisted files:

- `~/.config/specode/config.json` — currently holds only `specsRoot`
  (the user's document directory, used verbatim as the specs root).
- `~/.config/specode/defaults.json` — optional autonomous-mode
  defaults (`interactive` / `project_root_default` /
  `execution_mode_default` / `auto_distill` / `specs_root_default`),
  written via `resolve_root.py write-default`; env vars
  (`SPECODE_*`) always win over it.

There is no per-session state file and no per-spec config/lock file
anymore — spec state is inferred from the documents on disk (which
fixed docs exist + `- [ ]` progress in `design.md`). Config writes use
`tempfile + os.replace + fsync` (`_atomic_write_json` in
`resolve_root.py`).

## Release

Public release procedure for plugin maintainers.

### Multi-host manifest convention

Every plugin ships **four** independent host manifests, one per
supported host, plus a matching **root catalog** per host. All eight
sites carry the same `version` and MUST stay in lock-step:

| Host | Per-plugin manifest | Root catalog |
| --- | --- | --- |
| Claude Code | `<plugin>/.claude-plugin/plugin.json` | `.claude-plugin/marketplace.json` |
| CodeBuddy | `<plugin>/.codebuddy-plugin/plugin.json` | `.codebuddy-plugin/marketplace.json` |
| Codex | `<plugin>/.codex-plugin/plugin.json` | `.agents/plugins/marketplace.json` |
| Kimi | `<plugin>/.kimi-plugin/plugin.json` | `.kimi-plugin/marketplace.json` |

The `.claude-plugin/plugin.json` version is the **canonical** source.
When bumping a plugin, change all four host manifests and all four root
catalogs together — `scripts/check_marketplace_versions.py` (the CI
gate) validates that all four hosts are in lock-step and refuses
otherwise. Plugins with hooks (specode, ragkit) additionally maintain
per-host hook files under `hooks/` (`hooks.json` for Claude,
`hooks.codebuddy.json`, `hooks.codex.json`) that differ only in the
plugin-root env var; the `SessionStart` handler script itself is shared.
Codex and Kimi are experimental (unverified on a real host) — see
README §Multi-host support.

### Version manifests (must agree)

Each plugin's version lives in **four** per-plugin host manifests and
**four** root catalogs (see Multi-host manifest convention above). They
MUST all match or both the CI gate
(`scripts/check_marketplace_versions.py`) and the plugin tag tooling
refuse to operate. The `.claude-plugin/plugin.json` version is
canonical:

- `plugins/<plugin>/.{claude,codebuddy,codex,kimi}-plugin/plugin.json` → `"version": "X.Y.Z"`
- each root catalog (`.claude-plugin/marketplace.json` /
  `.codebuddy-plugin/marketplace.json` / `.agents/plugins/marketplace.json`
  / `.kimi-plugin/marketplace.json`) → **that plugin's** entry's `version`
  (leave the other plugins' entries untouched)

### Picking the next version (semver)

"API surface" for semver purposes = the four command names
(`/specode:spec <需求>` / `/specode:continue <slug>` /
`/specode:list` / `/specode:distill [<slug>]`), the `SessionStart`
hook event, the persisted `config.json.specsRoot` field, and the 3
fixed document filenames (`requirements.md` / `design.md` /
`implementation-log.md`) that users or future runtime code observe.

| Bump | When | Examples |
| --- | --- | --- |
| **major** | A user feels a breaking change after a plugin update | rename / remove a `/specode:*` command; rename a hook event; rename `config.json.specsRoot`; rename a fixed document filename |
| **minor** | Backwards-compatible new capability or evolution | new `/specode:*` command; new optional config field; new selector option |
| **patch** | Bug fix / docs / internal refactor with no surface change | fix a typo in a prompt; clarify a reference; CI-only; remove dev-only files from the repo |

When in doubt, bump higher.

### Cutting a release

```sh
# 1. Bump all four host manifests + all four root catalogs to the new
#    version (Claude / CodeBuddy / Codex / Kimi — see Multi-host
#    manifest convention). check_marketplace_versions.py validates all
#    four hosts are in lock-step.
$EDITOR plugins/<plugin>/.claude-plugin/plugin.json
$EDITOR plugins/<plugin>/.codebuddy-plugin/plugin.json
$EDITOR plugins/<plugin>/.codex-plugin/plugin.json
$EDITOR plugins/<plugin>/.kimi-plugin/plugin.json
$EDITOR .claude-plugin/marketplace.json
$EDITOR .codebuddy-plugin/marketplace.json
$EDITOR .agents/plugins/marketplace.json
$EDITOR .kimi-plugin/marketplace.json

# 2. Land the plugin's CHANGELOG: rename `## Unreleased` →
#    `## X.Y.Z (YYYY-MM-DD)`, then add a fresh empty `## Unreleased`
#    above it for the next cycle
$EDITOR plugins/<plugin>/CHANGELOG.md

# 3. Run the version-sync gate (the same check CI runs)
python3 scripts/check_marketplace_versions.py

# 4. Run that plugin's test suite one more time
python3 -m pytest plugins/<plugin>/tests/ -q

# 5. Commit + push
git commit -am "Bump <plugin> to X.Y.Z: <summary>"
git push

# 6. Dry-run the tag first
claude plugin tag --dry-run plugins/<plugin>
# (or codebuddy plugin tag --dry-run plugins/<plugin> — pick whichever
#  host CLI is installed; both wrap the same git operations)

# 7. Create + push the annotated tag
claude plugin tag plugins/<plugin> --push
```

Tag format: `<plugin>--v{version}` (annotated, message
`<plugin> {version}`, e.g. `specode--v5.1.2` /
`task-swarm--v0.10.1`). The plugin is **not** packaged into a tarball
or registry artifact — host CLIs fetch the marketplace manifest
directly from GitHub and resolve plugins by git tag. **Pushing the
tag IS the release.**

### Re-tagging the same version

Only safe if no user has installed it yet:

```sh
git tag -d <plugin>--vX.Y.Z
git push --delete origin <plugin>--vX.Y.Z
claude plugin tag plugins/<plugin> --push      # re-create
```

Once a release is in user hands, prefer a new patch version.

### Verifying after release

```sh
# Adjust the CLI name for whichever host you use (claude / codebuddy).
# The marketplace name is `pluginhub` (the repo name), NOT `qxbyte`.
claude plugin marketplace update pluginhub
claude plugin install specode@pluginhub      # or `update`
claude plugin list | grep specode             # confirm new version
```

Users on a different host follow the same procedure with their host's
CLI name (`codebuddy plugin …`).
