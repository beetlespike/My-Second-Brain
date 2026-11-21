# 推理服务的四份材料 · Four sources on LLM serving

- 视频 · 月球大叔《6分钟速通大模型KV Cache》：用 00:17–02:32 厘清预填充和解码在哪一步分道扬镳，以及后续 token 如何复用之前位置的 K/V。[Bilibili](https://www.bilibili.com/video/BV1jAZwBGEwi/?t=17)
- 文章 · 靳岩岩《【AI架构原理】预训练工程师在干什么——从 Karpathy 加入 Anthropic 说起》：重点看算力优化一节——小批量解码每次都要重读整份权重却只吐很少几个 token；vLLM 的 PagedAttention 博客顺手接上了缓存块的内存管理账。[WeChat](https://mp.weixin.qq.com/s/Wt_HyaK98tPF39p1y6eMow) · [vLLM: Easy, Fast, and Cheap LLM Serving with PagedAttention](https://vllm.ai/blog/2023-06-20-vllm)
- 论文 · *Taming Throughput-Latency Tradeoff in LLM Inference with Sarathi-Serve*：顺着调度器的一步步执行看，长提示词直接塞进批里怎样拖慢正在生成的回答，分块预填充又怎么让它们错峰拼到同一轮里。[OSDI paper and slides](https://www.usenix.org/conference/osdi24/presentation/agrawal) · [Author talk on YouTube](https://www.youtube.com/watch?v=S8rq3pYboZY)
- 对话 · 一段排查流式输出突然卡顿的学习记录（数字为公开示例重设）：为什么平均 TPOT 只有 20 ms，实际仍然会被中间那一下 65 ms 卡住。[计时一条流式回答 · Timing a streamed answer](streaming-dialogue.md)

顺着这四份材料往下看，正好引出 *DistServe* 第 6 节的联合达标率测试：同一到达率下，拆开预填充和解码分别压低各自延迟后，还要把在两组 GPU 间传 KV 缓存的时间算进去，再看两条单指标曲线和联合达标曲线。[OSDI paper](https://www.usenix.org/conference/osdi24/presentation/zhong-yinmin)
