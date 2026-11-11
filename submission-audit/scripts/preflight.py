# -*- coding: utf-8 -*-
"""投稿前确定性预检：把几项能机器判的检查汇总成一个裁决（PASS / WARN / BLOCK）。

检查项（都是确定性的，不调用模型）：
1. 引用对账：调用 citation-verifier/scripts/cite_check.py，看两栏是否为空。
2. 图表引用：正文引用「表 N / 图 N / Table N / Figure N」但文档里找不到对应题注 → WARN。
3. 占位符与临期词：TODO / TBD / XXX / 「待补」「待核」→ WARN。
4. 摘要数字：摘要里出现的数字，正文是否至少出现一次 → WARN（防摘要与正文脱节）。
5. 段落重复：连续 200 字以上完全重复的段落 → BLOCK（复制粘贴事故）。

用法：
    python preflight.py 稿件.md [--skip-cite]
退出码：0 PASS，1 WARN，2 BLOCK，3 输入错误。
"""
import argparse
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CITE = os.path.join(HERE, "..", "..", "citation-verifier", "scripts", "cite_check.py")


def load(path):
    return open(path, encoding="utf-8").read()


def split_abstract(md):
    m = re.search(r"^#+\s*(摘要|Abstract|内容提要)\s*[:：]?\s*$", md, re.M)
    if not m:
        m = re.search(r"^\*\*(摘要|内容提要)[:：]?\*\*", md, re.M)
    if not m:
        return ""
    rest = md[m.end():]
    nxt = re.search(r"^#+\s", rest, re.M)
    return rest[:nxt.start()] if nxt else rest


def body_without_refs(md):
    m = re.search(r"^#+\s*(参考文献|References)\s*$", md, re.M | re.I)
    return md[:m.start()] if m else md


def check_citations(path):
    if not os.path.exists(CITE):
        return "WARN", "找不到 cite_check.py，引用对账未跑"
    r = subprocess.run([sys.executable, CITE, path], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    out = r.stdout or ""
    miss = re.search(r"##\s*正文引了、参考文献里没有\s*\n+[^\n]*\n+([\s\S]*?)\n##", out)
    unused = re.search(r"##\s*参考文献里有、正文未见引用\s*\n+[^\n]*\n+([\s\S]*?)(?:\n## |\Z)", out)
    def count(block, strict):
        if not block:
            return 0
        n = 0
        for l in block.group(1).splitlines():
            t = l.strip()
            if not t.startswith("- ") or t.endswith("无"):
                continue
            if strict:
                if ("需补或删" in t) or ("正文完全未提及" in t):
                    n += 1
            else:
                n += 1
        return n
    n1, n2 = count(miss, True), count(unused, True)
    if n1 == 0 and n2 == 0:
        return "PASS", "对账通过（无「需补或删」「正文完全未提及」条目）"
    return "BLOCK" if n1 else "WARN", f"引用对账：正文缺文献 {n1} 条，文献未被引用 {n2} 条"


def check_figrefs(md):
    body = body_without_refs(md)
    cited = set(re.findall(r"(?:表|图|Table|Figure)\s*(\d+)", body))
    norm = "\n".join(re.sub(r"^\s*\*\*|\*\*\s*$", "", ln) for ln in body.splitlines())
    captions = set(re.findall(r"^\s*(?:表|图|Table|Figure)\s*(\d+)[　 :：]", norm, re.M))
    missing = sorted(cited - captions, key=lambda x: int(x))
    if missing:
        return "WARN", f"正文引用了但找不到题注的编号：{', '.join(missing)}"
    return "PASS", "图表编号与题注对得上"


def check_placeholders(md):
    hits = []
    for pat in ("TODO", "TBD", "XXX", "待补", "待核", "FIXME"):
        n = len(re.findall(pat, md))
        if n:
            hits.append(f"{pat}×{n}")
    if hits:
        return "WARN", "占位符：" + "、".join(hits)
    return "PASS", "无占位符"


def check_abstract_numbers(md):
    ab = split_abstract(md)
    body = body_without_refs(md)
    if not ab:
        return "WARN", "没找到摘要小节，跳过数字核对"
    nums = set(re.findall(r"\d+(?:\.\d+)?%?", ab))
    nums = {n for n in nums if len(n) >= 2}
    absent = sorted(n for n in nums if n not in body)
    if absent:
        return "WARN", f"摘要里这些数字正文没出现：{', '.join(absent[:8])}"
    return "PASS", "摘要数字在正文都能找到"


def check_duplicate_paragraphs(md):
    paras = [p.strip() for p in re.split(r"\n\s*\n", body_without_refs(md))]
    seen = {}
    for p in paras:
        if len(p) >= 200:
            if p in seen:
                return "BLOCK", f"有整段重复（{len(p)} 字）：{p[:40]}…"
            seen[p] = 1
    return "PASS", "无整段重复"


CHECKS = [
    ("引用对账", "cite"),
    ("图表编号", "fig"),
    ("占位符", "ph"),
    ("摘要数字", "abs"),
    ("段落重复", "dup"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--skip-cite", action="store_true")
    ap.add_argument("--output")
    a = ap.parse_args()

    try:
        md = load(a.input)
    except Exception as e:
        print("读文件失败：", e)
        return 3

    results = []
    for name, key in CHECKS:
        if key == "cite":
            r = ("SKIP", "按要求跳过") if a.skip_cite else check_citations(a.input)
        elif key == "fig":
            r = check_figrefs(md)
        elif key == "ph":
            r = check_placeholders(md)
        elif key == "abs":
            r = check_abstract_numbers(md)
        else:
            r = check_duplicate_paragraphs(md)
        results.append((name, *r))

    verdict = "PASS"
    if any(r[1] == "BLOCK" for r in results):
        verdict = "BLOCK"
    elif any(r[1] == "WARN" for r in results):
        verdict = "WARN"

    lines = [f"# 投稿前预检：{os.path.basename(a.input)}", "", f"**裁决：{verdict}**", "",
             "| 检查项 | 结果 | 说明 |", "|---|---|---|"]
    for name, st, msg in results:
        lines.append(f"| {name} | {st} | {msg} |")
    lines += ["", f"由 `submission-audit/scripts/preflight.py` 生成（确定性检查，不含模型判断）。"]
    report = "\n".join(lines)

    if a.output:
        open(a.output, "w", encoding="utf-8").write(report)
        print("报告写入", a.output)
    print(report)

    return 0 if verdict == "PASS" else (2 if verdict == "BLOCK" else 1)


if __name__ == "__main__":
    sys.exit(main())
