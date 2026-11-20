---
type: concept
aliases: ["请求到达率"]
tags: [case-serving]
status: active
stage: working
---

# Request Arrival Rate

单位时间内送到服务端的请求数，包括进队等待的请求。相同的平均到达率可以伴随很不一样的突发流量。

Count requests offered to the service per unit time, including requests that have to queue. At the same mean rate a burst may produce a longer queue than evenly spaced arrivals. Replay the same arrivals when comparing [TTFT](TTFT.md) under two schedules.

[DistServe: Disaggregating Prefill and Decoding for Goodput-optimized Large Language Model Serving](../../Papers/DistServe.md)
