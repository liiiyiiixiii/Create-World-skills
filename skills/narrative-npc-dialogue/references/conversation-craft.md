# Human conversation craft

Read this reference for every dialogue generation, revision, or naturalness audit. The goal is not casual-sounding noise. The goal is performable speech shaped by character, relationship, pressure, and the current game moment.

## Priority

Apply this order when goals compete:

1. selected film continuity, game canon, timeline, and knowledge boundaries;
2. required gameplay transition and repository constraints;
3. character truth and relationship truth;
4. conversational naturalness and performability;
5. person-centered interest;
6. surface cleverness.

Never sacrifice the first four to make a line funnier. A grave scene may score well for interest through tension, vulnerability, reversal, or silence and contain no joke.

## Mandatory five-pass workflow

### 1. Strip out the transaction skeleton

Privately list only what must happen: request, refusal, fact, choice, reward, relationship change, state effect, and handoff to play. This is scaffolding, not dialogue. If the skeleton already reads like finished speech, the result will probably sound like a quest log or exposition report.

### 2. Build the conversation pressure map

For the scene and each participant, set:

- `surface_goal`: what they appear to want;
- `hidden_pressure`: what they fear, conceal, resent, or hope for;
- `relationship_temperature`: warmth, debt, rivalry, distrust, rank, dependence, or changing trust;
- `subtext`: what is negotiated without being said directly;
- `emotional_turn`: the smallest meaningful change by the end;
- `conversation_moves`: how each person tends to open, probe, evade, disagree, soften, joke, and leave;
- `forbidden_patterns`: wording, candor, eloquence, humor, or behavior that would betray the character;
- `interest_device`: at most one for a short exchange and two or three for a longer scene.

### 3. Draft multiple approaches internally

For anything longer than a single bark, draft two or three versions with different conversational engines, such as:

- direct pressure versus guarded indirection;
- an object or action as the entry point versus a verbal challenge;
- warmth hiding conflict versus friction hiding care.

Do not show all versions by default. Variety is for selection, not output inflation.

### 4. Select by behavior, not prettiness

Choose the version in which:

- speakers react to each other rather than recite adjacent monologues;
- the relationship affects phrasing and timing;
- information emerges under pressure;
- at least one turn changes expectation, status, emotion, or interpretation;
- the film character remains recognizable without borrowed lines.

### 5. Perform the oral and trimming pass

Read each line as speech. Shorten breathless clauses, remove written-language connectors, and let shared context stay implicit. Keep fragments only when the character and pressure justify them. Remove any line whose only purpose is repeating what the previous line already made clear.

## Conversation mechanisms

Use a small, purposeful subset rather than forcing all of them into every scene:

- **Adjacency:** answer, challenge, echo, reinterpret, or deliberately dodge the immediately previous turn.
- **Compression:** people omit subjects and facts both sides already know.
- **Asymmetry:** speakers differ in line length, certainty, directness, and emotional exposure.
- **Repair:** a speaker corrects, narrows, retracts, or restarts when pressure changes.
- **Interruption:** reserve it for urgency, hierarchy, intimacy, or avoidance; do not sprinkle dashes mechanically.
- **Strategic non-answer:** the evasion itself should reveal motive or power.
- **Echo:** repeat one loaded word to question or reframe it, not to summarize the whole statement.
- **Callback:** reuse a shared incident, object, debt, joke, or phrase in a new emotional context.
- **Action anchor:** let a prop, task, pause, or glance carry information that speech need not explain.
- **Status move:** command, permission, correction, teasing, deference, or refusal changes who controls the moment.

Natural speech is selective, not vague. Preserve exact facts when gameplay requires them, but distribute them through response and verification.

## Person-centered interest toolkit

Interest should arise from who is talking to whom now:

- status contrast or a brief status reversal;
- goals that almost align but not quite;
- understatement, over-literal interpretation, or restrained exaggeration appropriate to the character;
- affectionate irritation or familiarity earned by history;
- an object used differently by each character;
- strategic misunderstanding or pretending not to understand;
- a callback whose meaning has changed;
- dramatic irony between what the player knows and what the speakers know;
- a silence, refusal, or unexpectedly plain answer at the point where a speech is expected.

Do not turn every character into a quip machine. Avoid generic internet humor, reference jokes that violate period or setting, and punchlines that erase grief, fear, or danger the film treats seriously.

## Situation-specific anti-stiffness rules

### Evidence and clue dialogue

- Begin from what someone noticed, handled, heard, or fears—not an abstract conclusion.
- Let the listener question certainty, significance, or motive.
- Reveal one dense factual cluster per turn; exact lists belong in a document or UI when possible.
- Calibrate certainty in voice. A witness can remember, suspect, or misread; an object does not explain itself.
- Let the final meaning emerge through connection or decision, not a sentence announcing “this is evidence.”

Mechanical:

```text
A: I saw the warehouse light turn on three times after midnight.
B: This proves someone entered after the patrol passed.
```

More human:

```text
A: The warehouse was lit again last night.
B: Again?
A: Three times. Always after the patrol turned the corner.
B: Then nobody forgot the switch.
```

### Quest handoff

- Let the NPC present a problem, stake, limitation, debt, or bargain.
- Give the player a reason to care or a reason to resist.
- Stop before the NPC narrates every interaction step. Use the quest system for exact quantities, controls, and checklist order.
- After completion, react to how the situation changed; do not merely announce the reward.

### Villain, authority, and conspiracy dialogue

- Power often speaks through what does not need explanation.
- Prefer euphemism, institutional language, veiled threat, selective praise, a test of loyalty, or a command with an implied consequence.
- Give subordinates partial operational knowledge unless the story establishes intimacy or complicity.
- Reject scenes where a villain names the entire scheme, motive, vulnerability, and cover-up for the audience's convenience.

### Ambient dialogue

- Start from something physically or socially present: a broken tool, late meal, wet coat, familiar habit, rumor, shared debt, or local change.
- A two-line exchange still needs a relationship angle or small turn, not just question plus factual answer.
- Repeatable topics must survive repetition and current story state. Avoid facts that become absurd after later events.
- Ordinary talk may be unresolved. It does not need a conclusion or quest direction.

### High emotion

- People under fear, grief, shame, or shock often speak around the subject, repeat a small detail, become unusually plain, or stop early.
- Do not equate intensity with longer speeches, more exclamation marks, or more stage directions.
- Humor is optional and must be a known coping behavior, not an authorial escape hatch.

## AI-smoothness warning signs

Rewrite when several of these appear:

- every line is a complete, polished sentence of similar length;
- each speaker restates or summarizes the previous speaker;
- causal links are all explicit: “therefore,” “this means,” “so our next step is”;
- everyone is equally articulate and cooperative;
- greetings and polite acknowledgements consume lines without relationship value;
- tone is repeatedly described in parentheses instead of heard in the wording;
- ellipses, filler words, slang, or interruptions are added merely to look spontaneous;
- every scene contains a joke, metaphor, or inspirational final line;
- an NPC recites exact quest instructions that the UI already shows;
- a villain conveniently confesses the whole plan;
- the last line repeats the objective instead of changing control, feeling, or expectation.

## Internal six-factor rubric

Score each candidate privately from 1–5. Do not show scores unless asked.

| Factor | A strong result |
|---|---|
| Naturalness | Turns connect, shared context is compressed, and imperfections are motivated |
| Character distinction | Names can be removed and voices still differ through choices and moves |
| Interest | Contains a relationship reveal, micro-reversal, tension, memorable image, or earned humor |
| Film fidelity | Matches the selected version's behavior, period, relationships, and knowledge |
| Game function | Produces the required understanding, choice, state change, or handoff |
| Performability | Can be spoken and staged cleanly within the presentation budget |

Reject a candidate below 4 in film fidelity, game function, naturalness, or performability. Interest may be 3 in deliberately austere scenes when tension or emotional truth carries the moment. Never average away a canon, knowledge, or state failure.

## Final checks

- Does every non-deliberate reply connect to what was just said or done?
- Does each speaker want something beyond delivering information?
- Is at least one line shaped by this specific relationship rather than generic personality?
- Is there a small turn in status, interpretation, emotion, or expectation?
- Could animation or a prop replace any explanatory sentence?
- Would removing a line lose plot, pressure, relationship, atmosphere, or rhythm?
- Did forced wit, filler, or polished completeness sneak back in?
