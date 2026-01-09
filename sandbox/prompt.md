# Task: Implement Player Archetypes

I want you to implement typical poker player archetypes under `src/maverick/players/`. Each player implementation should encapsulate a typical behavioral pattern.

- Each implementation should be in a separate python module in `src/maverick/players/`, imported in `src/maverick/players/__init__.py`. You can take `src/maverick/players/foldbot.py` as a template.
- Each implemented class should have NumPy-style docstring, that explains the strategy of the player.

---

## Fundamental Play-Style Archetypes

### Tight-Aggressive (TAG)

- **Description:** Selective with starting hands, but bets and raises assertively when involved.
- **Key Traits:** Discipline, strong value betting, positional awareness.
- **Strengths:** Consistently profitable, difficult to exploit.
- **Weaknesses:** Can become predictable if overly rigid.
- **Common At:** Winning regulars in cash games and tournaments.

---

### Loose-Aggressive (LAG)

- **Description:** Plays a wide range of hands and applies relentless pressure.
- **Key Traits:** Frequent raises, bluffs, creative lines.
- **Strengths:** Forces opponents into mistakes, dominates passive tables.
- **Weaknesses:** High variance, vulnerable to strong counter-strategies.
- **Common At:** Higher-stakes games, experienced online players.

---

### Tight-Passive (Rock / Nit)

- **Description:** Plays very few hands and avoids big pots without premium holdings.
- **Key Traits:** Folding, calling instead of raising.
- **Strengths:** Minimizes losses.
- **Weaknesses:** Misses value, extremely readable.
- **Common At:** Low-stakes live games.

---

### Loose-Passive (Calling Station)

- **Description:** Plays too many hands and calls too often.
- **Key Traits:** Limping, calling with weak or marginal hands.
- **Strengths:** Pays off strong hands.
- **Weaknesses:** Long-term losing style.
- **Common At:** Casual home games and low-stakes casinos.

---

## Psychological & Table-Dynamic Archetypes

### Maniac

- **Description:** Ultra-aggressive and unpredictable.
- **Key Traits:** Constant betting and raising, massive bluffs.
- **Strengths:** Creates confusion and short-term chaos.
- **Weaknesses:** Burns chips rapidly over time.
- **Common At:** Short bursts in live and online play.

---

### Tilted Player

- **Description:** Emotionally compromised after losses or bad beats.
- **Key Traits:** Revenge plays, poor decision-making.
- **Strengths:** None while tilted.
- **Weaknesses:** Severe strategic leaks.
- **Common At:** All stakes, especially after big pots.

---

### Bully

- **Description:** Uses stack size and intimidation to control the table.
- **Key Traits:** Overbets, fast actions, pressure plays.
- **Strengths:** Exploits fearful or inexperienced opponents.
- **Weaknesses:** Overplays weak holdings.
- **Common At:** Deep-stack live games.

---

## Skill-Based / Modern Archetypes

### Grinder

- **Description:** Volume-oriented player focused on steady expected value.
- **Key Traits:** Multitabling, consistent lines, bankroll discipline.
- **Strengths:** Reliable long-term profits.
- **Weaknesses:** Predictability, limited creativity.
- **Common At:** Online cash games.

---

### GTO-Oriented Player

- **Description:** Strategy driven by game-theory optimal solutions.
- **Key Traits:** Balanced ranges, mixed strategies.
- **Strengths:** Extremely difficult to exploit.
- **Weaknesses:** May underperform in soft, highly exploitative games.
- **Common At:** Mid-to-high stakes online.

---

### Exploitative Player (Shark)

- **Description:** Adapts strategy dynamically based on opponent tendencies.
- **Key Traits:** Strong reads, targeted adjustments.
- **Strengths:** Maximizes profit against weak players.
- **Weaknesses:** Requires constant attention and accurate reads.
- **Common At:** Live games and mixed-skill environments.

---

## Informal & Recreational Archetypes

### Fish (Fish Player)

- **Description:** A generally weak or inexperienced player who makes
  systematic, exploitable mistakes.
- **Key Traits:** Plays too many hands, poor position awareness,
  excessive calling, inconsistent bet sizing.
- **Strengths:** Unpredictable in the short term.
- **Weaknesses:** Negative expected value over time.
- **Common Variants:**
  - Loose-Passive Fish (calling station)
  - Loose-Aggressive Fish (erratic bluffer)
  - Short-Stack Fish (commits incorrectly)
- **Typical Thought:** *“Maybe this will work.”*
- **Common At:** Low-stakes online games, casual live games.

---

### ABC Player

- Straightforward, textbook poker with little deviation.

### Hero Caller

- Calls big bets to “keep opponents honest,” often incorrectly.

### Scared Money

- Plays too cautiously due to being under-rolled for the stakes.

### Whale

- Extremely loose player willing to gamble large sums.

---
