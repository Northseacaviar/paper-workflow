# -*- coding: utf-8 -*-
"""从标色流复算检测报告里的全部数字，并做块级置换检验。

输入：reconstruct_markup.py 产出的 labeled_lines.jsonl
输出：data/fragments.csv  连续游程（= 报告片段）
      data/type_shares.csv 按文本类型的被标占比
      data/blocks.csv     块级特征表

用法
----
    python report_stats.py --data data/labeled_lines.jsonl
    python report_stats.py --data data/labeled_lines.jsonl --outdir data --iters 5000

要看的不是总分，是"同样长度、不同类型分别多少被计"，以及块级 7 个特征能不能分开
标红与未标。块级 p 显著而句级反号时，该特征方向不稳，任何对策都得降级为待验证。
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import re
import statistics as st
from collections import defaultdict
from pathlib import Path

NUMCHARS = re.compile(r"[\d.,%−+\-]")
ITEM_HEAD = re.compile(r"^[（(]?[一二三四五六七八九十0-9]+[）)、.]")
# 片段表、页眉、页码这类报告自身的排版件，一律不进统计
FURNITURE = re.compile(
    r"^(?:序\s*号|片段名称|字符数|AI\s*特征|篇名[:：].*|原文内容|片段指标列表|"
    r"注[:：]?|内容提要[:：]?|[—\-]\s*\d+\s*[—\-]|[0-9.]+%\(?\d*\)?)$"
)


def nonspace(s: str) -> int:
    return len(re.sub(r"\s", "", s))


def cjk_ratio(s: str) -> float:
    n = nonspace(s)
    return len(re.findall(r"[\u4e00-\u9fff]", s)) / max(n, 1)


def load(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.open(encoding="utf-8") if l.strip()]


def runs_of(lines: list[dict]) -> list[tuple[str, str]]:
    """连续同标签的字符游程。这就是报告里"片段"的生成方式。"""
    out: list[tuple[str, str]] = []
    cur: str = "."
    buf: list[str] = []
    for l in lines:
        for ch, lb in zip(l["text"], l["labels"]):
            if not ch.strip():
                continue
            if lb != cur:
                if buf:
                    out.append((cur, "".join(buf)))
                cur, buf = lb or ".", []
            buf.append(ch)
        # 换行算软分隔，不打断游程
    if buf:
        out.append((cur, "".join(buf)))
    return out


def type_shares(lines: list[dict]) -> dict[str, list[int]]:
    shares: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0])
    for l in lines:
        t = l["text"].strip()
        n = nonspace(t)
        if not n or FURNITURE.match(t):
            continue
        s = l["labels"].count("S")
        lat = sum(1 for c in t if c.isascii() and c.isalpha()) / n
        if lat > 0.5:
            key = "英文/参考文献"
        elif t.startswith(("注：", "注:")):
            key = "表注"
        elif len(NUMCHARS.findall(t)) / n > 0.75:
            key = "纯数字行"
        elif len(NUMCHARS.findall(t)) / n > 0.45:
            key = "表体/算式行"
        elif n < 25 and ITEM_HEAD.match(t):
            key = "小标题"
        else:
            key = "正文散文"
        a = shares[key]
        a[0] += n
        a[1] += s
        a[2] += 1
    return shares


def feats(t: str) -> dict[str, float]:
    n = nonspace(t)
    sent = [len(x) for x in re.split(r"[。！？；]", t) if len(x) > 4]
    return {
        "digit": 100 * len(re.findall(r"\d", t)) / n,
        "ordinal": 100 * len(re.findall(r"第[一二三四五六七八九十][，、]|其一|其二|首先|其次|最后|一是|二是", t)) / n,
        "paren": 100 * len(re.findall(r"[（(][^）)]*[）)]", t)) / n,
        "conn": 100 * len(re.findall(r"因此|然而|但是|而且|同时|此外|从而|由此", t)) / n,
        "hedge": 100 * len(re.findall(r"可能|或许|不能|无法|不足|难以|未必|并不", t)) / n,
        "meanlen": st.mean(sent) if sent else 0.0,
        "sdlen": st.pstdev(sent) if len(sent) > 1 else 0.0,
    }


def blocks_of(lines: list[dict]) -> list[dict]:
    """按"连续同标签"切块，块不跨页。阈值：>60% 字符标红算 S，0 算 N，中间算 M。"""
    blocks: list[dict] = []
    cur = None
    for l in lines:
        t = l["text"].strip()
        n = nonspace(t)
        if n < 12 or FURNITURE.match(t) or re.search(r"https?://|cx\.cnki", t):
            continue
        s = l["labels"].count("S")
        state = "S" if s / n > 0.6 else ("N" if s == 0 else "M")
        if cur is None or cur["state"] != state or cur["page"] != l["page"]:
            cur = {"state": state, "page": l["page"], "text": ""}
            blocks.append(cur)
        cur["text"] += t
    out = []
    for b in blocks:
        if nonspace(b["text"]) >= 40:
            b["n"] = nonspace(b["text"])
            b.update(feats(b["text"]))
            out.append(b)
    return out


def perm_test(a: list[float], b: list[float], iters: int, seed: int = 7) -> tuple[float, float, float]:
    obs = st.mean(a) - st.mean(b)
    pool = a + b
    rng = random.Random(seed)
    cnt = 0
    for _ in range(iters):
        rng.shuffle(pool)
        m = st.mean(pool[:len(a)]) - st.mean(pool[len(a):])
        if abs(m) >= abs(obs):
            cnt += 1
    return st.mean(a), st.mean(b), (cnt + 1) / (iters + 1)


def main() -> None:
    ap = argparse.ArgumentParser(description="复算检测报告的占比与块级特征")
    ap.add_argument("--data", type=Path, default=Path("data/labeled_lines.jsonl"))
    ap.add_argument("--outdir", type=Path, default=None)
    ap.add_argument("--iters", type=int, default=3000)
    args = ap.parse_args()

    out = args.outdir or args.data.parent
    out.mkdir(parents=True, exist_ok=True)
    lines = load(args.data)
    total = sum(nonspace(l["text"]) for l in lines)
    n_s = sum(l["labels"].count("S") for l in lines)
    n_q = sum(l["labels"].count("Q") for l in lines)
    print(f"lines={len(lines)} chars={total} S={n_s} Q={n_q} ratio={100 * n_s / total:.2f}%")

    # 1. 游程
    rows = []
    for lb, txt in runs_of(lines):
        n = nonspace(txt)
        if lb not in "SQ" or n < 20:
            continue                       # 版面上的 "9.1%" 小标签不是片段
        rows.append((len(rows) + 1, lb, n, re.sub(r"\s", "", txt)[:40]))
    with (out / "fragments.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["run", "label", "chars", "head"])
        w.writerows(rows)
    print(f"fragments>=20 chars: {len(rows)}  "
          f"len min/max={min(r[2] for r in rows)}/{max(r[2] for r in rows)}")

    # 2. 类型池
    shares = type_shares(lines)
    with (out / "type_shares.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["type", "chars", "marked_chars", "share", "lines"])
        for k, (n, s, c) in sorted(shares.items(), key=lambda kv: -kv[1][0]):
            w.writerow([k, n, s, f"{100 * s / max(n, 1):.1f}%", c])
    print("types:")
    for k, (n, s, _) in sorted(shares.items(), key=lambda kv: -kv[1][0]):
        print(f"  {k:8s} chars={n:6d} marked={100 * s / max(n, 1):5.1f}%")

    # 3. 块级
    blocks = blocks_of(lines)
    with (out / "blocks.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["page", "state", "chars", "digit", "ordinal", "paren", "conn",
                    "hedge", "meanlen", "sdlen", "head"])
        for b in blocks:
            w.writerow([b["page"], b["state"], b["n"]] +
                       [f"{b[k]:.2f}" for k in ("digit", "ordinal", "paren", "conn",
                                                "hedge", "meanlen", "sdlen")] +
                       [b["text"][:30]])

    prose = [b for b in blocks if cjk_ratio(b["text"]) > 0.65]
    S = [b for b in prose if b["state"] == "S"]
    N = [b for b in prose if b["state"] == "N"]
    print(f"blocks={len(blocks)} prose={len(prose)} (S={len(S)}, N={len(N)})")
    if len(S) >= 3 and len(N) >= 3:
        for k in ("digit", "ordinal", "paren", "conn", "hedge", "meanlen", "sdlen"):
            ms, mn, p = perm_test([b[k] for b in S], [b[k] for b in N], args.iters)
            flag = "  <-- 可区分" if p < 0.05 else ""
            print(f"  {k:8s} S={ms:6.2f} N={mn:6.2f} p={p:.3f}{flag}")
        print("块长 S:", sorted(b["n"] for b in S))
        print("块长 N:", sorted(b["n"] for b in N))
    else:
        print("未标或标红散文块太少，不做检验（检验力不足，置信度最多给'中'以下）")


if __name__ == "__main__":
    main()
