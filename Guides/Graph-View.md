# 在 Obsidian 看知识网络

[English](#view-the-network-in-obsidian)

用 Obsidian 打开含示例笔记的完整目录，在左侧选择「查看关系图谱」。点圆点可以读笔记。鼠标移到圆点上可以看它连着哪些笔记。

想复现预览的分组和黑底，可以在单独的示例库中使用配套文件。

1. 在打开该库之前，把 `assets/demo/obsidian-graph.json` 复制到该库的 `.obsidian/graph.json`。如果已有图谱设置，先备份。
2. 把 `assets/demo/obsidian-graph.css` 放到该库的 `.obsidian/snippets/`。打开 Obsidian，在「外观」选深色配色并启用此 CSS 片段。
3. 打开关系图谱。六种颜色对应概念目录。淡金色的圆点是带 `ai-suggested` 标签的待学页。

例如，「检索上下文预算」同时连着「检索与重排」和「Prefill 与 Decode」。点进去可以试着在给定 token 限额内选出支持结论、条件和例外的证据。

[Obsidian 关系图谱说明](https://obsidian.md/help/plugins/graph)

## View the network in Obsidian

Open the full example folder as a vault and select **Open graph view**. Click a node to read the note. Hover to see its links.

To reproduce the preview in a separate example vault, copy `assets/demo/obsidian-graph.json` to `.obsidian/graph.json` before opening the vault. Back up your graph settings if that file already exists. Put `assets/demo/obsidian-graph.css` in `.obsidian/snippets/`, then choose the dark appearance and enable the snippet. The six colors correspond to concept folders. Pale gold marks pending study notes tagged `ai-suggested`.

Try **Retrieval context budget** (检索上下文预算). Its links lead to **Retrieve and rerank** and **Prefill and decode**. The note asks you to fit the evidence for a result, its conditions, and its exception within a token budget.

[Obsidian Graph view help](https://obsidian.md/help/plugins/graph)
