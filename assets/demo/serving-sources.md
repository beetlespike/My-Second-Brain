# 推理服务的四份材料 · Four sources on LLM serving

- 视频 · 月球大叔《6分钟速通大模型KV Cache》。00:17–02:32 解释预填充、解码与缓存。Watch for what the next decode step can reuse. [Bilibili](https://www.bilibili.com/video/BV1jAZwBGEwi/?t=17)
- 文章 · 靳岩岩《【AI架构原理】预训练工程师在干什么——从 Karpathy 加入 Anthropic 说起》。算力优化一节讨论小批量解码时的数据读取。An English companion illustrates how cache blocks are assigned as a sequence grows. [WeChat](https://mp.weixin.qq.com/s/Wt_HyaK98tPF39p1y6eMow) · [vLLM: Easy, Fast, and Cheap LLM Serving with PagedAttention](https://vllm.ai/blog/2023-06-20-vllm)
- 论文 · *Taming Throughput-Latency Tradeoff in LLM Inference with Sarathi-Serve*。留意长提示词入批时，已有请求何时能拿到下一个 token。Follow one scheduling iteration with and without a prefill chunk. [OSDI paper and slides](https://www.usenix.org/conference/osdi24/presentation/agrawal) · [Author talk on YouTube](https://www.youtube.com/watch?v=S8rq3pYboZY)
- 对话 · 用一组新的到达时间，自己算首 token 延迟与随后四个 token 的平均间隔。Can an average of 20 ms hide a 65 ms pause? [计时一条流式回答 · Timing a streamed answer](streaming-dialogue.md)

想继续读，可以从 *DistServe: Disaggregating Prefill and Decoding for Goodput-optimized Large Language Model Serving* 的第 6 节看联合达标率。In Figure 8, follow the same arrival rate across the two individual latency curves and their joint attainment. [OSDI paper](https://www.usenix.org/conference/osdi24/presentation/zhong-yinmin)
