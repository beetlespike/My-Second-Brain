---
type: concept
aliases: ["题目难度偏差"]
tags: [ai-suggested, case-rlvr]
status: active
stage: working
学习状态: 待学
---

# Question-Level Difficulty Bias

同题内的奖励方差也决定题目在更新中的相对权重。几乎全对或全错，与整组完全同分，是两个不同的边界情况。

After subtracting a [Group Baseline](../../Concepts/强化学习/Group%20Baseline.md), [Advantage Normalization](../../Concepts/强化学习/Advantage%20Normalization.md) divides by the reward standard deviation of that prompt’s sampled group. Rare outcomes in nearly uniform groups can get large weight. If every [reward](../../Concepts/强化学习/Verifiable%20Rewards.md) in a group is equal, every centered reward is zero.

[Understanding R1-Zero-Like Training: A Critical Perspective](../../Papers/Understanding%20R1-Zero-Like%20Training.md)

## 知识卡

### 正面

What signal remains in a group of eight failures after subtracting the group mean and dividing by a guarded standard deviation? / 八次全错的题还留下什么组内信号？

### 简答

Every centered reward is zero, so this group contributes no relative reward advantage. A rare success in a new group would change both its mean and its scale. / 八个中心化奖励都为零。若下一组多出一次成功，均值和缩放都会改变。
