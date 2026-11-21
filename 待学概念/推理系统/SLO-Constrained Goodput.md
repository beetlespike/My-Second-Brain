---
type: concept
aliases: ["延迟约束下的有效服务率"]
tags: [ai-suggested, case-serving]
status: active
stage: working
学习状态: 待学
---

# SLO-Constrained Goodput

线上服务卡不卡，看的不是极限能压出多少并发，而是在同时守住首字延迟（TTFT）和后续输出速度（TPOT）两个红线的前提下，每张 GPU 还能扛住多少请求速率。把负载一档档往上推、逐条请求核对两项是否**一起过线**，找到达标率刚滑出红线前的那一档，才是真实可用的单卡服务力。

Fix the hardware, prompt distribution, and both latency targets—[TTFT](../../Concepts/推理系统/TTFT.md) and [TPOT](../../Concepts/推理系统/TPOT.md)—then sweep [Request Arrival Rate](../../Concepts/推理系统/Request%20Arrival%20Rate.md) upward while grading **each request** on both limits together. DistServe defines per-GPU goodput as the highest load keeping joint attainment above your target floor.

[DistServe: Disaggregating Prefill and Decoding for Goodput-optimized Large Language Model Serving](../../Papers/DistServe.md)

## 知识卡

### 正面

在 90% 请求必须同时达标的红线下，单卡测到 `2 / 3 / 4 req/s` 时的联合达标率分别是 `98% / 93% / 84%`。这轮实测真正站得住的单卡容量上限报多少？ / With a 90% joint SLO floor, tested loads of 2, 3, and 4 req/s hit 98%, 93%, and 84% joint attainment. What per-GPU goodput is backed by this sweep?

### 简答

已实测的最高合格档是 3 req/s/GPU；4 req/s 已经跌破 90%，想更精细定位 3 到 4 之间的拐点，只能在这个区间补测。 / 3 req/s/GPU is the highest verified passing rate; pinpointing the knee between 3 and 4 requires extra runs inside that interval.
