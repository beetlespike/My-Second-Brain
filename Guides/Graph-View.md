# 在 Obsidian 看知识网络

[English](#view-the-network-in-obsidian)

用 Obsidian 打开含示例笔记的完整目录，在左侧选择「查看关系图谱」。点圆点可以读笔记。鼠标移到圆点上可以看它连着哪些笔记。

想复现预览的分组和黑底，可以在单独的示例库中使用配套文件。

1. 在打开该库之前，把 `assets/demo/obsidian-graph.json` 复制到该库的 `.obsidian/graph.json`。如果已有图谱设置，先备份。
2. 把 `assets/demo/obsidian-graph.css` 放到该库的 `.obsidian/snippets/`。打开 Obsidian，在「外观」选深色配色并启用此 CSS 片段。
3. 打开关系图谱。各主题按概念目录着色。淡金色的圆点是带 `ai-suggested` 标签的待学页。

例如，「延迟预算下比较 RAG」连着检索召回率、答案正确性和推理延迟。点进去可以先按等待上限选一套方案，再核对它放到真实流量里还缺什么数据。

[Obsidian 关系图谱说明](https://obsidian.md/help/plugins/graph)

## View the network in Obsidian

Open the full example folder as a vault and select **Open graph view**. Click a node to read the note. Hover to see its links.

To reproduce the preview in a separate example vault, copy `assets/demo/obsidian-graph.json` to `.obsidian/graph.json` before opening the vault. Back up your graph settings if that file already exists. Put `assets/demo/obsidian-graph.css` in `.obsidian/snippets/`, then choose the dark appearance and enable the snippet. The groups follow the concept folders. Pale gold marks pending study notes tagged `ai-suggested`.

Try **Comparing RAG under a latency budget** (延迟预算下比较RAG). It connects retrieval recall, answer quality, and serving latency. Pick a setup that meets the latency limit, then check what you would still need to measure under real traffic.

[Obsidian Graph view help](https://obsidian.md/help/plugins/graph)
