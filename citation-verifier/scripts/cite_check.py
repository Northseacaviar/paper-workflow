# -*- coding: utf-8 -*-
"""中文/英文混排稿件的引用对账与元数据核验。

两件事：
1) 正文引用 ↔ 参考文献双向对账（纯文本，不需要网络）。
   抓“作者+年份”两种写法：中文「李常青等，2010」、英文「Romer and Romer (2023)」。
2) 英文条目逐条查 Crossref，比对年份、卷、期、页码（可选，需联网）。

用法：
    python cite_check.py 稿件.md                 # 只做对账
    python cite_check.py 稿件.md --crossref      # 对账 + Crossref 核验
    python cite_check.py 稿件.md --crossref --output 报告.md
退出码：0 全通过；1 有问题；2 输入/依赖错误。
"""
import argparse
import json
import re
import sys
import urllib.parse
import urllib.request

REF_RANGE = None
CJK = re.compile(r"[\u4e00-\u9fa5]")
YEAR = r"(?:19|20)\d{2}"

# 正文里的中文引用：张三等，2010 / 张三、李四，2010 / 张三（2010）
RE_CN_CITE = re.compile(r"([\u4e00-\u9fa5]{2,4})(?:等|、[\u4e00-\u9fa5]{2,4})?\s*[，,（(]\s*(" + YEAR + r")")
# 正文里的英文引用：Romer and Romer (2023) / Mian and Sufi 2009
RE_EN_CITE = re.compile(
    r"([A-Z][A-Za-z\-]+(?:\s+(?:and|&)\s+[A-Z][A-Za-z\-]+)?)\s*[，,]?\s*[（(]?\s*(" + YEAR + r")")


def load_section(md, heading_pat=r"^##\s*参考文献|^##\s*References", end_pat=r"^##\s"):
    lines = md.splitlines()
    start = None
    for i, ln in enumerate(lines):
        if re.match(heading_pat, ln.strip(), re.I):
            start = i + 1
            break
    if start is None:
        return None, lines
    end = len(lines)
    for j in range(start, len(lines)):
        if re.match(end_pat, lines[j].strip()) and lines[j].strip():
            end = j
            break
    return "\n".join(lines[start:end]), lines


def split_entries(reftext):
    parts, buf = [], []
    for ln in reftext.splitlines():
        if ln.strip():
            buf.append(ln.strip())
        elif buf:
            parts.append(" ".join(buf))
            buf = []
    if buf:
        parts.append(" ".join(buf))
    return [p for p in parts if len(p) > 10]


def cn_key(entry):
    m = re.match(r"([\u4e00-\u9fa5]{2,4})", entry)
    y = re.search(YEAR, entry)
    if m and y:
        return (m.group(1), y.group(0))
    return None


def en_key(entry):
    m = re.match(r"([A-Z][A-Za-z\-]+)", entry)
    y = re.search(YEAR, entry)
    if m and y:
        return (m.group(1), y.group(0))
    return None


def parse_en(entry):
    """粗解析英文条目：作者、年份、题名、期刊、卷(期): 页。"""
    year = re.search(YEAR, entry)
    vol_issue_pages = re.search(r"(\d+)\s*(?:\((\d+)\))?\s*[:：]\s*(\d+)\s*[-–—]\s*(\d+)", entry)
    doi = re.search(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", entry)
    return {
        "raw": entry,
        "year": year.group(0) if year else None,
        "volume": vol_issue_pages.group(1) if vol_issue_pages else None,
        "issue": vol_issue_pages.group(2) if vol_issue_pages else None,
        "pages": (vol_issue_pages.group(3), vol_issue_pages.group(4)) if vol_issue_pages else None,
        "doi": doi.group(0) if doi else None,
    }


def crossref_lookup(surname, year, title_guess):
    q = {"query.bibliographic": f"{surname} {year} {title_guess}".strip(), "rows": 3}
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(q)
    req = urllib.request.Request(url, headers={"User-Agent": "cite-check/1.0 (mailto:1986912185@qq.com)"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.loads(r.read())
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}
    items = (data.get("message") or {}).get("items") or []
    return {"items": items[:3]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--crossref", action="store_true", help="对英文条目查 Crossref")
    ap.add_argument("--output")
    a = ap.parse_args()

    try:
        md = open(a.input, encoding="utf-8").read()
    except Exception as e:
        print(f"读文件失败：{e}")
        return 2

    reftext, all_lines = load_section(md)
    if reftext is None:
        print("没找到「## 参考文献」或「## References」小节")
        return 2

    lines_all = md.splitlines()
    a0, a1 = REF_RANGE if REF_RANGE else (0, 0)
    body = "\n".join(lines_all[:a0] + lines_all[a1:])
    entries = split_entries(reftext)
    ref_cn = {cn_key(e) for e in entries if cn_key(e)}
    ref_en = {en_key(e) for e in entries if en_key(e)}

    cited_cn = set()
    for m in RE_CN_CITE.finditer(body):
        prev = body[m.start() - 1] if m.start() > 0 else ""
        if prev and (CJK.match(prev) or prev in "、·/"):
            continue          # 位于「魏志华、李茂良」这类序列中段，不是第一作者
        cited_cn.add((m.group(1), m.group(2)))
    cited_en = set()
    for m in RE_EN_CITE.finditer(body):
        pre = body[max(0, m.start() - 6):m.start()]
        if pre.rstrip().endswith(("&", "＆", "and", "、")):
            continue          # 合著里的第二作者，不算独立引用
        cited_en.add((m.group(1).split()[0], m.group(2)))
    STOP_EN = {"january","february","march","april","may","june","july","august",
               "september","october","november","december","fy","in","the","by","see",
               "table","figure","figure","panel","data","source","note","section",
               "appendix","china","chinese","journal","review","working","paper"}
    cited_en = {k for k in cited_en if len(k[0]) >= 4 and k[0].lower() not in STOP_EN}
    STOP = {"口径", "交易", "个交", "重叠", "计算", "最大", "高度", "逐项", "与郑", "中郑", "和肖", "是卿", "三年"}
    cited_cn = {k for k in cited_cn if not any(w in k[0] for w in STOP)}

    out = []
    out.append("# 引用对账报告\n")
    out.append(f"- 参考文献条目：{len(entries)}（中文类 {len(ref_cn)}，英文类 {len(ref_en)}）")
    out.append(f"- 正文中文引用：{len(cited_cn)} 组；英文引用：{len(cited_en)} 组\n")

    def cn_match(a, b):
        """同名或前缀互含（组织名长短不一）。"""
        return a == b or a.startswith(b) or b.startswith(a)

    def in_refs_cn(name, year):
        return any(y == year and cn_match(n, name) for n, y in ref_cn)

    def in_cited_cn(name, year):
        return any(y == year and cn_match(n, name) for n, y in cited_cn)

    def in_refs_en(surname, year):
        return any(y == year and s == surname for s, y in ref_en)

    def in_cited_en(surname, year):
        return any(y == year and s == surname for s, y in cited_en)

    miss_in_refs = sorted(x for x in cited_cn if not in_refs_cn(*x))
    unused_cn = sorted(x for x in ref_cn if not in_cited_cn(*x))
    miss_en = sorted(x for x in cited_en if not in_refs_en(*x))
    unused_en = sorted(x for x in ref_en if not in_cited_en(*x))

    out.append("## 正文引了、参考文献里没有\n")
    out.append("（这类要么补文献，要么删引用）\n")
    for x in miss_in_refs:
        out.append(f"- 中文：{x[0]}，{x[1]}")
    for x in miss_en:
        out.append(f"- 英文：{x[0]} ({x[1]})")
    if not (miss_in_refs or miss_en):
        out.append("- 无")
    out.append("")

    out.append("## 参考文献里有、正文未见引用\n")
    out.append("（分两档：正文完全没出现 → 必删或补引；正文出现该年份或相近名称 → 人工确认）\n")
    for tag, items in (("中文", unused_cn), ("英文", unused_en)):
        for x in items:
            name, year = x
            alias = name[:3] if len(name) >= 4 else name
            if name in body:
                verdict = "已引用（形态与正则不同，人工看一眼）"
            elif alias in body:
                verdict = "待确认（正文出现相近名称）"
            elif year in body:
                verdict = "待确认（正文出现该年份）"
            else:
                verdict = "正文完全未提及 → 补引或删除"
            out.append(f"- {tag}：{name}，{year} —— {verdict}")
    if not (unused_cn or unused_en):
        out.append("- 无")
    out.append("")

    bad = []

    if a.crossref:
        out.append("## Crossref 元数据核验（英文条目）\n")
        out.append("| 条目 | 本地年份 | Crossref 年份 | 卷(期): 页 | 判定 |")
        out.append("|---|---|---|---|---|")
        for e in entries:
            k = en_key(e)
            if not k or CJK.search(e[:20]):
                continue
            info = parse_en(e)
            title_guess = " ".join(re.findall(r"[A-Za-z]{4,}", e)[2:12])[:120]
            res = crossref_lookup(k[0], k[1], title_guess)
            if "error" in res:
                out.append(f"| {e[:40]}… | {info['year']} | — | {info['volume']}({info['issue']}): {info['pages']} | 查询失败 |")
                continue
            items = res.get("items") or []
            if not items:
                bad.append(e)
                out.append(f"| {e[:40]}… | {info['year']} | — | — | 查不到 |")
                continue
            it = items[0]
            cr_year = (it.get("issued", {}).get("date-parts") or [[None]])[0][0]
            cr_vol = it.get("volume")
            cr_issue = it.get("issue")
            cr_page = it.get("page")
            ok = str(cr_year) == str(info["year"])
            verdict = "✓" if ok else f"✗ 年份应为 {cr_year}"
            if ok and info["volume"] and cr_vol and str(cr_vol) != str(info["volume"]):
                verdict += f"；卷应为 {cr_vol}"
                ok = False
            if ok and info["pages"] and cr_page:
                local = f"{info['pages'][0]}-{info['pages'][1]}"
                if local.replace("–", "-") not in str(cr_page).replace("–", "-"):
                    verdict += f"；页应为 {cr_page}"
                    ok = False
            if not ok:
                bad.append(e)
            out.append(f"| {e[:42]}… | {info['year']} | {cr_year} | {cr_vol}({cr_issue}): {cr_page} | {verdict} |")
        out.append("")

    report = "\n".join(out)
    if a.output:
        open(a.output, "w", encoding="utf-8").write(report)
        print("报告已写入", a.output)
    print(report if len(report) < 4000 else report[:3000] + "\n…（完整报告见输出文件）")

    problems = bool(miss_in_refs or miss_en or unused_cn or unused_en or bad)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
