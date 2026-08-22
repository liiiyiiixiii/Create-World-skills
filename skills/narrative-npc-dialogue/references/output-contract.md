# Dialogue output contract

Read this reference for substantial dialogue generation, branching, batch work, or integration into game code/data.

## Normalized scene card

Use this as a thinking and review model. Do not impose it on a repository that already has a schema.

```yaml
scene_id: stable-local-id
mode: npc_player | npc_npc
location: where the exchange occurs
timeline: exact point in the story
participants:
  - id: stable-character-id
    role: player_avatar | npc
trigger: proximity, interaction, quest event, timer, or observation
preconditions: []
relationship_state: relevant trust, debt, fear, rank, or history
relationship_texture: what familiarity, friction, dependence, or status sounds like here
facts:
  shared: []
  private_by_character: {}
  may_reveal: []
  must_not_reveal: []
interaction_goal: what changes because the conversation happens
subtext: what is negotiated without being stated directly
emotional_turn: smallest meaningful change in feeling or expectation
interest_device: one restrained source of person-centered interest, or none for austere scenes
conversation_moves:
  character_id: [open, probe, evade, disagree, soften, joke, leave]
forbidden_patterns:
  character_id: [speech or behavior that would break the voice]
state_effects: []
presentation: boxed | overhead | bark | cinematic | other
ui_budget: line and character constraints
repetition_policy: once, cooldown, shuffle bag, state variant, or repeatable
```

For evidence-bearing scenes, add provenance per fact: `direct_observation`, `physical_evidence`, `hearsay`, or `inference`.

## Beat table

Plan only the beats the scene needs. This is scene-level scaffolding, not a demand that every spoken line advance plot. A beat may be carried by action, silence, relationship texture, or a brief hesitation.

| Beat | Speaker action | Listener change | Game purpose |
|---|---|---|---|
| Contact | Opens, tests, or interrupts | Pays attention | Establishes context |
| Pressure | Requests, refuses, warns, bargains | Understands obstacle | Creates friction |
| Turn | Reveals, notices, chooses, or reframes | Gains actionable understanding | Advances state |
| Exit | Commits, withholds, redirects, or departs | Knows what to do or feel next | Hands control back |

If two adjacent beats cause the same listener change, compress them.

## Repository-native payloads

Detect and use the existing form. Common examples:

String-array dialogue:

```js
const GatekeeperWarningLines = [
  "守门人（看向远处）：巡逻刚换班。现在过去，只会撞上他们。",
  "玩家：那我等钟声以后再走。"
];
```

Structured ambient topic:

```js
{
  id: "casual_mechanic_cook_bad_kettle",
  type: "casual",
  participants: ["mechanic", "cook"],
  lines: [
    { speaker: "mechanic", text: "水壶又漏了？" },
    { speaker: "cook", text: "它比我们更想离开这间厨房。" }
  ]
}
```

Tuple dialogue:

```js
[
  ["管理员", "你可以自己决定先做哪一件。"],
  ["玩家角色", "……我还不太习惯。"]
]
```

When the repository separates text from actions, conditions, or effects, keep them separate. Do not hide state mutation inside dialogue strings.

## Branching rules

Create a branch only when at least one changes:

- available knowledge;
- relationship or leverage;
- player choice;
- success/failure outcome;
- reward, quest, or evidence state;
- future availability or risk.

Each branch needs a distinct entry condition and an explicit merge or terminal state. Avoid near-duplicate branches that differ only in politeness.

## Line-budget fallback

The renderer is authoritative. If it cannot be inspected, use these conservative Chinese-language fallbacks:

- overhead/bark: roughly 8–24 Han characters per line;
- ordinary dialogue box: roughly 12–40 Han characters per line;
- put one dense factual unit in a line and let another speaker react before adding more;
- use at most one short stage direction when it affects interpretation.

Count punctuation and embedded variables in the real payload. Prefer a second line over font shrink or truncation.

## Verification checklist

- **Causality:** Preconditions justify the exchange; post-state follows from it.
- **Naturalness:** Each non-deliberate reply connects to the preceding turn; shared facts are not over-explained.
- **Voice:** Removing names would not make every speaker interchangeable.
- **Interest:** The exchange contains a relationship detail, micro-turn, tension, memorable image, or earned humor appropriate to tone.
- **Performability:** Lines are speakable, stageable, and not dependent on decorative directions.
- **Knowledge:** Each claim has an available source and correct certainty.
- **Relationship:** Address, politeness, interruption, and risk match history and power.
- **Gameplay:** The player receives no more and no less direction than the scene requires.
- **Evidence:** Testimony, hearsay, inference, and physical proof are not conflated.
- **Continuity:** Names, timeline, locations, items, quest IDs, and prior choices agree.
- **Repetition:** Repeatable dialogue does not repeatedly award state; ambient topics have suitable cooldown or variation.
- **Presentation:** Text fits the renderer and stage directions do not duplicate animation.
- **Integration:** Syntax, IDs, callbacks, save flags, localization, and call sites match the host project.
- **Freshness:** No source quotation, imitation, or thin paraphrase slipped into the final text.

For a batch, review the full set for repeated sentence shapes, metaphors, openings, and final instructions—not only each scene in isolation.

## Default delivery

Internally compare two or three approaches for exchanges longer than a single bark. Return one polished repository-native payload, not a menu of cosmetic alternatives. Include only the canon assumptions and state/integration notes needed to use it. Provide candidates or the private six-factor assessment only when the user explicitly requests them.
