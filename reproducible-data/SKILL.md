---
name: reproducible-data
description: "Use when 建实证项目目录、交稿前查复现、或被人问「这个数怎么来的」。三层数据（raw/interim/final）留痕：拉取记录、清洗链、变量字典、运行环境，加 manifest 校验与从零重建测试。"
version: 1.0.0
author: Northseacaviar
license: MIT
metadata:
  hermes:
    tags: [reproducibility, data, pipeline, manifest, empirical]
    related_skills: [paper-bootstrap, data-availability, results-analysis, stats-reporting-audit, claim-source-verification]
---

# 数据留痕：让论文里每个数字都能重跑出来

目标只有一句：**半年后（或评审）问「这个数怎么来的」，能用一句话答出来——哪个脚本、读了哪个文件、原文件是哪份、什么时候拉的。**

做不到这件事的项目，通常不是算错了，是**说不清算的是什么**。换台机器、换个助手、或者只是隔了一个月，就再也跑不出同一组数。

## When to Use

- 新项目开工、建目录时（与 `paper-bootstrap` 一起做）。
- 数据更新、脚本重跑、样本口径改过之后。
- 交稿前、投稿前的最后一次可复现体检。
- 被问「这个 −2.24 是怎么算的」「换台电脑还能跑出来吗」。

## 三层目录（硬规定）

```
data/raw/      原始数据。只读，任何脚本不许写这里。拉到即冻结。
data/interim/  中间数据。面板、清洗结果、匹配表。全部可重建。
data/final/    最终数据。论文里表和图直接读的那几张。
output/        生成物。表、图、日志。可删、可重建。
code/          00_fetch / 01_clean / 02_build / 03_tables，编号即顺序。
docs/          变量字典、数字对照表、数据说明。
```

三条配套规则：

- `data/raw/` 的文件名带快照日期：`20261103_csmar_daily.csv`。同名不同日期就是两次拉取，不许覆盖。
- `interim/`、`final/`、`output/` 不进版本库——它们应该能被命令重建。进版本库的是 `code/` 加 `raw/` 的清单。
- 商业库（CSMAR、Wind、巨潮）的原始文件通常不能外传：版本库里放 `manifest.json` 与变量字典，不放文件本体。

## 必须留的五样

| 留什么 | 写在哪 | 长什么样 |
|---|---|---|
| 拉取记录 | `data/README.md` | 源、接口或页面、参数、拉取日期、原始文件名、行数 |
| 清洗链 | 每个脚本的 docstring | 读什么、写什么、行数怎么变（4656 → 4628 → 4612） |
| 变量字典 | `docs/变量字典.md` | 变量名、构造式、单位、窗口、缺失怎么处理 |
| 运行环境 | `docs/环境.md` 或脚本头 | Python 版本、包版本、随机种子、机器 |
| 数字对照 | `docs/数字对照表.md` | 数字 → 值 → 出处表 → 脚本 → 数据文件 |

「数字对照表」是这套东西唯一直接服务论文的部分：正文里出现的每个关键数字，一行，写清它来自哪张表、哪段代码、哪个文件。改稿时对着它核，比对着记忆核可靠。

## 每张表都要能追溯到源

表头或表注写一行 provenance，格式固定：

```
source: code/03_tables.py::tab3_caliber → data/final/panel_main.csv (n=4656)
```

图同理，写在生成脚本的 docstring 里。评审不问就算了，一旦问，这一行就是答案。

## 三件校验

1. **样本漏斗闭合**：初始 → 剔除 → 留存，每一步的剔除数与留存数必须加总对得上。漏斗对不上，后面所有数字都不可信。
2. **行数核对**：`data/final/` 的行数 = 论文里报告的那个 n。表里写 4612，文件里就得是 4612 行。
3. **哈希留痕**：`manifest.json` 记录每个文件的 sha256、字节数、行数、修改时间。重跑后比对，一致才算复现。

生成与校验用同一个脚本，只用标准库：

```bash
python scripts/data_manifest.py /path/to/project            # 生成 manifest.json
python scripts/data_manifest.py /path/to/project --verify   # 与 manifest 比对，报漂移
```

## 重建测试：唯一能证明复现的动作

删掉 `interim/`、`final/`、`output/`，从 `raw/` 按编号顺序重跑 00 → 03，再与旧 `final/` 比对。

- 哈希一致 → 可复现，收工。
- 不一致 → 只有三种原因：有随机性没记种子、有隐藏的中间文件依赖、有人手工改过数据。

**这个测试一年至少做一次**，最好在交稿前做。第一次做通常会失败，失败的地方就是隐患所在。

## 不可得的数据怎么办

商业库数据不能随稿公开，这不影响可复现性，只要能说清怎么重新拉到：

- `data/README.md` 写清库名、数据集 ID、字段列表、时间窗、筛选条件、导出参数。
- 附一份拉取脚本（哪怕只是 curl/网页操作步骤），让下一个人能照着重做。
- 数据可得性声明里写"数据来自 CSMAR XX 库，按附录 A 的参数可复现"，不写"数据不便公开"了事。

## 常见死法（按出现频率）

1. **手工改过 Excel**，没有痕迹。复现失败的头号原因，且无法事后补救。
2. 文件名带「最终版2_改_真的最终」。
3. 论文里的数字是上一次跑的老版本，脚本已经改过。
4. 只有结果没有脚本，或者脚本里写死了中间文件路径。
5. 时间窗口、样本筛选条件只写在脑子里，没写进代码也没写进文档。
6. 两个脚本写同一个中间文件，先后顺序不同结果就不同。

## 与相邻 skill 的分界

- `paper-bootstrap`：建项目骨架、活动源文件、项目记忆。本 skill 管数据这一层的纪律，两者一起用。
- `data-availability`：写投稿用的数据可得性声明文字。本 skill 管数据本身留没留痕，声明是它的产出之一。
- `results-analysis`：把模型输出变成可辩护的图表。本 skill 保证那张图能从 raw 重建出来。
- `stats-reporting-audit`：查论文里报的统计量对不对。本 skill 查那些数字有没有可追溯的来路。

## 开工清单

- [ ] 建三层目录，`data/README.md` 写第一批拉取记录
- [ ] 拉数据脚本进 `code/00_fetch/`，文件名带日期
- [ ] 每个清洗脚本 docstring 写明输入、输出、行数变化
- [ ] `docs/变量字典.md` 覆盖所有进入回归的变量
- [ ] 跑一次 `data_manifest.py` 生成 manifest
- [ ] 每张表加 `source:` 一行
- [ ] 建 `docs/数字对照表.md`，正文关键数字逐条登记
- [ ] 交稿前做一次全量重建测试
