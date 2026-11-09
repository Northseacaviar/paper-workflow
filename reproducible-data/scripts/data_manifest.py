#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成或校验项目的数据清单（manifest）。

用法：
    python data_manifest.py <项目目录>              # 生成/更新 manifest.json
    python data_manifest.py <项目目录> --verify      # 与已有 manifest 比对
    python data_manifest.py <项目目录> --layer raw   # 只处理某一层

扫描 data/raw、data/interim、data/final 三层，记录每个文件的
sha256、字节数、行数（csv/tsv/txt/json 才数）、修改时间。
校验模式只报告漂移，不写文件；有漂移时退出码为 1。

只用标准库。
"""
import csv
import hashlib
import io
import json
import os
import sys
import datetime as dt

LAYERS = ("raw", "interim", "final")
MANIFEST = "manifest.json"
COUNT_EXT = {".csv", ".tsv", ".txt"}


def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def count_rows(path):
    ext = os.path.splitext(path)[1].lower()
    if ext not in COUNT_EXT:
        return None
    try:
        with io.open(path, "r", encoding="utf-8-sig", errors="replace", newline="") as f:
            if ext == ".tsv":
                return sum(1 for _ in csv.reader(f, delimiter="\t")) - 1
            return sum(1 for _ in csv.reader(f)) - 1
    except Exception:
        # 编码不是 utf-8 时退回按行数
        try:
            with io.open(path, "r", encoding="gbk", errors="replace") as f:
                return sum(1 for _ in f) - 1
        except Exception:
            return None


def walk(root, layer):
    base = os.path.join(root, "data", layer)
    out = []
    if not os.path.isdir(base):
        return out
    for dirpath, _, files in os.walk(base):
        for name in sorted(files):
            p = os.path.join(dirpath, name)
            rel = os.path.relpath(p, root).replace("\\", "/")
            st = os.stat(p)
            out.append({
                "path": rel,
                "layer": layer,
                "bytes": st.st_size,
                "sha256": sha256(p),
                "rows": count_rows(p),
                "mtime": dt.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            })
    return out


def build(root, layers=LAYERS):
    files = []
    for layer in layers:
        files.extend(walk(root, layer))
    return {
        "project": os.path.abspath(root),
        "generated_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "files": files,
    }


def load(root):
    p = os.path.join(root, MANIFEST)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def verify(root, layers=LAYERS):
    old = load(root)
    if old is None:
        print("没有 manifest.json，请先不带 --verify 跑一次")
        return 2
    new = build(root, layers)
    oldmap = {f["path"]: f for f in old["files"]}
    newmap = {f["path"]: f for f in new["files"]}

    added = sorted(set(newmap) - set(oldmap))
    removed = sorted(set(oldmap) - set(newmap))
    changed = []
    for p in sorted(set(newmap) & set(oldmap)):
        a, b = oldmap[p], newmap[p]
        if a["sha256"] != b["sha256"]:
            changed.append((p, a, b))

    print(f"清单生成于 {old['generated_at']}，共 {len(oldmap)} 个文件")
    print(f"当前扫描 {len(newmap)} 个文件\n")
    if added:
        print(f"[新增] {len(added)}")
        for p in added:
            print("  +", p, f"({newmap[p]['bytes']} B)")
    if removed:
        print(f"[消失] {len(removed)}")
        for p in removed:
            print("  -", p)
    if changed:
        print(f"[内容变了] {len(changed)}")
        for p, a, b in changed:
            dr = ""
            if a["rows"] is not None and b["rows"] is not None and a["rows"] != b["rows"]:
                dr = f"，行数 {a['rows']} → {b['rows']}"
            print(f"  ! {p}{dr}")
            print(f"      {a['mtime']} → {b['mtime']}")
    if not (added or removed or changed):
        print("✓ 与清单一致，可复现")
        return 0
    print("\n漂移意味着：要么数据被改过，要么重建过程不确定，先查清楚再出表。")
    return 1


def normalize(path):
    """git-bash 风格路径转 Windows：/d/foo → D:/foo。"""
    if os.name == "nt" and len(path) > 2 and path[0] == "/" and path[2:3] == "/" and path[1].isalpha():
        return path[1].upper() + ":" + path[2:]
    return path


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    root = normalize(sys.argv[1])
    layers = LAYERS
    if "--layer" in sys.argv:
        layers = (sys.argv[sys.argv.index("--layer") + 1],)

    if "--verify" in sys.argv:
        return verify(root, layers)

    data = build(root, layers)
    out = os.path.join(root, MANIFEST)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    total = len(data["files"])
    sizes = sum(x["bytes"] for x in data["files"])
    print(f"写入 {out}")
    print(f"文件 {total} 个，合计 {sizes / 1048576:.1f} MB")
    for layer in layers:
        n = sum(1 for x in data["files"] if x["layer"] == layer)
        print(f"  {layer:8s} {n} 个")
    return 0


if __name__ == "__main__":
    sys.exit(main())
