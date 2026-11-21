# Explore the knowledge graph in Obsidian

[简体中文](关系图谱.md)

From the downloaded repository, open `examples/demo-vault/` as an Obsidian vault. If you made a full copy with `workflow.py init`, open that copy instead. Select **Open graph view**, then enter a filter.

| What to explore | Filter |
| --- | --- |
| All studied and suggested concepts in the example | `path:Concepts OR (path:待学概念 tag:#ai-suggested)` |
| LLM serving | `tag:#case-serving` |
| Multilingual tokenizers | `tag:#case-tokenizers` |
| Reinforcement learning and problem coverage | `tag:#case-rlvr` |

For the colors shown on the homepage, close the example vault window. Back up any existing graph settings. Inside that vault, copy `assets/demo/obsidian-graph.json` to `.obsidian/graph.json` and `assets/demo/obsidian-graph.css` to `.obsidian/snippets/`. Reopen the vault, choose dark appearance and enable the snippet. Blue-gray nodes are studied concepts. Pale gold marks suggestions to explore. Open a node to read why it connects to its neighbors.

Append ` OR path:MOCs` to the full filter to include the topic maps. Obsidian lays out the nodes afresh when you open the graph. [Obsidian graph view help](https://obsidian.md/help/plugins/graph)
