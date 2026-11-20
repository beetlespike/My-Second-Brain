# 计时一条流式回答 · Timing a streamed answer

一段系统学习讨论的公开改写。问题保留了客户端计时的口径，数字为本例重设。

**问**　请求发出后，第一个 token 在 120 ms 到达，第五个在 200 ms 到达。该报哪个延迟？

**答**　等开头花了 120 ms。接下来四个 token 共花 80 ms，平均每个 20 ms。

**问**　如果中间有一次明显卡顿呢？

**答**　后四次分别等 5、5、65、5 ms，平均值还是 20 ms。保留每次抵达的时间，就能从这 80 ms 里找出那次停顿。若客户端把多个 token 合成一块返回，得说明测到的是块间隔。

## English

**Q**　A client sees token one at 120 ms and token five at 200 ms. What latency should it report?

**A**　It waited 120 ms for the first token. The four later tokens took another 80 ms, or 20 ms each on average.

**Q**　Could someone still notice a pause?

**A**　Gaps of 5, 5, 65 and 5 ms have the same average. Individual arrival times reveal the 65 ms gap. If the client receives chunks containing several tokens, record that it measured gaps between chunks.
