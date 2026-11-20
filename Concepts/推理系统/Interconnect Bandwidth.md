---
type: concept
aliases: ["设备间互连带宽"]
tags: [case-serving]
status: active
stage: working
---

# Interconnect Bandwidth

跨设备搬运 S 字节数据，若链路能持续提供 B 字节/秒，传输至少花 S/B 秒。与计算重叠的部分未必会完整出现在用户等待时间里。

For a cache of S bytes moved between devices over a link sustaining B bytes per second, S/B is a transfer-time lower bound. Contention, setup and overlap change the exposed delay. The amount of data comes from the [KV Cache](KV%20Cache.md). [Memory Bandwidth](Memory%20Bandwidth.md) applies to reads on the device itself.

[DistServe: Disaggregating Prefill and Decoding for Goodput-optimized Large Language Model Serving](../../Papers/DistServe.md)
