---
type: moc
status: active
---

# 吞吐升上去了，为什么流式回答还会卡？

把更多并发塞进同一批 GPU，每秒生成的总 token 确实往上涨了，但正在等下一句的人反而觉得隔三岔五卡一下。要想看清卡在哪里、值不值得改架构，把这周啃下的四份材料摊开对一遍账：

| 材料 | 这一份把哪段卡点讲透了 |
| --- | --- |
| 月球大叔的 B 站视频《6分钟速通大模型KV Cache》 | 先把[预填充与解码](../Concepts/推理系统/Prefill%20and%20Decode.md)两段活彻底分开，讲清为什么后续每吐一个字都得靠复用 [KV 缓存](../Concepts/推理系统/KV%20Cache.md)省计算，以及并发一多显存就吃紧。[视频笔记](../Videos/KV%20Cache%20in%20Six%20Minutes.md) |
| 靳岩岩公众号文章《【AI架构原理】预训练工程师在干什么》 | 点出小批量解码的真正瓶颈在[显存带宽](../Concepts/推理系统/Memory%20Bandwidth.md)（每次搬整份权重只吐几个字，算得合批才摊得开）；vLLM 博客接着用 [PagedAttention](../Concepts/推理系统/PagedAttention.md) 解决了长短请求的缓存碎片。[公众号笔记](../Articles/The%20Pretraining%20Engineers%20Article.md) · [vLLM 作者文章](../Articles/vLLM%20on%20PagedAttention.md) |
| *Sarathi-Serve*（OSDI 2024） | 用上[连续合批](../Concepts/推理系统/Continuous%20Batching.md)以后，一条刚进来的长输入如果不做[分块预填充](../Concepts/推理系统/Chunked%20Prefill.md)，整批正在解码的老请求都得原地干等。[论文与演讲笔记](../Papers/Sarathi-Serve.md) |
| 那次查流式停顿的聊天记录 | 数字重设后依然很直观：首 token 120 ms（[TTFT](../Concepts/推理系统/TTFT.md)），后四个平均 20 ms（[TPOT](../Concepts/推理系统/TPOT.md)），但拆成 `5、5、65、5 ms` 后，平均值彻底掩盖了那一下 65 ms 的真实卡顿。[排查对话与笔记](../Chats/Timing%20a%20Stream.md) |

真到拍板部署策略的时候，必须先钉死现场的[输入长度分布](../Concepts/推理系统/Prompt%20Length%20Distribution.md)和[请求到达率](../Concepts/推理系统/Request%20Arrival%20Rate.md)。接着看 *DistServe* 的解法更干脆：把两个阶段拆到不同 GPU 池免得互相拖慢，可算净收益时一定要把每条请求的 KV 缓存通过[互连带宽](../Concepts/推理系统/Interconnect%20Bandwidth.md)送过去的时间、加上接收端新排队算回来。[DistServe 笔记](../Papers/DistServe.md)

## Three gaps in the serving map

| Suggested concept | What it connects |
| --- | --- |
| [Prefill-Decode Interference](../待学概念/推理系统/Prefill-Decode%20Interference.md) | Explains why a newly admitted long prompt freezes ongoing decodes; test by lining up token arrival timestamps against scheduler iterations under smaller chunk sizes. |
| [SLO-Constrained Goodput](../待学概念/推理系统/SLO-Constrained%20Goodput.md) | Stops counting raw throughput once either TTFT or TPOT breaks SLO—sweep arrival rates while measuring **joint** per-request attainment on each GPU. |
| [Prefill-Decode Disaggregation](../待学概念/推理系统/Prefill-Decode%20Disaggregation.md) | Separates contention by putting prefill and decode on distinct GPU pools, trading batch interference for KV transfer time across interconnect links. |

假设同一批 100 个请求里，首 token 延迟和后续 token 间隔各有 95 个达标。两边没过线的各有 5 个。如果恰好是同一批，就有 95 个同时达标。如果这两批完全错开，同时达标的还有 90 个。实际落在 90 到 95 之间的哪个数，要逐条对照请求记录才能知道。

## In English

Higher tokens/sec on paper often hides uneven streaming pauses on screen. Putting four sources together isolates the pipeline: a Bilibili explainer draws the line between prompt prefill and stateful decoding, an engineering essay traces why small-batch decode stalls on memory bandwidth, *Sarathi-Serve* shows how one unchunked prompt stalls every active decode alongside it (also in its [OSDI talk](https://www.youtube.com/watch?v=S8rq3pYboZY)), and our rewritten latency trace shows a clean 20 ms average TPOT concealing a 65 ms hitch. Moving forward with *DistServe* means checking **joint** TTFT + TPOT attainment per GPU after pricing the KV handoff across interconnect links.
