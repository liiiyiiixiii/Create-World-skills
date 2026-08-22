# Film-adaptation workflow

Read this reference for every game-dialogue task adapted from a film. It is film-agnostic: inspect the current project and selected movie instead of assuming the structure, tone, or dialogue model of a previous game.

## 1. Define the adaptation boundary

Record the exact work in scope:

- film title, year, release/cut, and language or dub when relevant;
- whether sequels, prequels, remakes, deleted scenes, or licensed tie-in material count;
- where the game branches from the film timeline;
- whether the player controls a film character, a new character, or an observer;
- which game inventions override or extend the film.

Classify the request:

- **interactive reconstruction:** turns a known film moment into player action;
- **gap scene:** fills time between film scenes without changing their outcomes;
- **branch:** explores an outcome the film did not take;
- **side quest:** adds a game-native objective around film characters;
- **ambient layer:** gives NPCs routine, relationship, and world texture;
- **repair or expansion:** revises existing game dialogue while preserving triggers and state.

This classification determines how much freedom is safe. A gap scene must land cleanly on later film continuity. A declared branch may diverge after its branch point but must track the consequences.

## 2. Build a film evidence packet

Inspect local game material first. Research the film only for gaps that affect the scene.

Capture paraphrased evidence, not quotations:

- the character's repeated decisions under normal conditions and stress;
- how they speak differently to authority, allies, strangers, rivals, and dependents;
- pace, sentence shape, formality, humor, evasion, silence, and recurring subject domains;
- their repeated conversational moves and the kinds of candor, jokes, or eloquence they avoid;
- what the character knows at this exact point in the film;
- relationship changes before and after the nearest film scenes;
- period, location, institutions, objects, and social assumptions that constrain wording;
- performance information that belongs in animation, staging, pauses, or camera behavior rather than spoken text.

Separate evidence from interpretation. “Leaves rather than answering” is behavioral evidence; “emotionally avoidant” is an inference. Both may help, but they do not have equal authority.

## 3. Convert film function into game function

Write the film beat in one sentence: what changes for the characters or audience. Then design the playable equivalent.

| Film element | Possible game conversion |
|---|---|
| Expository conversation | Investigation, optional questions, environmental clue, or a shorter confirmation exchange |
| Silent performance | Animation, navigation, timing, object interaction, or a player-controlled pause |
| Montage | Repeated tasks with evolving barks, relationship variants, or time-state transitions |
| Dramatic reveal | Evidence assembly, observation requirement, choice, failed interpretation, or delayed confirmation |
| Character decision | Player choice when divergence is allowed; otherwise a controlled-character commitment grounded in prior play |
| Background world detail | NPC-to-NPC ambient talk tied to location, schedule, props, and current events |

Do not make dialogue explain an action the player just performed or an emotion already clear from performance. Use speech for negotiation, interpretation, concealment, relationship, and decisions that the interaction cannot convey alone.

After assigning game function, run the full process in [conversation-craft.md](conversation-craft.md). Game utility is the skeleton; character pressure and turn-by-turn response make it conversation.

## 4. Preserve character identity under interactivity

A controlled film character is not a blank player insert. Choices should form a credible possibility space for that character at that moment. If a requested player choice would break the character or later continuity, either:

- frame it as tone or method rather than a contradictory goal;
- mark the scene as an explicit alternate branch;
- show a believable cost and propagate the divergence;
- explain the incompatibility before generating when no honest adaptation is possible.

New player characters need their own knowledge and relationship boundaries. Film NPCs should not trust them merely because the audience recognizes the character.

## 5. Generate dialogue by interaction type

### NPC to player avatar

Define what each side wants before writing. Let the film NPC pursue their own goal, test the avatar, withhold information, bargain, misread, or leave. End with an actionable or emotional change, not a disguised quest log.

### NPC to NPC

Give the exchange a reason independent of player observation. Ambient dialogue should reveal routine, friction, shared history, local change, or partial information. Major film facts should not become casual public knowledge unless the timeline and participants justify it.

### Reactive barks

Tie barks to an observable trigger and emotional delta. Create state variants only when the event, relationship, danger, or knowledge has changed. Avoid generic pools that could be spoken by every character.

## 6. Check adaptation integrity

Before delivery, verify:

- **version:** every imported fact belongs to the chosen film continuity;
- **timeline:** nobody knows later revelations or relationship outcomes;
- **function:** the scene advances play, character, relationship, atmosphere, or evidence;
- **agency:** player action matters where the design promises agency;
- **consequence:** branches propagate rather than snapping back without explanation;
- **voice:** wording follows behavior observed in the film without copying its dialogue;
- **naturalness:** turns respond, shared context stays implicit, and speech is not uniformly polished;
- **interest:** the scene contains relationship texture, a micro-turn, tension, or earned humor without breaking tone;
- **performability:** an actor could speak and stage the lines within the presentation budget;
- **medium:** animation, environment, UI, and mechanics carry what they can;
- **format:** output matches the current project's data and rendering limits;
- **originality:** the result is a new scene or interactive transformation, not a reconstructed screenplay passage.

## 7. Stop condition

The task is ready to draft when the film version, game branch point, character knowledge, relationship state, gameplay transition, output format, and line budget are known or safely assumed. Do not delay generation for trivia that cannot change the scene.
