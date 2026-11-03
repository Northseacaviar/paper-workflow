---
name: text-provenance-verification
description: "Use when verifying a quote's source or exact wording."
version: 1.0.0
author: Northseacaviar
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Research, Quotations, Provenance, Text, Verification]
    category: research
    related_skills: [grounded-citations, arxiv, blocked-page-recovery]
---

# Text Provenance Verification

Class of task: someone hands you a passage and asks what it is or where it is
from; or your own draft quotes a literary, historical, philosophical, or legal
text and the attribution has to be right. Canonical public-domain texts are the
usual case.

## When to Use

- The user pastes a passage and asks what it is or where it is from.
- You are about to write a verbatim quote, or name the work a line comes from,
  in anything the user will read, keep, or forward.
- Two copies of the same text disagree, or the user asks which edition a text is.
- You need to decide whether a claim can be answered from knowledge at all, or
  has to be looked up — see the triage table at the end of this file.

Skip it for a paraphrase or a gist-level reference ("Burke argued against
abstract rights"): that needs no fetch. It applies the moment wording,
attribution, or edition is load-bearing.

## Rules

- Model knowledge is reliable at the **gist** level and unreliable at the
  **verbatim + attribution** level. State the gist freely; never emit a verbatim
  quote or a work-level attribution you have not fetched.
- The characteristic failure is not nonsense — it is *plausible*: the author's
  most famous work, the best-known wording of the claim. Assume that bias in your
  own first guess, and search anyway.
- Report provenance at a level the user can re-check themselves: work title,
  volume/edition, and the character offset of the hit. "I looked it up" is not
  provenance.
- Never silently promote similarity into identity. Say which of the two you
  actually established: same text in different typography, or a genuinely
  different version.
- A quote with uncertain attribution is worse than no quote. If the corpus
  returns nothing, report that — do not fall back to the plausible guess.

## Procedure

① **Extract a fossil phrase.** Pick the most distinctive 3–6 word sequence —
archaic diction, an unusual collocation, a name plus verb phrase. Never search a
paraphrase; the whole point is to match literal text.

② **Exact-phrase search leads, corpus grep proves.** Quote the phrase in a
`web_search`. Anthology, quotation, and study-guide pages usually surface the
work name — treat that as a *lead only*, because such a page may label the page
or a section rather than the passage. Then confirm against complete primary text
(see `references/text-corpora.md`): download the candidate volumes and grep each
one. Report hit counts per volume — zero hits in a volume is real information,
because it eliminates the work you would have guessed.

③ **Name the enclosing work.** Walk backwards from the hit to the nearest
all-caps heading line; that is the work title. Record the character offset for
the report.

④ **Characterize the edition** when the user's copy and the corpus copy are not
byte-identical. Normalize both (lowercase, strip punctuation, collapse
whitespace) and run `difflib.SequenceMatcher` with `get_opcodes()`:

- `ratio() == 1.0`, equal word counts, punctuation-only differences → the same
  text in a different typographic edition. Say exactly that; do not dress it up
  as a correction or a variant reading.
- Word-level differences → a genuinely different version. List them as
  `corpus[x] -> source[y]` pairs.

⑤ **Report the check honestly.** Once retrieval has put the answer into your
context you can no longer demonstrate what you knew — memory is untestable after
contamination. Say what you *would* have answered unaided and why that guess is
the trap, then give the verified result with its provenance. That contrast is the
entire value of the exercise; claiming you "already knew" destroys it.

## Presentation

Show the evidence chain (phrase search → volume → character offset) and the
word-level diff, not just the conclusion — the user's trust comes from being able
to re-run the check. Keep the conclusion first, then the chain.

## Knowledge-boundary triage

Decide per claim which route applies:

| Kind of knowledge | Route |
|---|---|
| In training data, needed at gist level (canonical works, concepts, syntax) | Answer directly; retrieval adds noise |
| Private and small (preferences, project conventions, standing rules) | Always-loaded context (memory / skills) |
| Private and large (note vaults, codebase, transcripts) | Real RAG: chunk → embed → retrieve → generate |
| Public but fresh or long-tail (news, new papers, one doc page) | Live retrieval; do not build an index |

The criterion is never "public vs private" — it is "does the model hold it
*accurately* enough, and how precise must the output be". Exact figures, dates,
proper names, verbatim wording, and current state always go through retrieval.
