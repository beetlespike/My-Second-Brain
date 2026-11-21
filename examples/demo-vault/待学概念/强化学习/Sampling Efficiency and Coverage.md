---
type: concept
aliases: ["采样效率与解题覆盖"]
tags: [ai-suggested, case-rlvr]
status: active
stage: working
学习状态: 待学
---

# Sampling Efficiency and Coverage

单次成功率上升时，可以同时追问两件事：原先偶尔做对的题是否更常做对，以及同样多次尝试后是否多做对了其他题。逐题配对才能分清。

An increase at k = 1 can mean correct solutions became easier to sample on previously solvable questions. Compare [pass@k](../../Concepts/模型评测/pass@k.md) at several k, then use [Paired Evaluation](../../Concepts/研究方法/Paired%20Evaluation.md) to inspect per-question outcomes with matched [Sampling Temperature](../../Concepts/强化学习/Sampling%20Temperature.md) and [Generation Budget](../../Concepts/强化学习/Generation%20Budget.md). Finite samples give evidence about observed coverage.

[Does Reinforcement Learning Really Incentivize Reasoning Capacity in LLMs Beyond the Base Model?](../../Papers/RLVR%20at%20Large%20k.md)

## 知识卡

### 正面

Two policies each solve 60 of 100 tasks at k = 64. Can you conclude that they solve the same tasks? / 两个模型各有 60 题做对过，覆盖的是同一批题吗？

### 简答

Compare the per-task success sets, including gains and losses. Equal totals permit different sets. Even failure on all 64 attempts leaves a smaller success probability possible. / 要比对逐题集合。64 次都没采到也只能限定观察范围。
