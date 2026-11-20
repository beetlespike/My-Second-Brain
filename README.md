# My Second Brain

简体中文 · [English](README.en.md)

My Second Brain 是一套本地 Markdown 模板。你从各处学到的概念，在 Obsidian 里连成一张自己的知识网。Codex 帮你整理，也会沿着已有的联系找出你还没学过的概念，做成知识卡。

[用自己的材料开始](Guides/第一次使用.md) · [在 Obsidian 里看示例](Guides/Graph-View.md)

## 平凡的一周

看完一段 B 站视频，我把链接发给 Codex，说说自己看懂的部分。「KV 缓存」和「预填充与解码」各写成一页。隔天读公众号，文章里的一个例子又补进了原有的「显存带宽」笔记。[6 分钟讲 KV 缓存](https://www.bilibili.com/video/BV1jAZwBGEwi/) · [预训练工程师在干什么](https://mp.weixin.qq.com/s/Wt_HyaK98tPF39p1y6eMow)

这几天还看了段分词课。读 *Sarathi-Serve* 时，我和 GPT 算过一段回答中途停了多久。[YouTube 分词课](https://www.youtube.com/watch?v=zduSFxRajkE&t=1430s) · [论文](https://www.usenix.org/conference/osdi24/presentation/agrawal) · [改写对话](assets/demo/streaming-dialogue.md)

## 周末翻笔记

我让 Codex 定期整理选好的学习对话。周末把那次停顿的算例和缓存、带宽放在一起，才看出这几页都和推理服务有关。我把它们编成一张主题地图（MOC），想细读时，就从「回答为什么会停在半句」读起。分词另有一张。[推理服务](MOCs/Streaming%20LLM%20Serving.md) · [多语言分词](MOCs/Multilingual%20Tokenizers.md)

![Obsidian 原生推理服务图谱。灰蓝色是学过的概念，三个淡金色节点是 Codex 建议补学的概念。](assets/demo/obsidian-serving.png)

## 清晨的两张卡

早上的卡片里有一道关于那次停顿的旧题，也有一个新概念「预填充与解码分离」。图里这个淡金色的节点，是 Codex 顺着缓存和调度笔记找到的。等我弄懂了，就请它用这个概念出复习题。

翻过旧卡，我选了「有点模糊」，又留了句“下次换个例子”。把反馈交给 Codex，它会按评分安排复习，也能照着留言改题。[试试这组卡片](Guides/第一次使用.md#走一遍推理服务的例子)

![完整的 Obsidian 关系图谱，包括推理服务、多语言分词、强化学习等主题。](assets/demo/obsidian-graph.png)

笔记都是普通的 Markdown，可以换编辑器和 AI 助手。定时任务在自己的环境里设置，也可以手动提供材料。[来源与工具](Guides/来源与工具.md) · [自动整理与每日卡片](Guides/自动整理与维护.md)

[更多主题地图](MOCs/知识库入口.md) · [MIT 许可](LICENSE) · [第三方材料](THIRD-PARTY.md) · [反馈](https://github.com/beetlespike/My-Second-Brain/issues)
