# Python 卡尔曼滤波与贝叶斯滤波 · 简体中文版

这是 Roger R. Labbe Jr. 所著 [Kalman and Bayesian Filters in Python](https://github.com/rlabbe/Kalman-and-Bayesian-Filters-in-Python) 的简体中文版本。通过可运行的 Python 示例，逐步学习贝叶斯滤波、卡尔曼滤波、UKF、EKF、粒子滤波和平滑。

**从[中文目录](table_of_contents.ipynb)开始阅读。** 当前已覆盖全书现有 Notebook 的讲解文字；这是中文初稿，翻译来源、校订范围与原著尚未完成的部分见 [TRANSLATION.md](TRANSLATION.md)。英文项目说明保存在 [README.en.md](README.en.md)。

## 在线阅读

- [GitHub 中文目录](https://github.com/Ancho5515/Kalman-and-Bayesian-Filters-in-Python_zh_cn/blob/master/table_of_contents.ipynb)：浏览正文、代码和已保存的图表。
- [nbviewer 中文目录](https://nbviewer.org/github/Ancho5515/Kalman-and-Bayesian-Filters-in-Python_zh_cn/blob/master/table_of_contents.ipynb)：静态阅读。
- [Binder 交互入口](https://mybinder.org/v2/gh/Ancho5515/Kalman-and-Bayesian-Filters-in-Python_zh_cn/master?filepath=table_of_contents.ipynb)：由第三方服务按需构建运行环境，首次打开可能较慢。

上面的链接读取 `master` 分支。若正在查看尚未合并的翻译分支，请直接点击当前分支中的 `table_of_contents.ipynb`。

## 本地阅读与运行

本版使用 **Python 3.12** 验证，依赖版本保存在 `requirements.txt`。建议使用独立虚拟环境，避免影响其他 Python 项目。

```bash
git clone https://github.com/Ancho5515/Kalman-and-Bayesian-Filters-in-Python_zh_cn.git
cd Kalman-and-Bayesian-Filters-in-Python_zh_cn
```

Windows：

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\jupyter notebook table_of_contents.ipynb
```

Linux / macOS：

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/jupyter notebook table_of_contents.ipynb
```

打开章节后，从上到下运行代码单元。主要章节都在仓库根目录；辅助说明在 `Supporting_Notebooks/`，动画生成代码在 `animations/`，作者的实验草稿在 `experiments/`。

也可以在仓库根目录运行 `conda env create -f environment.yml`，然后执行 `conda activate kf_bf`。

## 校验

在已安装依赖的环境中执行：

```bash
python tools/check_translation.py
python tools/check_translation.py --render build/html
python tools/run_smoke.py
```

第一个命令校验全部 44 个 Notebook 的结构、625 段独立公式、示例代码块、输出与本地文件链接；第二个同时导出 HTML，并检查指向同一章节内部的锚点；第三个逐一执行主目录全部 23 个 Notebook 的代码。运行检查在临时副本中执行，不覆盖书中保存的图表。

第 14 章有一格刻意演示 IMM 状态维度不一致时的 `ValueError`，这是教材反例。自动校验会核对该异常；在 Jupyter 中阅读时，看到该异常后可继续运行后面的单元。

## 翻译与许可

原著作者为 **Roger R. Labbe Jr.**。本轮以 [kjkimnb 的完整中文译稿](https://github.com/kjkimnb/Kalman-and-Bayesian-Filters-in-Python_Chinese_edition/tree/a4378479bd3b04730e6f6cdd14bf0f1af61daf8b/zh-cn)为基础，补充校订、修复公式和链接，并进行运行验证。具体版本与改动记录见 [TRANSLATION.md](TRANSLATION.md)。

原项目 README 将正文标为 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)，仓库中的程序使用 MIT 许可。原始署名及各文件已有的许可声明均予保留，包括前言中的历史许可声明；英文原始说明见 [README.en.md](README.en.md)，代码许可见 [kf_book/LICENSE.txt](kf_book/LICENSE.txt)。
