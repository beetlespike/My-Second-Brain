---
type: concept
aliases: ["延迟约束下的有效服务率"]
tags: [ai-suggested, case-serving]
status: active
stage: working
学习状态: 待学
---

# SLO-Constrained Goodput

固定设备和请求分布，逐档增加到达率。逐条请求核对首 token 和后续输出两个门槛，再找出仍能让约定比例请求同时达标的最高负载。

Fix the GPU count, workload and latency targets. Increase [Request Arrival Rate](../../Concepts/推理系统/Request%20Arrival%20Rate.md) and measure the fraction of requests meeting both [TTFT](../../Concepts/推理系统/TTFT.md) and [TPOT](../../Concepts/推理系统/TPOT.md). DistServe reports the largest supported rate per GPU at a specified attainment target. Use joint per-request outcomes when two limits apply.

[DistServe: Disaggregating Prefill and Decoding for Goodput-optimized Large Language Model Serving](../../Papers/DistServe.md)

## 知识卡

### 正面

On one GPU, 2, 3 and 4 requests/s give 98%, 93% and 84% joint attainment. The target is 90%. What rate did the test demonstrate? / 单卡三档负载的联合达标率如上，哪一档得到验证？

### 简答

3 requests/s/GPU is the highest tested rate that passes. A rate between 3 and 4 needs another measurement. / 已测档位中每秒 3 个请求达标。要知道 3 和 4 之间的界限，还得在这个区间加测。
