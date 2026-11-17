# My Second Brain

简体中文 · [English](README.en.md) · [MIT](LICENSE)

用 Obsidian 管理笔记，用 Codex 整理材料和带学。视频、文章、论文或对话讲到同一个概念，就补进同一页。Codex 可以沿着这些笔记的联系，找出值得接着学的问题。

[第一次使用](Guides/第一次使用.md) · [浏览示例笔记](MOCs/知识库入口.md)

![黑底 Obsidian 关系图谱。灰蓝色是已有概念，淡金色是 AI 提出的待学建议。](assets/demo/obsidian-graph.png)

灰蓝色是已有概念，淡金色是 AI 建议接着学的题。[延迟预算下比较 RAG](待学概念/模型评测/延迟预算下比较RAG.md)把检索召回、答案质量和等待时间放进同一道选型题。[在 Obsidian 打开图谱](Guides/Graph-View.md)

## 拿一份材料试试

在 GitHub 点 **Code → Download ZIP** 并解压。用 Obsidian 和 Codex 打开同一个文件夹，把材料和一个想弄懂的问题交给 Codex。

> 请读 AGENTS.md。用这份材料帮我理解这个问题，把能复用的解释补进概念页，留好出处。也看看有没有值得接着学的问题。

示例里的[视频](Videos/抽样次数与误差.md)和[短文](Articles/重复抽样与标准误.md)是合成材料。它们都补进了[标准误](Concepts/数理基础/标准误.md)，也都假设观测独立。Codex 顺着这个条件提出了[相关抽样](待学概念/数理基础/相关抽样.md)。把数据表的每一行复制一次，均值的标准误会变小吗？先自己算，再请 Codex 讲卡住的那一步，做张复习卡。[从原文试到复习](Guides/第一次使用.md)

## 按自己的习惯用

我常在论文、课程和对话里碰到同一个问题。我想下次回来时能接着学，所以把解释留在一页，分别记下出处。[定期整理](Guides/自动整理与维护.md)

笔记是本地 Markdown，编辑器、AI 助手和材料读取工具都可以换。卡片用 Python 3.9 或更新版本生成，在浏览器里离线复习。[来源与工具](Guides/来源与工具.md) · [添加来源和调整复习](Guides/工具与扩展.md)

代码、模板和示例用 [MIT](LICENSE)。[第三方组件与导入材料](THIRD-PARTY.md)适用各自的许可。试用遇到问题，欢迎用公开或合成材料[提个 Issue](https://github.com/beetlespike/My-Second-Brain/issues)。
