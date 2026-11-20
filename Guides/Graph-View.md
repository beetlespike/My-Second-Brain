# 在 Obsidian 看知识网络 · Obsidian graph view

用 Obsidian 打开完整示例库，在左侧选择「查看关系图谱」。灰蓝色是已经整理的概念，淡金色是 AI 建议学习的概念。点击节点可以读它与相邻节点为什么相连。示例使用英文文件名，中文概念名保留在笔记或别名里，两种语言看到的是同一张图。

Open the full example folder as an Obsidian vault and select **Open graph view**. Blue-gray marks existing concepts. Pale gold marks proposed study nodes. Select one to read the explanation behind its links.

| 在图谱面板的「筛选」中输入 · Graph filter | 视图 · View |
| --- | --- |
| `path:Concepts OR (path:待学概念 tag:#ai-suggested)` | 完整概念网络 · Full network |
| `tag:#case-serving` | 推理服务 · LLM serving |
| `tag:#case-tokenizers` | 多语言分词 · Multilingual tokenizers |
| `tag:#case-rlvr` | 强化学习与解题覆盖 · RLVR and coverage |

**沿用 README 的配色**　关闭示例库窗口，把 `assets/demo/obsidian-graph.json` 复制为 `.obsidian/graph.json`，将 `assets/demo/obsidian-graph.css` 放入 `.obsidian/snippets/`。已有配置可先备份。重新打开库，选深色外观并启用此样式片段。在全图筛选条件后加上 ` OR path:MOCs`，就能同时看主题地图。

**Use the README colors**　Close the example vault. Copy `assets/demo/obsidian-graph.json` to `.obsidian/graph.json` and the companion CSS file to `.obsidian/snippets/`. Back up existing settings if needed. Reopen the vault, select dark appearance and enable the snippet. To include the topic maps, append ` OR path:MOCs` to the full-network filter. [Obsidian Graph view help](https://obsidian.md/help/plugins/graph)
