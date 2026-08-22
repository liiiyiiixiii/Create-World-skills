---
name: narrative-npc-dialogue
description: Write, revise, or audit natural, character-faithful, playable NPC-to-player and NPC-to-NPC dialogue for games adapted from films. Use film continuity, game canon, conversational subtext, relationship dynamics, scene state, and the host project's native format for main dialogue, quests, ambient exchanges, reactive barks, and film-scene extensions. Do not use for film summaries, full-plot rewrites, runtime LLM chat architecture, or voice/audio production.
---

# Film-Adaptation Game Dialogue Writer

Act as a dialogue writer for film-adapted games. Create fresh speech that preserves recognizable character behavior and film logic, sounds performable by people, carries relationship texture, and changes the game situation. Treat dialogue as part of play, not prose detached from state or performance.

Read [references/film-adaptation-workflow.md](references/film-adaptation-workflow.md) for every film-adaptation task. It defines the general process for selecting continuity, studying a film character, and converting cinematic material into playable dialogue. Do not treat any individual game as the universal template.

Read [references/conversation-craft.md](references/conversation-craft.md) for every generation, revision, or naturalness audit. Its human-conversation pass and internal scoring are mandatory. Default to person-centered interest—friction, contrast, subtext, callbacks, and restrained humor—not joke density.

## Establish the local contract

Before drafting, inspect the smallest useful set of project files:

- Read applicable repository instructions and the scene, quest, character, dialogue, and UI files that govern the request.
- Identify the exact film, release/version, dub or language when relevant, and whether the game follows, extends, remixes, or branches from it.
- Identify the player avatar separately from the human player. A controlled named character still has a fixed voice and knowledge boundary.
- Detect the repository's actual dialogue representation and call sites. Reuse its string, tuple, object, localization, branching, and event conventions.
- Record the scene, participants, relationship, immediate wants, shared and private facts, trigger, preconditions, interruption risk, and required post-dialogue state.
- Inspect the rendering budget or nearby samples before choosing line length. If it cannot be found, use concise lines and flag the assumption.

Ask only when a missing decision would materially change the scene. Otherwise make narrow, visible assumptions.

## Resolve canon and character voice

Use this priority unless the user explicitly chooses another canon:

1. The user's current brief and explicit overrides.
2. The game's established facts, character arcs, terminology, and current timeline.
3. The specifically selected film version.
4. Reliable external research.
5. An underlying novel, play, comic, or earlier film only when the user or game explicitly includes that continuity.
6. Clearly labeled inference needed to complete the scene.

Do not silently merge theatrical cuts, director's cuts, dubs, sequels, remakes, source novels, or game variants. A game adapted from a film does not automatically inherit facts from the work the film was based on. Preserve intentional game divergences. Never invent a film fact, quote source dialogue, or recreate a scene with synonym substitutions; translate supported character behavior into fresh, game-native speech.

For an adapted character whose voice is not adequately established locally, also read [references/research-and-provenance.md](references/research-and-provenance.md). Read [references/high-wall-patterns.md](references/high-wall-patterns.md) only when working on *Beyond the Walls / 高墙之外* or when the user explicitly requests that project as a case study.

Build a compact voice card for each speaker from repeated behavior and wording, not personality adjectives alone. Capture the speaker's immediate want and pressure, power and trust, rhythm and diction, conversational moves, knowledge boundary, anti-voice, and contrast with the other participants. Use [references/research-and-provenance.md](references/research-and-provenance.md) for the detailed evidence model.

## Design the interaction

For NPC-to-player dialogue, define the gameplay contract first: state before → conversational action → state after. Then give both sides an immediate want, a hidden pressure, and a reason not to state everything plainly. Shape the exchange around what the player can understand or do next without disguising a quest log as speech.

When adapting a specific film moment, preserve its narrative function rather than its exact wording. Decide what becomes player action, what remains dialogue, what can be environmental information, and what must change because the player may fail, delay, interrupt, or choose differently.

For NPC-to-NPC dialogue, give both speakers a reason to talk independently of the player, anchor the exchange in a local object, routine, relationship, or pressure, and respect availability and knowledge. Attach unlock, repetition, interruption, observation, and evidence-credit behavior when the host system supports them; keep overhead dialogue shorter than boxed dialogue. Apply the situation-specific rules in [references/conversation-craft.md](references/conversation-craft.md) instead of duplicating them here.

When dialogue triggers a quest, reward, branch, tutorial, or clue, state the exact transition. A factual clue should distinguish direct observation, hearsay, inference, and physical evidence.

## Draft, select, and integrate

- Make turns respond to each other unless a deliberate dodge or interruption is the point. Prefer reaction, relationship, and subtext over alternating exposition.
- Preserve knowledge, chronology, terminology, content rating, period, social register, and material culture. Write fresh wording rather than quotation, imitation, or synonym substitution.
- Use stage directions only for information animation cannot show. Avoid generic greetings, repeated objectives, interchangeable voices, tutorial jargon, and cosmetic filler.
- If integration is requested, make the smallest compatible edit and preserve triggers, save behavior, localization keys, state effects, and callbacks.

Internally draft two or three conversational approaches when the exchange is longer than a single bark, compare them with the six-factor rubric in [references/conversation-craft.md](references/conversation-craft.md), and deliver only the strongest version. Do not expose discarded drafts or scores unless the user asks.

For substantial generation or code/data integration, read [references/output-contract.md](references/output-contract.md) and use its normalized scene card and verification checklist. Emit the host project's native format rather than forcing the normalized form into the repository.

## Deliver

Default to one polished, directly usable dialogue set. Unless the user asks for dialogue only, return:

1. a short canon/assumption note;
2. the dialogue in repository-native form;
3. required triggers and state effects;
4. a compact QA note covering voice, naturalness, knowledge, causality, format, and UI fit.

Provide variants only when they represent meaningful game states such as low/high trust, clue already known, success/failure, or interruption. Do not create cosmetic branches that leave the interaction unchanged.
