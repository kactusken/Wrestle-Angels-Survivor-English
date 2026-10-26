# Translation

## Where the text is

| File | Holds | Tool |
|---|---|---|
| `translation/script/NNN.txt` | event scripts: 8348 distinct messages (entry 321 = match commentary) | `tools/script.py` |
| `translation/script/quotes.txt` | pre-match quotes (/A040/A048.) | `tools/quotes.py` |
| `translation/text/exe.csv` | the executable's menus, messages, lists | `tools/exetext.py` |
| `translation/text/roster.csv` | wrestler and coach names, finishers | `tools/roster.py` |
| `translation/letters/*.json`, `translation/images-handmade/` | pictures with text (lettered) | `tools/letter.py`, `tools/gfx.py` |
| `translation/glossary.csv` | terms | `tools/lint.py` |

## File formats

Message blocks: `@ id`, source lines (`JP `), translation lines (`EN `); no `EN` lines = original
kept. A file's header says what it holds and its limits (`# limit lines=3 chars=28` is checked by
lint). Tables: original columns beside English ones (`japanese`/`english`, or `X`/`en_X`). See
`tools/blocks.py` and `tools/textdb.py`.

Control codes: `{name:N}` = a name the game fills in (FF 01 + u16 N: wrestler N's name in
events; in the commentary {name:2}/{name:3} are move names and {name:60}... pauses). Line breaks
are the EN lines themselves. In exe.csv: `\n` line break, `\k` new page, `%s`/`%d` values.

## Style guide

*Carried over from the WAS2 translation (approved there 2026-10-18); adopted for this game by the user, 2026-10-24.*

- **The player** is 社長, the (male) president of the promotion. Speaker label: `President`.
  When wrestlers address him: `Boss` (`President` in formal scenes - contracts, ceremonies,
  outsiders). His own narration in parentheses is first person: `(I offered her a contract.)`
- **Names**: Western order for full names (`Suzumi Ishikawa`); characters who use a surname
  keep the surname (`Ishikawa`). Ring names as in `translation/text/speakers.csv`. The table is
  the reference for every name in dialogue too.
- **Honorifics**: dropped (`石川さん` → `Ishikawa`, `ちゃん` → first name) except `senpai`, which
  carries the seniority that matters in joshi wrestling (`Senpai!`).
- **Thoughts and narration** in （） stay in parentheses: `(She seems tougher than she looks.)`
- **Quotes** 「」『』 → double quotes. Ellipses `…`/`……` → `...`. Stammers `そ、そうか` → `S-sure.`
  Drawn-out `～` at the end of a line: usually drop it or use `!`; keep `~` only for a sing-song
  voice where it carries character.
- **Voice**: wrestlers have strong personalities (tough, cute, haughty, sleepy, theatrical...).
  Keep each one's register and verbal tics (`うきゅ` → `Ukyu`), and keep catchphrases consistent
  within a character's file. The President is polite but plain-spoken.
- **Wrestling terms**: natural English pro-wrestling vocabulary (glossary).

## Glossary

`translation/glossary.csv` (`japanese, english, notes`): lint warns when a source line contains a
term and the English doesn't use its translation (several accepted forms: `A | B`). Prefer
established community names (existing English guides) over new coinages.

## Decisions

| Decision | Who / why |
|---|---|
| Reuse WAS2's approved choices: style guide, President/Boss, honorifics, name readings, lettering style A (Barlow Condensed, original colours) | the user, 2026-10-24 |
| Scope as in WAS2: event scripts, the executable's text, roster/move/other names, text pictures; logos and staff credits stay Japanese | the user, 2026-10-24 |
| WAS2's translations of the same names, terms and interface strings are reused as the starting point | Claude, 2026-10-24, following the decision above |
| English drawn with the font's own half-width set, fixed 11 px per letter, 36 letters per line; WAS2's proportional font is a later step (needs in-game testing here) | Claude, 2026-10-24 |
| ちーちゃん = Chii (as WAS2); 革命軍 Revolution Army, 反乱軍 Rebel Army, 正規軍 the regulars | Claude, 2026-10-24 (consistency pass) |
| New names (not in WAS2): Hikaru Sawazaki, Rina Nakae, Sanae Katsuragi, Mizuki Tachibana, Reira Kirishima, Miki Shibata, Miki Akiyama, Nanashi Kamishio, RIKKA, secretary Kiriko Inoue | Claude/agents, 2026-10-24 - to confirm |

## What stays untranslated

- Staff credits (A026 pictures), promotion logos (A01F), the title logo (English already).
- The name-entry kana/kanji grid (players type Japanese names).
- Voices (Japanese audio).
