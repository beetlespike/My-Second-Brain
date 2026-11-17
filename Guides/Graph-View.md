# 在 Obsidian 看知识网络

[English](#view-the-network-in-obsidian)

用 Obsidian 打开完整的示例目录，选择左侧的「查看关系图谱」。点圆点读笔记，鼠标停在圆点上看连线。

想用 README 里的黑底和两种节点颜色，可以在示例库里用配套设置。

1. 关闭示例库窗口。把 `assets/demo/obsidian-graph.json` 复制到 `.obsidian/graph.json`。目录可以手动建，已有设置先备份。
2. 把 `assets/demo/obsidian-graph.css` 复制到 `.obsidian/snippets/`。重新打开库，在「外观」选深色并启用该 CSS 片段。

灰蓝色是已有的概念。淡金色是「待学概念」中带 `ai-suggested` 标签的笔记。可以从「延迟预算下比较 RAG」点进去，看看检索召回、答案质量和首段输出延迟如何影响选型。

[Obsidian 关系图谱说明](https://obsidian.md/help/plugins/graph)

## View the network in Obsidian

Open the full example folder as a vault and select **Open graph view**. Click a node to read the note, or hover to see its links.

To use the README's dark background and two node colors in the example vault, close its window and copy `assets/demo/obsidian-graph.json` to `.obsidian/graph.json`. Create the folder if needed and back up any existing graph settings. Copy `assets/demo/obsidian-graph.css` into `.obsidian/snippets/`. Reopen the vault, choose dark mode in Appearance, and enable the snippet.

Blue-gray nodes are existing concepts. Pale gold marks study notes tagged `ai-suggested` in the `待学概念/` folder. Open **Comparing RAG under a latency budget** (延迟预算下比较RAG) to see how retrieval recall, answer quality, and wait time affect the choice of setup.

[Obsidian Graph view help](https://obsidian.md/help/plugins/graph)
