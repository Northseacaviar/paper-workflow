---
name: citation-verifier
description: Use when checking manuscript citations, bibliography hygiene, DOI or PMID completeness, placeholder references, or BibTeX consistency before submission or revision.
---

# Citation Verifier

## Overview

Use this skill when citation integrity is the bottleneck. It is narrower and more operational than general writing skills: the goal is to catch unverifiable references, missing identifiers, duplicated BibTeX keys, placeholder citations, and mismatches between local citation artifacts before they become submission problems.

Use this skill together with `scientific-writing` or `submission-audit`, not instead of them.

This is stage one of three. It shows the bibliography is well-formed; it cannot show that the
cited papers are real, and it cannot show that a real paper supports the sentence citing it.
Hand the surviving entries to `reference-audit-guide` (optional set, installed with `--set all`),
which queries CrossRef, Semantic Scholar, arXiv, and PubMed to confirm existence and match
metadata, then to `claim-source-verification` for claim-to-evidence support. When
`reference-audit-guide` is not installed, say that existence was not machine-verified rather than
letting a clean local scan stand in for it. A fabricated citation carrying a well-formed DOI passes this skill
and fails the next one.

## When To Use

Use this skill when:
- a manuscript is close to submission or resubmission
- the bibliography may contain placeholders, guessed entries, or stale metadata
- a `.bib` file needs a hygiene pass
- the draft mixes DOI, arXiv, PMID, or plain-text references inconsistently
- you need to verify that local citation artifacts are ready before manual or online source verification

Do not use this skill for:
- generic literature discovery from scratch
- full manuscript restructuring
- venue formatting that does not depend on citation integrity

## Local First Pass

Start with a local citation scan before any online verification.

The helper script:

```bash
python ~/.agents/skills/citation-verifier/scripts/scan_citations.py path/to/file_or_dir [...]
# Claude Code (global install): replace ~/.agents/skills with ~/.claude/skills
# Claude Code (project-local install): replace ~/.agents/skills with .claude/skills
```

Use it to find:
- `[CITATION NEEDED]` or similar placeholders
- `PLACEHOLDER_...` citation keys
- `TODO: verify` markers
- DOI, arXiv, and PMID tokens
- LaTeX `\cite{...}` keys
- duplicate BibTeX keys inside `.bib` files

Treat imported BibTeX and Google Scholar-style exports as draft metadata, not as verified truth.

## Verification Order

1. Scan the local draft and bibliography artifacts.
2. Remove or flag all placeholder citations.
3. Check BibTeX-key uniqueness and obvious identifier gaps.
4. Normalize metadata fields that are commonly wrong in copied BibTeX:
   - author list and spelling
   - year
   - venue or journal name
   - volume, issue, pages, or article number
   - DOI versus preprint identifier
5. For every citation that matters to a scientific claim, verify the paper exists in trusted sources.
6. If a claim depends on a specific result, confirm the cited paper actually supports that claim. For a systematic pass over many such claims, hand off to `claim-source-verification`: existence and metadata checks do not catch a real paper made to carry a conclusion it does not reach.
7. Only then finalize formatting for the venue.

## Severity Grading

When you report field-level mismatches, grade each one so authors fix the dangerous ones first:

- **Critical (must fix)**: wrong or fabricated first author, reversed author order, a DOI that resolves to a different paper, a title whose core terms do not match, or a page range off by five or more.
- **Warning (verify)**: volume-year inconsistent with the DOI-registration year, a missing or extra issue number, a missing middle initial, a page range off by one to four, or an ambiguous publisher-name variant.
- **Info (note only)**: title case versus sentence case, abbreviated versus full journal name, and punctuation or conjunction differences (`and` versus `&`).

Two checks are easy to miss and worth running explicitly:
- **Volume-year versus DOI-year**: a citation whose stated volume-year differs from the year encoded in the DOI or the online-publication date is a common sign of a miscopied entry.
- **Author-order reversal**: verify the first author specifically, not just that all names are present; a reversed or shifted author list still passes a set-membership check.

Roll each reference up to one confidence verdict: `verified`, `check_suggested` (has a Warning), `needs_fix` (has a Critical), or `unverifiable` (no source could confirm it).

## Trusted Verification Sources

Prefer this order when moving beyond local scans:
- publisher page or DOI resolver
- PubMed for biomedical papers
- arXiv for preprints
- Crossref or Semantic Scholar for metadata cross-checking
- Google Scholar only as a fallback discovery aid, not as the sole source of truth

## Common Failure Modes

- writing BibTeX from memory
- leaving placeholder citation keys in the draft
- assuming an arXiv preprint and published version are interchangeable
- citing a paper correctly but using it to support a claim it does not make
- letting duplicate BibTeX keys silently overwrite entries
- blindly trusting copied Scholar or BibTeX metadata for venue names, pages, years, or DOI fields

## Output Standard

When using this skill, report:
- placeholder or unverifiable items
- duplicate or suspicious BibTeX keys
- missing or inconsistent DOI/arXiv/PMID information
- suspicious metadata fields that need manual correction
- claims that still need source verification
- the minimum safe next step before submission

## 中文/英文混排稿件的对账脚本（`scripts/cite_check.py`）

面向 .md 稿件的实测脚本，补上前面几个脚本只吃 .bib/.tex 的缺口。两件事：

1. **双向对账（离线）**：把「## 参考文献」小节切出来，其余当正文；正文抓两种引用写法——中文「魏志华、李茂良，2014」「李常青等（2010）」、英文「MacKinlay，1997」「Barberis & Shleifer（2003）」——与文献条目互查，输出「正文引了但列表没有」「列表有但正文没引」两栏。
2. **Crossref 元数据核验（可选 `--crossref`）**：对英文条目按作者姓+年份+题名做检索，比对年份、卷、期、页码，给出 ✓ / ✗（附正确值）。

```bash
python cite_check.py 稿件.md                        # 只对账
python cite_check.py 稿件.md --crossref --output 报告.md
```

退出码：0 全通过，1 有问题，2 输入错误——可以直接挂在投稿前的门禁里。

**实测记录与已知局限**（2026-11，国九条稿 21 条文献、14 组引用）：

- 注入式验证通过：正文改成「（MacKinlay，1999）」「（Fake，2099）」后，两条都被抓出；干净稿的两栏均为空。
- **多作者英文引用会出假阳性**：`Barberis、Shleifer，2003` 这种中文式多人并列，第二、三作者会被当成独立引用报出来（Shleifer、Vishny、Modigliani）。报告里这类要人眼扫一遍，别直接按它删引用。
- 中文机构作者（中国证监会/上海证券交易所）在正文常写作简称，会落在「正文未见引用」栏，属于命名差异，不是漏引。
- 只适用于「作者-年份」制；数字脚注制（如 Chicago note style）需要另行改写解析。

**在流程里的位置**：这个脚本属于第 1 步（书目形态与引证一致性），不判断文献是否存在、更不判断文献是否支持你的句子——那两步仍是 `reference-audit-guide` 与 `claim-source-verification`。
