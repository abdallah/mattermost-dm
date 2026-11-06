---
name: mattermost-dm
description: Send Mattermost direct messages as the user (one person or a batch, with {first_name} personalisation) using their personal token from ~/.mattermost. Use when the user asks to DM, message, ping or notify colleagues on Mattermost. Claude runs the script itself; the script loads the token, so it never passes through Claude.
---

# mattermost-dm

Script: `~/.claude/skills/mattermost-dm/mm-dm`. It takes the server URL and token from environment
variables, or reads them from `~/.mattermost` when they're unset, and never prints them. Claude runs
the script directly with Bash. Don't read, cat, grep or source `~/.mattermost` yourself: the token
must never enter the conversation.

## Steps

Two tool calls per message: one preview, one send. Don't write message files, and don't run a
separate greeting check.

1. **Preview.** Draft the text in the user's voice (see "The user's voice") and pass it on stdin in
   one Bash call:
   ```
   ~/.claude/skills/mattermost-dm/mm-dm --dry-run --to name@company.com [--to ...] --message-file - <<'MSG'
   {hi}

   can you check the staging plan on [!885](https://gitlab.example.com/group/project/-/merge_requests/885) when you get a minute? no rush
   MSG
   ```
   - Start with `{hi}` on its own line. The script fills in a greeting when the user hasn't spoken to
     that person today or for over 4 hours, and drops it (and the blank line) otherwise. It works
     per person in a batch.
   - `{first_name}`, `{last_name}`, `{username}` personalise a batch; double literal braces `{{ }}`.
   - Prefer emails for `--to` (the username often differs from the email's local part). Many
     recipients: `--to-file <file>`, one per line, `#` comments.
   - No dates or promises the user did not give you, and no review-speak ("the part worth your
     eyes"). Lead with what you need, then one or two lines of context.
   - Always hyperlink a merge request, issue or ticket: `[!2830](https://gitlab.example.com/group/project/-/merge_requests/2830)`,
     never a bare `!2830`. These numbers are per project, so take the project from the item itself,
     not from the current repo. If you do not know the project, ask.

   Show the user the rendered messages from the output. Every recipient line must say `ok`; a `FAIL`
   means that email or username isn't on Mattermost: fix it or drop the person, and preview again.
2. **Send.** When the user confirms, run:
   ```
   ~/.claude/skills/mattermost-dm/mm-dm --send-pending
   ```
   It sends exactly what the preview printed, once, within an hour; then report the `sent <username>
   post <id>` lines. If the text changes, preview again: never send text the user hasn't seen.

If the user already approved the exact text and says "send it", preview and send in one Bash call
(`mm-dm --dry-run ... && mm-dm --send-pending`) and show the output.

`mm-dm --last-spoke --to <person>` prints the greeting status alone, without a preview, if you need it.

## Posting to a channel

`--channel TEAM/CHANNEL` (or a bare 26-char channel id, for group messages) posts once to a channel instead of DMs. TEAM and CHANNEL are the names in
the channel URL (for example `my-team/town-square`). Run it with `--dry-run` first: the output names
the channel it resolved. It prints `sent TEAM/CHANNEL post <id>`.

```
~/.claude/skills/mattermost-dm/mm-dm --channel my-team/town-square --message-file <msg> [--dry-run]
```

## Editing a post

`--edit POST_ID` replaces the text of a post you own with `--message-file`. `--attach FILE` uploads a
file to the post's channel and sets it as the post's attachment in the same edit. It replaces any
files already on the post. Show the user the new text before you run it.

```
~/.claude/skills/mattermost-dm/mm-dm --edit <post id> --message-file <msg> [--attach <file>]
```

## The user's voice

Before drafting, read `voice.md` next to this file. It is the user's personal style guide: copy its
habits, not its typos. If it doesn't exist, write short, friendly, plain messages, like a note to a
teammate, with no formal opening or closing, backticks or bold.

If the user asks to create or refresh `voice.md`, follow "Add your voice" in `README.md`.

## Reading a conversation

`--history USER [--days 14] [--grep TEXT]` prints the DM with one person, oldest first. It only
reads. Use it when the user asks you to, because it brings both sides of a private conversation into
the session.

## Waiting for a reply

When the user wants to know when someone answers, run this as a background command (Bash
`run_in_background`) with the post id from the `sent` line:

```
~/.claude/skills/mattermost-dm/mm-dm --wait-reply <post id> [--interval 60] [--timeout-hours 24]
```

It polls that post's channel and exits 0 as soon as anyone other than the token's owner posts after
it (a DM reply or a thread reply), printing each reply with its author and time. Exit 3 means no
reply before the timeout. The harness notifies you when it exits: read the output and relay the
reply to the user. It only reads; it never posts.

## Notes

- Contacts: after each successful send, the script saves the recipient to `contacts.json` next to
  it, under the name used, their username, email, the email's local part, nickname and full name.
  Later sends resolve those names from the file with no lookup. If the person is in `contacts.json`,
  send to that name directly: no guessing usernames, and no dry run only to resolve them.
- Messages go out as the token's owner (the `from:` line in the output). Never send to people the
  user did not name, and never send text the user has not seen.
- If the output says `none of these are set`, the env file uses other variable names: ask the user
  for `! grep -oE '^(export )?[A-Za-z_]+' ~/.mattermost` (names only) and extend `URL_NAMES` /
  `TOKEN_NAMES` in the script.
- A 401 means the token expired or was revoked; the user creates a new personal access token in
  Mattermost (Profile > Security > Personal Access Tokens) and updates `~/.mattermost`.
