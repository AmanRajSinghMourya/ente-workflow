# Copywriter

Tries to write friendly words.

Quality is not deterministic. Run until you find happiness.

## Install

Copy the folder into your agent’s skills directory.

- OpenAI Codex CLI: `cp -r copywriter ~/.codex/skills/`
- Claude Code: `cp -r copywriter ~/.claude/skills/` or `cp -r copywriter .claude/skills/`
- GitHub Copilot / VS Code: `cp -r copywriter .agents/skills/`
- Cursor: `cp -r copywriter .cursor/skills/`
- Claude.ai: `zip -r copywriter.zip copywriter/` and upload in **Settings → Features → Custom Skills**

## Use

You can use it for individual strings and dialog contents.

Example:

```
$copywriter We have done some improvements on our embeddings DB to make it feel instant.

• 1. We improved our search so it feels instant.
  2. We made our search system faster so results show right away.
  3. We upgraded the way we organize your photos so finding them feels instant.

  Jargon log: embeddings, DB
  Readability note: ~6th grade reading level
  Flagged concerns: “instant” is a strong claim and might be misleading if there is any delay in some cases.
```

```
$copywriter I have a screen where the user has to click a button to free up space by deleting photos
    from device that have already been backed up. Please share copies for the final confirmation dialog
    clicking which we will perform this operation.

  1. Title: Free up space
     Dialog message: Delete photos from this device that are already backed up.
     Button labels: Free up space, Not now
  2. Title: Clear space now
     Dialog message: We will remove photos from this device that are safely backed up.
     Button labels: Remove from device, Cancel
  3. Title: Remove backed up photos
     Dialog message: This will delete photos from this device after they are backed up.
     Button labels: Delete photos, Later

  Jargon log: device, backed up
  Readability note: ~6th grade reading level
  Flagged concerns: “safely” may be inaccurate if there is any chance of incomplete backup.
```

## Output

- Three rewrite options (shortest first)
- Jargon list
- Readability note
- Flagged concerns
