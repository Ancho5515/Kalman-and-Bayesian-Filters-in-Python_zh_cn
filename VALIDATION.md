# 中文版验证记录

日期：2026-11-25。英文基线：`04b2bea802321086effbd99402fc13c893d11110`。

| 检查 | 结果 |
| --- | --- |
| Notebook 原生格式校验（包含旧版 nbformat 3） | 44 / 44 通过 |
| Markdown 覆盖与基线检查 | 1,079 个单元 |
| 原著独立公式 `$$...$$` 的内容和顺序 | 625 段一致 |
| Markdown 围栏代码示例 | 与英文基线一致 |
| 非 Markdown 数据、元数据和缓存输出 | 与英文基线一致，仅允许第 5 章三处绘图关键字兼容改动 |
| Notebook 本地文件链接 | 通过 |
| 静态 HTML 导出 | 44 / 44 通过 |
| 导出 HTML 的同章锚点 | 44 / 44 通过；包含中文标题和旧式 `name` 锚点 |
| 主目录 Notebook 逐格执行 | 23 / 23 完成，共 609 个代码单元 |
| 非预期代码异常 | 0 |
| 预期教学异常 | 第 14 章第 92 号单元的 `ValueError`，核对异常类型与信息后继续 |
| `git diff --check` | 通过 |

执行环境为 Python 3.12.14，核心包版本见 `requirements.txt`。运行检查通过独立 IPython 进程逐格执行临时副本，可在禁止 Jupyter 内核套接字的环境中使用，不改写原书文件。它验证 Python 代码能够执行，不代替浏览器交互测试或科学结论的独立证明。

2026-11-25 补充校订时，已重新通过 44 个 Notebook 的结构和内容保护检查，以及主目录 23 个 Notebook、609 个代码单元的执行检查。另用 NumPy 复核了高斯章译注中的均值、方差与标准差，用 SciPy 的二维卡方分布核对了 EnKF 译注中的椭圆覆盖概率。正文进一步校订范围见 [TRANSLATION.md](TRANSLATION.md)。

锚点检查先在未修复的第 6 章导出结果上复现了 `#References` 缺失，再为中文标题加入稳定目标，并重新导出全书验证。检查还覆盖了中文目标、百分号编码目标及旧式 `[1]` 命名锚点；外部网址和其他文件的片段不作为同章目标检查。

重现命令：

```bash
python tools/check_translation.py
python tools/check_translation.py --render build/html
python tools/run_smoke.py
git diff --check
```

HTML 检查验证导出成功，没有逐页浏览全部图表，也没有测试 Binder/nbviewer 的远程构建。动画生成器和实验草稿只进行结构、翻译基线与静态导出检查，没有作为正式教材章节批量执行。译文完整性与后续审校范围见 [TRANSLATION.md](TRANSLATION.md)。
