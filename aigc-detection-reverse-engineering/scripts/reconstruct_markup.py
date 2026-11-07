# -*- coding: utf-8 -*-
"""重建 AIGC 检测报告 PDF 的字符级标色流。

检测报告把"显著"印成红、"疑似"印成橙、"未标识"印成深灰。这类 PDF 的字体通常没有
CMap，pdftotext 只能抽出数字与拉丁字母，中文全丢，所以必须读 span 的 color 字段。

用法
----
    python reconstruct_markup.py 报告.pdf --colors          # 先打调色板直方图
    python reconstruct_markup.py 报告.pdf -o data/labeled_lines.jsonl
    python reconstruct_markup.py 报告.pdf --map 404040=. E60111=S D99E4C=Q
    python reconstruct_markup.py 报告.pdf --left 0 --max-size 100

输出
----
每行 {"page":1,"x":183.0,"text":"...","labels":"SSS.."}，labels 与 text 等长：
S=显著（计入分子）、Q=疑似（进分母不计分子）、.=未标识。

脚本结尾会把显著字符数与占比打出来，与报告首页的"AI 特征值"核对；再列最长的几个
游程，用于和报告的片段表核对。两处都对上，才继续往下算。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

try:
    import pymupdf
except ImportError:  # pragma: no cover
    sys.exit("需要 PyMuPDF：pip install pymupdf")

# 知网个人 AIGC 检测（2026-11 版）的调色板。换厂商或换版本先用 --colors 重看。
DEFAULT_MAP = {0x404040: ".", 0xE60111: "S", 0xD99E4C: "Q"}

FURNITURE = re.compile(
    r"^(?:cx\.cnki\.net|知网个人AIGC|原文内容|片段指标列表|篇名[:：].*|"
    r"[—\-]\s*\d+\s*[—\-]|\d+\.\s*监管信号.*|[0-9.]+%\(?\d*\)?)$"
)


def parse_map(items: list[str] | None) -> dict[int, str]:
    if not items:
        return dict(DEFAULT_MAP)
    out: dict[int, str] = {}
    for it in items:
        if "=" not in it:
            sys.exit(f"--map 需要 KEY=LABEL 形式，收到 {it!r}")
        key, label = it.split("=", 1)
        key = key.lower().removeprefix("0x").removeprefix("#")
        if label not in (".", "S", "Q", "N"):
            sys.exit("--map 的标签只能是 . / S / Q / N")
        out[int(key, 16)] = label
    return out


def palette(pdf: Path) -> None:
    """打印每页 span 的颜色直方图，用来定 --map。"""
    doc = pymupdf.open(pdf)
    counter: Counter[int] = Counter()
    for page in doc:
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    if span["text"].strip():
                        counter[span["color"]] += len(span["text"])
    total = sum(counter.values()) or 1
    print(f"{'color':>8}  {'hex':>8}  {'chars':>8}  share")
    for color, n in counter.most_common(12):
        print(f"{color:>8}  #{color:06X}  {n:>8}  {100 * n / total:5.1f}%")


def main() -> None:
    ap = argparse.ArgumentParser(description="重建检测报告 PDF 的字符级标色流")
    ap.add_argument("pdf", type=Path)
    ap.add_argument("-o", "--out", type=Path, default=Path("data/labeled_lines.jsonl"))
    ap.add_argument("--map", nargs="*", help="color=LABEL，十六进制，可给多个")
    ap.add_argument("--colors", action="store_true", help="只打调色板，不输出")
    ap.add_argument("--left", type=float, default=95.0, help="左栏竖排水印的 bbox 右边界")
    ap.add_argument("--max-size", type=float, default=20.0, help="超过此字号视为水印")
    args = ap.parse_args()

    if args.colors:
        palette(args.pdf)
        return

    color_map = parse_map(args.map)
    doc = pymupdf.open(args.pdf)
    args.out.parent.mkdir(parents=True, exist_ok=True)

    runs: list[tuple[str, str, int]] = []
    cur_label: str = "."
    cur_buf: list[str] = []
    n_lines = n_s = n_q = n_total = 0

    with args.out.open("w", encoding="utf-8") as fh:
        for pno, page in enumerate(doc, 1):
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    text = labels = ""
                    xs: list[float] = []
                    for span in line["spans"]:
                        s = span["text"]
                        if not s.strip() or span["size"] > args.max_size:
                            continue          # 水印
                        if span["bbox"][2] < args.left:
                            continue          # 左侧竖排栏
                        if FURNITURE.match(s.strip()):
                            continue          # 页眉页脚与片段表标签
                        text += s
                        labels += color_map.get(span["color"], ".") * len(s)
                        xs.append(span["bbox"][0])
                    if not text.strip():
                        continue
                    n_lines += 1
                    n_s += labels.count("S")
                    n_q += labels.count("Q")
                    n_total += len(re.sub(r"\s", "", text))
                    fh.write(json.dumps({"page": pno, "x": round(min(xs), 1),
                                         "text": text, "labels": labels},
                                        ensure_ascii=False) + "\n")

                    # 顺带收集连续游程，用于和片段表核对
                    for ch, lb in zip(text, labels):
                        if not ch.strip():
                            continue
                        if lb != cur_label:
                            if cur_buf:
                                runs.append((cur_label, "".join(cur_buf), len(cur_buf)))
                            cur_label, cur_buf = lb or ".", []
                        cur_buf.append(ch)
    if cur_buf:
        runs.append((cur_label, "".join(cur_buf), len(cur_buf)))

    print(f"lines={n_lines} chars={n_total} S={n_s} Q={n_q} "
          f"ratio={100 * n_s / max(n_total, 1):.2f}% -> {args.out}")
    print(f"runs>=100: {sum(1 for r in runs if r[0] in 'SQ' and r[2] >= 100)}")
    for lb, txt, n in sorted((r for r in runs if r[0] in "SQ"), key=lambda r: -r[2])[:8]:
        print(f"  {lb} {n:5d}  {txt[:36]}")
    print("核对：游程数与长度应与片段表一致；ratio 通常比首页 AI 特征值高 1~3 个点，")
    print("因为本流已剔除页眉页脚与空白。差 5 点以上才是颜色映射错了。")


if __name__ == "__main__":
    main()
