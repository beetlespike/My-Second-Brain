# My Second Brain

简体中文 · [English](README.en.md)

> 答案随手可得，判断从哪里来？

两个人用同一个 AI，也可能从同一份材料里看出不同的问题。各自一路学过什么、能看见哪些联系，会影响他们把工作引向哪里。在研究、创作和决策中，*human in the loop* 意味着人一直在引导与 AI 的合作，从提出问题到判断怎样才算做好。AI 能参与的事越多，人的学识、品味和判断就越要紧。这套私人知识库想帮你积累所学，慢慢养成自己的眼光。

看完视频、读过文章或论文，或是和 AI 聊明白一个问题，就可以把链接或对话交给自己的 AI 助手。它把材料里学到的概念写进本地 Markdown，彼此有关的概念连成一张网。沿着这些联系，助手还能找出你没学过、却能把几个熟悉的概念串起来的东西，做成一张待学卡。下次再读到相关材料，你就多了一层理解。

[用自己的材料开始](Guides/第一次使用.md) · [今日知识卡](Guides/第一次使用.md#今日知识卡) · [在 Obsidian 里看示例](Guides/Graph-View.md)

![以 Obsidian 和 Codex 为例。你先看视频、读文章或论文、参与对话，再把学过的来源链接交进私人知识库。Codex 整理概念，从网络里发现缺失的节点，做成待学概念卡。卡片回到你手中，新学的概念伴你去读下一份材料。长期所学形成的品味和判断，也会影响你与 AI 共同做的事。](assets/demo/human-ai-loop.zh.png)

## 平凡的一周

> 有些主题，回头看才叫得出名字。

看完 B 站上[讲 KV 缓存的六分钟短片](https://www.bilibili.com/video/BV1jAZwBGEwi/)，我在库里的 Codex 聊天只贴了网址。Codex 用本机模型转写这段视频，把「KV 缓存」和「预填充与解码」各写成一页。隔天读到公众号文章[《预训练工程师在干什么》](https://mp.weixin.qq.com/s/Wt_HyaK98tPF39p1y6eMow)，我也把链接发过去。Codex 找到原有的「显存带宽」笔记，把文中的例子补了进去。

这几天还看了段 [YouTube 分词课](https://www.youtube.com/watch?v=zduSFxRajkE&t=1430s)。读 [*Sarathi-Serve*](https://www.usenix.org/conference/osdi24/presentation/agrawal) 时，我和 GPT 在[一段对话](assets/demo/streaming-dialogue.md)里算了算回答中途停了多久。

## 周末翻笔记

> 新发现有时就在两个熟悉的概念之间。

我设置了自动化任务，让 Codex 定期读取我指定的学习对话。Codex 把对话里的算例补进概念笔记，再把能一起解释一个问题的概念编成主题地图（MOC）。周末翻开[推理服务地图](MOCs/Streaming%20LLM%20Serving.md)，我才看出缓存、带宽和那次停顿之间的联系。分词笔记在[另一张地图](MOCs/Multilingual%20Tokenizers.md)里。

![Obsidian 原生推理服务图谱。灰蓝色是学过的概念，三个淡金色节点是 Codex 建议补学的概念。](assets/demo/obsidian-serving.png)

## 清晨的卡片

> 已经懂得的事，还能教我们什么？

早上收到的卡片里，除了那道关于停顿的旧题，还有图里淡金色的「预填充与解码分离」。这是 Codex 顺着缓存和调度找到的新概念。我先挑了这张。

[卡片上的两组算例](待学概念/推理系统/Prefill-Decode%20Disaggregation.md#简答)只改了带宽，拆分就从多花时间变成了省时间。接着读 [*DistServe*](Papers/DistServe.md) 时，我会留意两个阶段放在哪儿、缓存要经过哪条链路。读完再把论文链接交给 Codex，下一轮就从这次阅读开始。

每个知识库都有一个固定的私人网址。在这台电脑上收藏它，每天都在同一处翻卡、评分、留言。评分当场记入复习计划。下一次制卡前，助手先读积下的留言，改题、补卡，或直接回答。点「我的留言与回复」就能看到结果。我自己也在 Codex 的定时聊天里收卡，两边用的是同一份记录。

[试试这组卡片](Guides/第一次使用.md#走一遍推理服务的例子) · [给复习卡留意见](Guides/Flashcard-Review.md#反馈与保存)

![完整的 Obsidian 关系图谱，包括推理服务、多语言分词、强化学习等主题。](assets/demo/obsidian-graph.png)

用自己的材料，可以在公开模板旁边[另建一个私人库](Guides/第一次使用.md#自己的学习库)。笔记存在本地。用云端助手时，它读到的内容会发给相应服务，你可以只给它一个主题的材料。

[随库的练习字幕](assets/demo/first-token.vtt)可以离线试读。在线视频和 PDF 的读取工具按需安装，登录页可以用自己导出的正文，扫描件可以用 OCR 文本。想在早上收到卡片，可以在能读本地文件的客户端设置定时任务。[来源与工具](Guides/来源与工具.md) · [自动化设置](Guides/自动整理与维护.md)

[更多主题地图](MOCs/知识库入口.md) · [MIT 许可](LICENSE) · [第三方材料](THIRD-PARTY.md) · [反馈](https://github.com/beetlespike/My-Second-Brain/issues)
