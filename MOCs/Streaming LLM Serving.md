---
type: moc
status: active
---

# 吞吐升上去了，为什么流式回答还会卡？

同一批 GPU 既要读新用户的长提示，也要让已经开始的回答继续往下写。把更多请求放进来，每秒生成的 token 可能变多，正在等下一句的人却可能等得更久。要决定该怎样改，先把四份材料里学到的东西摆在一起。

| 材料 | 它把哪个问题讲清楚了 |
| --- | --- |
| 月球大叔的 B 站视频《6分钟速通大模型KV Cache》 | [预填充和解码](../Concepts/推理系统/Prefill%20and%20Decode.md)各做什么，[KV 缓存](../Concepts/推理系统/KV%20Cache.md)为什么能省下重复计算。00:17–02:32 讲两阶段和缓存，03:49–04:24 讲缓存随上下文增长。[视频与时间轴](../Videos/KV%20Cache%20in%20Six%20Minutes.md) |
| 靳岩岩的公众号文章《【AI架构原理】预训练工程师在干什么——从 Karpathy 加入 Anthropic 说起》 | 按文中算力优化一节，小批量解码会花很多时间读取权重。[显存带宽](../Concepts/推理系统/Memory%20Bandwidth.md)解释了合批为什么可能更划算。vLLM 作者的图解又说明 [PagedAttention](../Concepts/推理系统/PagedAttention.md) 怎样给长短不一的请求分配空间。[公众号原文](../Articles/The%20Pretraining%20Engineers%20Article.md) · [vLLM 作者文章](../Articles/vLLM%20on%20PagedAttention.md) |
| *Taming Throughput-Latency Tradeoff in LLM Inference with Sarathi-Serve* | [连续合批](../Concepts/推理系统/Continuous%20Batching.md)允许新请求在迭代之间加入。[分块预填充](../Concepts/推理系统/Chunked%20Prefill.md)限制长提示在一轮里占用的工作量，给正在解码的请求留出机会。[OSDI 论文与 YouTube 报告](../Papers/Sarathi-Serve.md) |
| 一段关于流式计时的对话 | 第一个 token 在 120 ms 到达，第五个在 200 ms 到达。[TTFT](../Concepts/推理系统/TTFT.md) 是 120 ms，[TPOT](../Concepts/推理系统/TPOT.md) 是 20 ms。后四次若分别等 5、5、65、5 ms，看平均值就会漏掉中间的停顿。[公开改写全文与推算](../Chats/Timing%20a%20Stream.md) |

如果要选部署方案，先固定[输入长度分布](../Concepts/推理系统/Prompt%20Length%20Distribution.md)，逐步提高[请求到达率](../Concepts/推理系统/Request%20Arrival%20Rate.md)。再从 *DistServe* 看阶段拆分的代价，一条请求积累的 KV 要送去另一组 GPU，[互连带宽](../Concepts/推理系统/Interconnect%20Bandwidth.md)给出了传输时间的下界。[论文与作者图解](../Papers/DistServe.md)

## Three gaps in the serving map

| Suggested concept | What it connects |
| --- | --- |
| [Prefill-Decode Interference](../待学概念/推理系统/Prefill-Decode%20Interference.md) | A new long prompt can stall active decodes. Align token arrival times with scheduling iterations, then replay the same arrivals with smaller prefill chunks. |
| [SLO-Constrained Goodput](../待学概念/推理系统/SLO-Constrained%20Goodput.md) | Choose two limits, one on TTFT and one on TPOT. Increase the arrival rate until too few requests meet both. This measures the load each GPU can sustain at the required service level. |
| [Prefill-Decode Disaggregation](../待学概念/推理系统/Prefill-Decode%20Disaggregation.md) | Separate GPU pools can relieve contention. The saved delay must justify the KV handoff and any new queue at the receiving pool. |

**一次练习**　如果要求至少 90% 的请求两项同时达标，只有各自的达标率够不够？各有 95% 达标时，两个失败集合可能重合，也可能分别落在不同请求上。保留逐请求记录，就能算出实际比例。再打开上表的 Goodput 卡，给一组新的到达率划出能运行的区间。

## In English

A six-minute Bilibili video explains why the prompt and the next generated token need different work. A WeChat article on pretraining engineering asks what a GPU spends its time reading. The two meet when a server batches several short decode steps to reuse the same weights. The OSDI paper *Sarathi-Serve* introduces a wrinkle. A long prompt arriving in the middle of that batch can make other users wait. Its author’s [recorded talk](https://www.youtube.com/watch?v=S8rq3pYboZY) covers chunked prefill.

The fourth source is a rewritten conversation. Four later tokens arriving over 80 ms give an average of 20 ms per token, even if one gap lasted 65 ms. This is why the first gold node calls for inspecting individual arrivals. *DistServe* supplies a different test for a deployment decision. Replay the same traffic, count the requests meeting **both** latency limits, and include the cost of moving the cache before estimating what a split deployment gains. The three study cards above work through each decision.
