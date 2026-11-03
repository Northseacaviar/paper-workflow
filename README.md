# paper-workflow

论文从选题到投稿的 Agent skill 集合，38 个，一个目录一个 skill。纯 markdown 加 Python 标准库，拷进 skills 目录即可用。

按一次投稿的先后分四组。组内 skill 可以单独用，也可以让 `paper-workflow` 路由。

## 一、流程骨架（6）

| skill | 用途 |
|---|---|
| [paper-workflow](paper-workflow/) | 总入口：先认文章类型与改动范围，再路由到具体 skill |
| [paper-bootstrap](paper-bootstrap/) | 开新稿或整理旧目录：标准结构、活动源文件、项目记忆、目标期刊默认值 |
| [paper-topic-screening](paper-topic-screening/) | 选题能不能做：先查撞车，再验数据，最后小样本试跑 |
| [manuscript-optimizer](manuscript-optimizer/) | 稿子的问题可能不在句子：重排主张层级与证据链 |
| [draft-marker-discipline](draft-marker-discipline/) | 跨多轮写作时用源内标记跟踪未决问题，按后果排序 |
| [submission-audit](submission-audit/) | 投稿前体检：主张支撑、图注同步、方法引用、术语一致 |

## 二、写作与语言（9）

| skill | 用途 |
|---|---|
| [scientific-writing](scientific-writing/) | 整段学术散文：结构、引用格式、报告规范 |
| [write-scientific-manuscript](write-scientific-manuscript/) | 句子对但读不懂：埋没的主旨句、缺失的逻辑桥 |
| [scientific-prose-style](scientific-prose-style/) | 文风规则：破折号预算、AI 味清单、检测脚本 |
| [academic-humanizer](academic-humanizer/) | 保留学术约定，改掉 AI 腔（论文、标书、rebuttal） |
| [humanizer](humanizer/) | 通用去 AI 味：删套话，注入真实语气 |
| [anti-defensive-writing](anti-defensive-writing/) | 删掉防御式写作：审计腔、自我辩解、开发者视角 |
| [econ-write](econ-write/) | 经济学论文写法：Cochrane、McCloskey 等 50+ 指南的合成 |
| [conference-paper-writing](conference-paper-writing/) | 会议稿优先（NeurIPS/ICML/ICLR/ACL/AAAI/COLM），附模板 |
| [chinese](chinese/) | 让中文读起来像母语写的，正式与口语、大陆与台湾 |

## 三、审查与核验（13）

| skill | 用途 |
|---|---|
| [citation-verifier](citation-verifier/) | 引文卫生：DOI/PMID 完整、占位引用、BibTeX 一致 |
| [reference-audit-guide](reference-audit-guide/) | 文献真不真：CrossRef / Semantic Scholar / arXiv / PubMed 实查 |
| [claim-source-verification](claim-source-verification/) | 每个论断对上它引的源 |
| [text-provenance-verification](text-provenance-verification/) | 引语的来源与措辞逐字核验 |
| [data-availability](data-availability/) | 数据可得性声明：仓库、登录号、受限数据措辞 |
| [stats-reporting-audit](stats-reporting-audit/) | 统计报告审查：p 值、区间、样本量、重复数、多重比较 |
| [results-analysis](results-analysis/) | 把模型评估输出变成可辩护的图表与结论 |
| [results-section-revision](results-section-revision/) | Results 小节：图和主张已定，改小节流与论述推进 |
| [ai-draft-quality-screen](ai-draft-quality-screen/) | 判断这篇 AI 草稿到底有没有说东西 |
| [empirical-manuscript-diagnosis](empirical-manuscript-diagnosis/) | 实证稿能投哪一档、投稿前改什么 |
| [rebuttal-response](rebuttal-response/) | 审稿意见答复：逐条回应、改写稿定位 |
| [paper-reviewer](paper-reviewer/) | 站审稿人一侧：写审稿报告、清点诉求、给答复打分 |
| [review-article-architecture](review-article-architecture/) | Review / survey / perspective 的架构 |

## 四、图表与交付（10）

| skill | 用途 |
|---|---|
| [nature-figure](nature-figure/) | Nature 系投稿级配图：多面板、matplotlib/ggplot2、SVG/PDF/TIFF |
| [figure-style](figure-style/) | 交付图的正确性与可读性：字号阶梯、无框图例、300 dpi 自检 |
| [figure-planner](figure-planner/) | 一张图一个主张：面板分工、图例与正文对齐 |
| [nature-portfolio-playbook](nature-portfolio-playbook/) | Nature / Nature Methods / Nature Biotechnology 选刊与政策 |
| [journal-selection-for-submission](journal-selection-for-submission/) | 挑刊：抓该刊近两年目录核实题材，按录用概率排序 |
| [academic-presentations](academic-presentations/) | 从论文做学术幻灯片与演示视频 |
| [nature-paper2ppt](nature-paper2ppt/) | 中文组会与答辩 PPTX，带源图与讲稿备注 |
| [paper-deck](paper-deck/) | 高质感 AIGC 幻灯片：先叙事导演，再逐页生图合成 |
| [paper-comic](paper-comic/) | 论文方法图解：封面、概述、机制三类图，先定范围再生成 |
| [paper-analyzer](paper-analyzer/) | 论文转深度 HTML 长文：公式、Mermaid、多轮工作流 |

## 怎么挑

- 手上是一份稿子要改：`paper-workflow` 认类型，`manuscript-optimizer` 重排主张，`submission-audit` 收口。
- 只有一个段落读不动：`write-scientific-manuscript`，别上整套。
- 疑心引文是编的：`reference-audit-guide` 先实查，`citation-verifier` 再查格式。
- 要出图：`figure-planner` 定主张与面板，`nature-figure` 出图，`figure-style` 收可读性。
- 被拒了要答复：`rebuttal-response` 写，`paper-reviewer` 反过来挑刺。

## 安装

整仓克隆，或只拷你要的目录，保持 `SKILL.md` + `scripts/` + `references/` 的结构：

```bash
git clone https://github.com/Northseacaviar/paper-workflow.git
cp -r paper-workflow/{paper-workflow,manuscript-optimizer} ~/.hermes/skills/
```

- Hermes：`~/.hermes/skills/<skill>/`（或你配置的 skills 目录）
- Claude Code：`<project>/.claude/skills/<skill>/`

脚本只依赖 Python 3 标准库，无第三方包。

## 上游参考

[cLin-c/paper-skill](https://github.com/cLin-c/paper-skill)（MIT，138 stars）是另一条路：单入口单 skill，把读论文、文献综述、研究框架、写作、中英互译、LaTeX、配图、引文核验、选刊、审稿与答复、投稿包串成 11 条 route（`read` `literature` `write` `figures` `review` `rebuttal` `citations` `journal` `submit` `reporting` `full-verify`）。

本仓库没有复制它的内容。两边取舍不同：它是"一个 skill 管到底、按 route 加载"，这里是"按工序拆开、按需拼装"。

## 外部 skill 库（参考，未收录）

星数截至 2026-11-03，用 `gh api repos/<owner>/<repo>` 可复核。判断一栏是我自己的取舍，装之前请自己看一遍 SKILL.md。

| 仓库 | 星 | 许可 | 做什么 | 我的判断 |
|---|---:|---|---|---|
| [Yuan1z0825/nature-skills](https://github.com/Yuan1z0825/nature-skills) | 52.0k | Apache-2.0 | Nature 论文学术表达与科研绘图，24 个 `nature-*` skill：检索、引文、数据、下载、实验日志、配图、审稿、答复、提案 | 本仓库 `nature-figure`、`nature-paper2ppt` 的上游。做生命科学或 Nature 系投稿，整包看一遍值得 |
| [k-dense-ai/scientific-agent-skills](https://github.com/k-dense-ai/scientific-agent-skills) | 55.9k | MIT | 177 个科研 skill + 100 多个科学数据库接口（生物、化学、医学、药物发现） | 偏湿实验与生物信息，经济金融用不上几个；数据库接入的写法可参考 |
| [blader/humanizer](https://github.com/blader/humanizer) | 64.2k | MIT | 删掉文本里的 AI 痕迹 | 本仓库 `humanizer` 的原版，英文场景第一选择 |
| [op7418/Humanizer-zh](https://github.com/op7418/Humanizer-zh) | 21.9k | MIT | humanizer 的汉化版 | 中文稿优先用这个，比硬翻英文版顺 |
| [imbad0202/academic-research-skills](https://github.com/imbad0202/academic-research-skills) | 55.2k | NOASSERTION | Claude Code 学术流水线：研究 → 写作 → 审稿 → 修改 → 定稿 | 覆盖面大；许可未明示，公开再分发前先问作者 |
| [orchestra-research/ai-research-skills](https://github.com/orchestra-research/ai-research-skills) | 14.2k | MIT | AI 研究与工程 skill 库，模型无关 | 做 ML 系统与实验管理时有用，跟论文写作是两件事 |
| [Master-cai/Research-Paper-Writing-Skills](https://github.com/Master-cai/Research-Paper-Writing-Skills) | 8.1k | MIT | 彭思达公开笔记改编的 ML/CV/NLP 论文写作 skill | 计算机方向投稿教程密度高，别的学科借的是结构不是内容 |
| [brycewang-stanford/Auto-Empirical-Research-Skills](https://github.com/brycewang-stanford/Auto-Empirical-Research-Skills) | 4.9k | NOASSERTION | 23,000+ 条实证研究 skill，8 个社科学科，Stanford REAP / CoPaper.AI 维护 | 经济学实证最相关的一个；量太大质量参差，按需挑单条，别全装 |
| [aiscientists-dev/academic-humanizer](https://github.com/aiscientists-dev/academic-humanizer) | 3.3k | MIT | 去 AI 味但保留学术语气，覆盖论文与 NSF/NIH 标书 | 本仓库 `academic-humanizer` 的上游，标书场景它比通用版细 |
| [Kiterlin/anti-defensive-writing](https://github.com/Kiterlin/anti-defensive-writing) | 1.6k | MIT | 删防御式写作：审计腔、自我辩解、开发者视角 | 本仓库 `anti-defensive-writing` 的上游 |
| [boom5426/nature-paper-skills](https://github.com/boom5426/nature-paper-skills) | 653 | MIT | Nature 风格稿件的起草、修改、审查、重投工作流 | 与本仓库分组思路接近，可对照看它的审查清单 |
| [Z4science/paper-buddy](https://github.com/Z4science/paper-buddy) | 82 | MIT | 陪写论文的 prompt 集：翻译、润色、改稿、答审稿人 | 轻量，复制即用，不装 skill 也能用 |
| [xcl2005/academic-paper-writing-skill](https://github.com/xcl2005/academic-paper-writing-skill) | 24 | MIT | 中文科研全流程单入口，可选接 18 个专业 skill | 中文语境写得最贴；接口是 Codex/Claude Code |
| [CyberStaZJU/paper-prose-calibration](https://github.com/CyberStaZJU/paper-prose-calibration) | 0 | MIT | 论文文风校准：句子级分诊、四轴诊断、LaTeX 感知的零依赖扫描器 | 星少但方法对，Claude 侧 `prose-calibration` 出自这里 |

一句话怎么用这张表：**上游三个（nature-skills、humanizer、academic-humanizer）已经在本仓库里；剩下的是补缺，不是必装。** 许可写着 NOASSERTION 的两个，自己用没问题，别往公开仓库里搬。

## 许可

原创部分 MIT © @Northseacaviar。转载与改写自第三方的 skill 逐项列在 [ATTRIBUTIONS.md](ATTRIBUTIONS.md)，Apache-2.0 全文在 [licenses/Apache-2.0.txt](licenses/Apache-2.0.txt)。
