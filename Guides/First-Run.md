# From your first source to your first review

Use the short article and transcript included in this repository to try the full process: organize sources, connect concepts, study a suggested topic, and review it. These are synthetic teaching materials. Work in a separate learning folder.

## Prepare a learning folder

In Codex, open the downloaded project and send:

> Read AGENTS.md and Guides/工具与扩展.md. Use the initialization tool to create an empty My-Learning folder beside this project. If that name already contains files, choose a new name. Keep the guides and tools, and copy assets/demo/文章原文.md and assets/demo/教学字幕.vtt from this project into assets/demo/ in the new folder. Leave out the existing notes, concepts, and cards. Tell me the full path when it is ready.

Open the new folder as a vault in Obsidian, and switch Codex to the same folder. Continue the following steps there. You can also start from an empty folder when you use your own materials later.

## Organize the sources and check shared concepts

> Follow Prompts/整理材料.md to organize assets/demo/文章原文.md and assets/demo/教学字幕.vtt. I want to understand why adding samples usually makes an estimate more stable. Read the article first, then the transcript. Record what you actually read, connect their concepts in one network, and update the knowledge index. Show which concepts both sources support and check for a missing explanation. Write the explanations in English.

Open `MOCs/知识库入口.md` in Obsidian. These materials cover the sample mean, standard error, and the relationship between sample size and precision. Follow the links: both source notes should lead to the relevant concepts, and the concept pages should point back to their sources. The video note should identify the transcript timestamps it covers.

The transcript contains text and timestamps. The note should say that no video images or audio were inspected. If a concept already has a page, new material should add to that page.

## Find a topic to study next

The intake step may already produce a suggestion. You can also ask:

> Follow Prompts/回顾与补学.md to review this concept network. Find one condition shared by these concepts that has not been explained yet. Write a study note with an explanation and example, and say which question it would help me answer. Show me the suggestion and wait for my choice before teaching it.

Both materials assume independent sampling and mention correlated samples without working through them. Correlated sampling is therefore one supported suggestion. If that note already exists, expand it. If Codex suggests another topic, check that it explains the specific relationship to the existing concepts.

The suggested page should contain material you can read and have links from the study index and related concepts. A title on a “learn later” list is not enough to begin a lesson.

## Choose a topic and answer the questions

> I choose correlated sampling (相关抽样). Follow Prompts/带学新概念.md and teach me in English, starting with duplicated observations. First check that I understand the sample mean. Explain the calculation, give me a variation, and wait for my answer.

Pause here and answer yourself. Say if a step is unclear. Codex should use your answer to decide what to explain next and check whether you can solve a variation.

Once you understand the topic, ask Codex to move it into the main concept network, update its incoming links and study index, and prepare review cards. Links should still open the page after it moves. Unresolved parts stay in the study area. An answer written by the AI does not count as your answer.

## Open the review page and save feedback

> Follow Prompts/每日复习.md to prepare a review of what I have just studied. Check the card sources, generate the review set, and give me the full path to the HTML file I can open in a browser. If there are no usable cards, explain why and address the material we have just worked through first.

Open the HTML file. Try answering, then flip the card. Expand the explanation and sources to check that the card matches the topic you studied. Choose a rating or add a written comment, then click “导出反馈文件” (export feedback file).

Give the downloaded JSON file to Codex and say:

> Save this feedback file and tell me how many entries were actually saved and how they affect later reviews. Check that it belongs to this learning folder and review set.

Feedback enters the review history after a successful import. Importing the same file again should report duplicates. Feedback from a different learning folder cannot be mixed in.

The first review set generated each day keeps its original content. Generating it again opens the same set; cards added afterward wait for a later set. Keep the database and dates intact. For your first complete run, follow the order above: study the topic, create cards, then generate the review set.

See the [card guide](Flashcard-Review.md) for card format and source checks, and the [tool guide](工具与扩展.md) for initialization and review commands. Those guides are in Chinese; Codex can explain them in English.
