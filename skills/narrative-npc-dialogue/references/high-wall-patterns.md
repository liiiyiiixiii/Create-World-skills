# 可选案例：《高墙之外》

This is one optional implementation case, not the default structure for film-adapted games. Read it only when working on *Beyond the Wall / 高墙之外*, when the user asks to reproduce its dialogue model, or when its implementation is explicitly selected as a reference for another project.

This original analysis is based only on the publicly released open-source game snapshot. It contains no source-film dialogue, private development material, screenshots, or local-machine paths. When applying it to a newer project version, inspect the public project files supplied for the task because triggers and text may have changed.

## The game's dialogue layers

### 1. NPC-to-player main dialogue

The player controls Andy in the main game, so “NPC-to-player” is normally dialogue between an NPC and Andy, not a personality-free player insert.

Main exchanges use arrays of strings shaped like `角色（可选动作）：文本`. Lines without a recognized speaker become narration. `安迪（心理）` is treated as internal/narrative presentation rather than spoken conversation.

Typical interaction pattern:

1. Andy approaches with a concrete need.
2. The NPC tests motive or risk.
3. A price, task, warning, or choice is established.
4. Control returns to gameplay for a minigame or action.
5. A later exchange confirms completion and delivers the item, clue, or next quest.

Dialogue completion is coupled to quest and save state. Generating replacement text without checking the callback and post-dialogue branch is incomplete.

### 2. NPC-to-player evidence talk

Evidence conversations usually contain four or five turns:

- the NPC supplies one concrete observation, document, object, date, number, or anomaly;
- Andy classifies or connects its significance;
- the NPC marks risk, limits certainty, or explains what can be verified;
- physical objects and oral testimony are kept distinct in inventory/state.

The current evidence chain intentionally cross-corroborates recurring identifiers, dates, vehicles, transfers, and records. Preserve exact shared facts across conversations, but do not make every NPC know the whole chain.

### 3. NPC-to-NPC ambient conversations

Ambient topics are structured objects with:

- a stable `id`;
- `type: "casual"` or `type: "evidence"`;
- two participant IDs;
- short `{ speaker, text }` lines;
- optional evidence ID, label, unlock condition, and `keyEvidence` marker.

The runtime waits for compatible idle actors who are near each other, stages them facing one another, displays one short overhead line at a time, and releases them afterward. Casual topics rotate through a shuffle bag. Evidence topics unlock at specific story states, receive priority after enough casual topics, and can be credited only when the player remains close enough to hear the marked line.

Casual topics are two-line micro-scenes about books, meals, weather, shoes, radio static, sleep, work, and small debts. They establish routine and relationship without sounding like quest text. Evidence topics use the same lightweight presentation but pair a specific observation with corroboration.

### 4. Controlled-character dialogue in endings

In one ending the player controls Red and speaks with a store manager. The tuple format `[[speaker, text], ...]` differs from the main system. Red remains a characterized avatar: hesitation and repeated requests for permission express institutionalization, while the manager's plain reassurance creates the dramatic contrast.

## Project-derived voice cards

These are working constraints, not claims that every trait appears verbatim in the novella.

| Character | Game-native voice | Knowledge and dramatic function | Provenance boundary |
|---|---|---|---|
| Andy | Restrained, analytical, precise; often turns a detail into a plan or evidence link; occasional compact metaphor | Player avatar, planner, accountant, connector of clues; conceals the full escape plan | Game dialogue plus film narrative function |
| Red | Practical broker and risk assessor; dry humor, guarded warmth, concrete questions | Acquires items, reads people, worries about consequences, gradually trusts Andy | Official source identifies him as the prisoner who can obtain things; game extends his evidence role |
| Brooks / 老布 | Patient, formal, gentle; book, paper, patience, and time imagery; warnings carry quiet fatalism | Librarian, giver of books/documents, embodiment of institutionalization | Film version is more expanded than the novella; keep the chosen continuity explicit |
| Tommy | Direct, youthful, confessional under pressure; less polished syntax is acceptable but should remain readable | Eyewitness/testimony carrier who fears retaliation | Source and film establish his revelatory role; game changes the content of his testimony |
| Heywood / 海伍德 | Blunt, observant, practical; notices visible routine and uses dry everyday humor | Group texture and concrete visual corroboration | Primarily film/game characterization |
| Floyd / 弗洛伊德 | Material-minded, skeptical, terse; speaks from what he handled or found | Physical-detail corroboration and grounded banter | Thin source characterization; much of the voice is a game inference |
| Warden / 典狱长 | Commanding, self-justifying, formal; institutional or religious rhetoric masks control and corruption | Authority, threat, inspection, and concealment | The film consolidates/adapts wardens; the game adds a new trafficking conspiracy |
| Guards / 狱警 | Terse commands upward, formal reports to authority, evasive rumor downward | Immediate danger, hierarchy, and partial operational knowledge | Role-based game voice; distinguish named guards if the project later does so |
| Store manager | Plain, patient, non-punitive, direct | Counterpoint to Red's dependence on permission | Game-only character |

## Canon boundaries specific to the game

Treat these as game canon when present in the current build, even though they diverge from the source film or novella:

- the human player is drawn into the film world and acts through Andy;
- the terminology may use “拘禁地”, “被困者”, and “脱离拘禁” rather than the source's ordinary prison vocabulary;
- D-area transfers, missing people, shell-company payments, vehicle identifiers, altered records, and the trafficking evidence chain are game inventions;
- tasks such as radio repair, book sorting, gear calibration, pipe navigation, poster selection, evidence collection, and multi-ending branches determine conversational timing;
- dialogue must cooperate with offline quest flags, checkpoints, achievements, inventory, and evidence state.

Do not “correct” these to the movie. Import source characterization only where it supports the game's version.

## What to preserve and what to improve

Preserve:

- dialogue attached to actions and state transitions;
- concrete clue handoffs and cross-corroboration;
- concise two-line ambient exchanges;
- Andy's analytical response, Red's guarded pragmatism, and Brooks's book/time imagery;
- separation of narration, internal thought, boxed speech, and overhead talk.

Improve when generating new material:

- distribute dense exposition across reaction and verification rather than long monologues;
- give minor NPCs distinct motives beyond delivering a clue;
- let power and risk create subtext instead of repeatedly saying “do not let them know”;
- avoid making villains explain their entire scheme to an ally when a partial, euphemistic exchange would be more credible;
- test repeated ambient lines against story progression so old small talk does not contradict later events.

## Naturalness calibration from the current sample

Preserve the strongest conversational behavior already present:

- Red and Andy's item negotiations contain risk-testing, understatement, and guarded humor rather than a bare transaction.
- The two-line ambient exchanges use concrete routines and props; several reveal relationship through a dry second-line turn.
- Brooks's book and paper imagery feels tied to his role instead of being generic poetic language.

Use the human-conversation pass to catch weaker tendencies before adding new dialogue:

- Evidence scenes can become long factual reports followed by Andy summarizing their meaning. Break the report with doubt, correction, fear, or a relationship-specific response.
- Avoid giving every witness the same “tell facts, warn Andy, ask for secrecy” rhythm. Give each person a distinct reason for speaking and a distinct way of protecting themselves.
- The warden should not state the full conspiracy or praise his own cleverness for the audience's benefit. Let institutional euphemism, partial orders, and the guard's caution reveal complicity.
- Keep useful quest state outside the mouth of the character when the task UI already carries it.

These notes guide future generation and revision only. They are not a substitute for inspecting the current public project, and they do not authorize rewriting existing dialogue unless the user asks.

## Reference anchors

- Stephen King's official work page confirms the 1982 novella, its collection, and basic character roles: <https://stephenking.com/works/novella/rita-hayworth-and-shawshank-redemption.html>
- The American Film Institute catalog identifies the 1994 adaptation, credited roles, source relationship, and major plot functions: <https://catalog.afi.com/Catalog/moviedetails/55199>

Use these anchors for identity and narrative facts. Derive exact game voice first from the current project, then from legally available primary material when more evidence is necessary.
