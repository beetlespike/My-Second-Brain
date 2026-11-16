---
type: concept
aliases:
  - KL 散度
status: active
stage: working
---

# KL散度

按 p 遇到结果，却用 q 描述这些结果，与直接使用 p 相比，平均多付出多少对数损失？KL 散度衡量这个差额。左边的分布决定平均时的权重，因此顺序有意义。

## 从交叉熵减去熵

对同一事件空间上的离散分布，以 2 为对数底：

$$
D_{\mathrm{KL}}(p\Vert q)
=\sum_{i:p_i>0}p_i\log_2\frac{p_i}{q_i}
=H(p,q)-H(p).
$$

前一页[[Concepts/信息论/交叉熵|交叉熵]]的例子中，$p=(0.75,0.25)$、$q=(0.5,0.5)$，所以 KL 约为 $1-0.811=0.189$ bit。[相对熵的定义](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.entropy.html)

## 为什么不会是负数

先用自然对数证明，再除以正数 $\ln2$ 即可换成 bit。假设所有 $p_i>0$ 的位置都有 $q_i>0$，利用 $-\ln u\ge1-u$：

$$
\sum_{p_i>0}p_i\ln\frac{p_i}{q_i}
\ge \sum_{p_i>0}(p_i-q_i)
=1-\sum_{p_i>0}q_i
\ge0.
$$

等号要求两分布相同。若某处 p 为正而 q 为零，该项直接变为无穷；p 为零的项对这个方向的平均贡献为零。

## 为什么交换方向会不同

令 $p=(1,0)$、$q=(0.9,0.1)$。用自然对数时，$D_{\mathrm{KL}}(p\Vert q)=\ln(1/0.9)\approx0.1054$ nat。反过来，q 会遇到第二种结果，而 p 给它零概率，所以 $D_{\mathrm{KL}}(q\Vert p)=\infty$。

KL 不具备数学距离要求的对称性。写下公式前，先明确哪一侧提供观察频率、哪一侧提供预测概率。[[Concepts/信息论/信息熵|信息熵]]与交叉熵也需要区分这两个角色。

阅读路径：[[MOCs/信息与预测|信息与预测]]。
