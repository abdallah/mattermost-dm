# mattermost-dm

An agent skill and a small script that let Claude Code send Mattermost direct messages as you, with
a preview you approve first.

This is a safe DM workflow, not a general Mattermost client. It adds these guarantees on top of the
Mattermost API:

- **Exact preview:** `--send-pending` sends exactly what the last `--dry-run` printed, once, within
  an hour.
- **All-or-nothing batches:** if one recipient doesn't resolve, the preview can't be sent.
- **Per-person messages:** `{hi}` adds a greeting only when one is due, and `{first_name}` fills in
  each name.
- **Token handling:** the script loads the token itself and never prints it, and the skill tells
  Claude not to read the file.
- **Reply waiting:** `--wait-reply` blocks until someone answers, which suits a background command.

## Requirements

- Python 3.9 or later. The script has no third-party dependencies.
- A Mattermost personal access token. Create one in **Profile > Security > Personal Access Tokens**.
  If that option is missing, ask your Mattermost administrator to enable personal access tokens.

## Install

1. Clone the repo into your skills folder. The folder must not exist yet:
   ```sh
   git clone https://github.com/abdallah/mattermost-dm.git ~/.claude/skills/mattermost-dm
   ```
2. Create `~/.mattermost` so that only you can read it:
   ```sh
   touch ~/.mattermost && chmod 600 ~/.mattermost
   ```
3. Add your server and token to that file:
   ```sh
   MM_URL=https://chat.example.com
   MM_TOKEN=your-token
   ```

## Use

Ask Claude Code to message someone, for example "DM alex@example.com and ask for the staging plan".
Claude shows you the rendered message and sends it after you confirm.

You can also run the script yourself. Run `./mm-dm --help` for every option.

```sh
./mm-dm --dry-run --to alex@example.com --message-file - <<'MSG'
{hi}

can you share the staging plan?
MSG
./mm-dm --send-pending
```

## Add your voice

Your voice lives in `voice.md`, next to `SKILL.md`. Git ignores this file, so it stays on your
machine. Without it, Claude writes short, friendly, plain messages.

### Write it by hand

1. Copy the template:
   ```sh
   cp voice.example.md voice.md
   ```
2. Replace each line with your own habits.

### Learn it from your messages

1. Choose three to five people you message often, across different kinds of work.
2. Ask Claude Code to draft the file:
   ```
   Run mm-dm --history <name> --days 90 for each of these people: <names>.
   Learn only from messages I wrote. Draft voice.md from voice.example.md. Describe my habits for
   length, capitals, punctuation, greetings, asks, warmth, common words and links, and what I never
   do. Copy my habits, not my typos. Don't include real names, projects, clients or quoted messages.
   Show me the draft before you save it.
   ```
3. Read the draft and correct anything that doesn't sound like you.
4. Ask Claude to draft a few test messages, and adjust `voice.md` until they sound right.

`--history` prints both sides of each conversation, so your colleagues' messages reach your AI
provider during this step. Check your company's policy and choose conversations with no confidential
content. To avoid this, write the file by hand.

### Set your greetings

`{hi}` comes from the script, not from `voice.md`. To use your own greetings, add `|`-separated lists
to `~/.mattermost`:

```sh
MM_DM_GREETINGS_AM="good morning|morning :)"
MM_DM_GREETINGS_PM="hi there|hey|good afternoon"
```

### Use it on several machines

Copy `voice.md` to each machine yourself, because Git doesn't sync it. `contacts.json` is also local
to each machine, and it builds up as you send messages.

## Your data

| File | Holds | Where it stays |
|---|---|---|
| `~/.mattermost` | Server URL and token | Your home folder |
| `voice.md` | Your writing style | Skill folder, ignored by Git |
| `contacts.json` | Names and emails of people you messaged | Skill folder, ignored by Git |
| `~/.cache/mm-dm/pending.json` | The last previewed message | Your cache folder, deleted when sent |

## When to use something else

- For a full terminal client, use [`ziyan/mm`](https://github.com/ziyan/mm).
- For reading mentions, unread messages and search, use
  [`rhnvrm/mattermost-cli`](https://github.com/rhnvrm/mattermost-cli).
- For a server-supported integration, use the
  [official Mattermost MCP server](https://github.com/mattermost/mattermost-plugin-agents/tree/master/mcpserver).

## Test

```sh
python3 -m unittest discover -s tests
```

## License

[MIT](LICENSE)
