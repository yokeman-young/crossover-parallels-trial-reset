# Installing the agent skill

The skill lives in `skills/trial-reset/SKILL.md` (frontmatter + procedure). Copy the directory into
your agent's skill location:

```bash
# Claude Code
mkdir -p ~/.claude/skills && cp -R skills/trial-reset ~/.claude/skills/

# DeepSeek Harness
mkdir -p ~/.dsh/skills && cp -R skills/trial-reset ~/.dsh/skills/
```

After that the agent can pick it up by name (`trial-reset`) and will follow the procedure:
inventory → dry-run → apply → verify → optional launcher/watcher/block.

The skill intentionally contains the assertion table and failure map, so an agent can tell
"reset succeeded" from "adapter is stale" without human interpretation.
