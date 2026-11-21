#!/usr/bin/env python3
"""建立独立学习目录，检查知识链接与来源属性。"""

import argparse
import importlib.util
import json
from pathlib import Path
import re
import shutil
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = Path('examples/demo-vault')
QUEUES = ('Study-Queue', '待学概念')
NOTE_DIRS = ('Papers', 'Articles', 'Videos', 'Chats', 'Concepts', 'MOCs', 'Flashcards') + QUEUES
TYPES = dict(Papers='paper', Articles='article', Videos='video', Chats='chat', Concepts='concept', MOCs='moc', Flashcards='flashcard_set')
HOMEPAGES = ('README.md', 'README.zh.md')
SUPPORT = ('LICENSE', 'AGENTS.md', 'AGENTS.zh.md', 'CLAUDE.md', 'THIRD-PARTY.md', '.gitignore', 'Guides', 'Prompts')
PROGRAM = ('tools', '.flashcards', 'Today.command', 'Today.cmd')
PORTAL_PAGES = set(HOMEPAGES) | {
    'MOCs/Knowledge-Index.md', 'MOCs/知识库入口.md',
    'Guides/First-Run.md', 'Guides/第一次使用.md', 'Guides/Flashcard-Review.en.md', 'Guides/Flashcard-Review.md',
    'AGENTS.md', 'AGENTS.zh.md',
    'Guides/Automation.md', 'Guides/自动整理与维护.md', 'Guides/Network-Notes.md', 'Guides/网络与主题地图.md',
    'Guides/Article-Notes.md', 'Guides/文章笔记.md', 'Guides/Video-Notes.md', 'Guides/视频笔记.md',
    'Guides/Paper-Notes.md', 'Guides/论文笔记.md', 'Guides/Chat-Notes.md', 'Guides/对话笔记.md',
    'Guides/Other-Sources.md', 'Guides/其他来源.md', 'Guides/Tools-and-Extensions.md', 'Guides/工具与扩展.md',
    'Guides/Sources-and-tools.md', 'Guides/来源与工具.md', 'Guides/Graph-View.md', 'Guides/关系图谱.md',
    'Prompts/intake.md', 'Prompts/整理材料.md', 'Prompts/daily-review.md', 'Prompts/每日复习.md',
    'Prompts/discover-concepts.md', 'Prompts/回顾与补学.md', 'Prompts/study-concept.md', 'Prompts/带学新概念.md',
}
DEMO_SOURCES = ('assets/demo/serving-sources.md', 'assets/demo/streaming-dialogue.md',
                'assets/demo/first-token.vtt', 'assets/demo/retrieval.md')


def files_under(path):
    """只遍历实体文件，跳过运行状态、环境与版本历史。"""
    skip = {'local', '.local', '.git', '.obsidian', '__pycache__', '.venv', '.cursor', 'AGENTS.override.md', 'GEMINI.md'}
    if path.is_symlink() or path.name in {'GEMINI.md', 'AGENTS.override.md', '.cursor'}:
        return []
    if path.is_file():
        return [path]
    return [p for p in path.rglob('*') if p.is_file() and not p.is_symlink()
            and not skip.intersection(p.relative_to(path).parts)
            and not any(q.is_symlink() for q in p.parents if q != path.parent)]


def review_module():
    spec = importlib.util.spec_from_file_location('review_check', ROOT / '.flashcards/review.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def homepages(root):
    if not (root / 'README.zh.md').is_file() and (root / 'README.en.md').is_file():
        return ('README.md', 'README.en.md')
    return HOMEPAGES


def bundled_example(root):
    example = root / EXAMPLE
    if (not (root / 'Flashcards').is_dir() and example.is_dir()
            and example.resolve() == example and (example / '.secondbrain.json').is_file()):
        return example
    return None


def initialize(source, destination, empty=False, *, demo=False):
    source, destination = source.resolve(), destination.resolve()
    if not source.is_dir():
        raise ValueError(f'找不到知识库目录 {source}')
    if empty and demo:
        raise ValueError('请选择空白目录或示例原文')
    if destination == source or destination.is_relative_to(source):
        raise ValueError('请在项目之外选择独立目录，避免嵌套知识库')
    if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
        raise ValueError('目标目录必须为空，已有内容不会被覆盖')
    example = bundled_example(source)
    data = example or source
    config_root = source if example and (empty or demo) else data
    guides = source if (source / 'tools/workflow.py').is_file() else ROOT
    cfg = review_module().settings(config_root)
    note_dirs = tuple(dict.fromkeys(NOTE_DIRS + tuple(cfg['source_dirs'])))
    extra = ()
    if demo:
        for name in DEMO_SOURCES:
            path = data / name
            if not path.is_file() or path.resolve() != path:
                raise ValueError(f'缺少示例原文 {name}，请从完整模板运行 init --demo')
        extra = DEMO_SOURCES
    elif not empty:
        extra = homepages(data) + note_dirs + ('assets',)
    selected = []
    for base, names in ((guides, SUPPORT), (ROOT, PROGRAM), (config_root, ('.secondbrain.json',)), (data, extra)):
        for name in names:
            selected.extend((p, p.relative_to(base)) for p in files_under(base / name))
    destination.mkdir(parents=True, exist_ok=True)
    for p, relative in selected:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, target)
        if relative == Path('Today.command') and sys.platform != 'win32':
            target.chmod(target.stat().st_mode | 0o111)
    for name in note_dirs:
        if empty or demo or name not in QUEUES or (data / name).is_dir():
            (destination / name).mkdir(exist_ok=True)
    if empty or demo or not (destination / 'README.md').exists():
        write_starter_pages(destination, demo, populated=not (empty or demo))
    return {'created': str(destination), 'example_notes': not (empty or demo)}


def write_starter_pages(destination, demo, *, populated=False):
    demo_en = 'You can also practise with the [four sources on LLM serving](assets/demo/serving-sources.md).\n\n' if demo else ''
    demo_zh = '想先练习一次，可以从[推理服务的四份材料](assets/demo/serving-sources.md)里选一份。\n\n' if demo else ''
    intake = 'Prompts/intake.md' if (destination / 'Prompts/intake.md').is_file() else 'Prompts/整理材料.md'
    if populated:
        intro_en = 'Browse the notes already in this vault or add a source you have studied.'
        intro_zh = '可以浏览库中已有的笔记，也可以加入自己学过的材料。'
        cards_en = 'Ask your assistant, “Open today’s cards.”'
        cards_zh = '可以对助手说「打开今日知识卡」。'
    else:
        intro_en = 'Start with one source you have studied.'
        intro_zh = '从一份自己学过的材料开始。'
        cards_en = 'Your vault starts with zero cards. Once you have notes, ask your assistant, “Make review cards from these notes and open today’s deck.”'
        cards_zh = '新库有 0 张复习卡。写好笔记后，可以对助手说「按这些笔记做卡，打开今日知识卡」。'
    (destination / 'README.md').write_text(
        '# My Second Brain\n\nEnglish · [简体中文](README.zh.md)\n\n'
        f'{intro_en} Open this folder with an AI assistant that can read and write local files and run commands. '
        f'Give it the link or saved file and ask it to follow the [intake prompt]({intake}). '
        'You can find maps of related concepts in the [knowledge index](MOCs/Knowledge-Index.md).\n\n'
        f'{demo_en}'
        f'{cards_en} '
        'Bookmark the fixed local address it opens. If you want a fresh deck each day, ask your assistant to set up the '
        '[daily review task](Guides/Automation.md) once. You can then review at the same bookmark. '
        'To open the page yourself or restart it after a reboot, use `Today.command` on macOS, `sh Today.command` on Linux, or `Today.cmd` on Windows.\n\n'
        'Your notes are Markdown files you can open in any editor. Ratings and comments are saved in this vault’s local database. '
        'With a cloud assistant, what reaches the service depends on the tool, its permissions, and the material included in the conversation.\n\n'
        '[First use](Guides/First-Run.md) · [Today’s Cards](Guides/First-Run.md#todays-cards) · [MIT license](LICENSE)\n',
        encoding='utf-8')
    (destination / 'README.zh.md').write_text(
        '# My Second Brain\n\n[English](README.md) · 简体中文\n\n'
        f'{intro_zh}用能读写本地文件、运行命令的 AI 助手打开这个目录，把材料的链接或文件交给它，请它按[整理提示](Prompts/整理材料.md)记下你学过的概念。'
        '从[知识库入口](MOCs/知识库入口.md)可以找到把相关概念串起来的主题地图。\n\n'
        f'{demo_zh}'
        f'{cards_zh}把打开的本机固定网址存为书签。想每天收到新题组，可以请助手一次设好[每日复习任务](Guides/自动整理与维护.md)，以后进同一个书签就能复习。'
        '自己打开页面或电脑重启后重新启动时，macOS 双击 `Today.command`，Linux 运行 `sh Today.command`，Windows 双击 `Today.cmd`。\n\n'
        '笔记以 Markdown 文件保存在这个目录里，用任意文本编辑器都能打开。评分和留言存入本库的本地数据库。使用云端助手时，哪些材料会发送给服务商，取决于所用工具、它的权限和对话中包含的内容。\n\n'
        '[第一次使用](Guides/第一次使用.md) · [今日知识卡](Guides/第一次使用.md#今日知识卡) · [MIT 许可](LICENSE)\n',
        encoding='utf-8')
    frontmatter = '---\ntype: moc\nstatus: active\n---\n\n'
    english_index = destination / 'MOCs/Knowledge-Index.md'
    if not english_index.exists():
        english_index.write_text(
            frontmatter + '# Knowledge Index\n\n[简体中文](知识库入口.md)\n\n'
            'When several notes help answer the same question, link them in a topic map and add the map here. '
            'A concept can appear in more than one map.\n\n[Home](../README.md)\n',
            encoding='utf-8')
    chinese_index = destination / 'MOCs/知识库入口.md'
    if not chinese_index.exists():
        chinese_index.write_text(
            frontmatter + '# 知识库入口\n\n[English](Knowledge-Index.md)\n\n'
            '当几篇笔记能一起回答一个问题时，可以把它们连成一张主题地图，再把地图列在这里。同一个概念也可以出现在几张地图里。\n\n'
            '[首页](../README.zh.md)\n',
            encoding='utf-8')


def prose(text):
    """链接检查跳过示例代码和隐藏的机器记录。"""
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    text = re.sub(r'^(`{3,}|~{3,}).*?^\1\s*$', '', text, flags=re.S | re.M)
    return re.sub(r'`[^`\n]*`', '', text)


def fields(text):
    frontmatter = re.match(r'\A---[ \t]*\n(.*?)^---[ \t]*$', text, re.M | re.S)
    if not frontmatter:
        return {}
    header = frontmatter[1]
    return {k: v.strip().strip('\"\'') for k, v in re.findall(r'^([\w_]+):[ \t]*([^\n]*)$', header, re.M)}


def heading_anchors(module, text):
    """列出门户文档中标题的章节链接及显式 HTML 锚点。"""
    anchors = set()
    _, headings = module.markdown_structure(text)
    for _, _, title in headings:
        base = re.sub(r'[^\w -]', '', title.lower()).replace(' ', '-')
        anchor = base
        suffix = 1
        while anchor in anchors:
            anchor = f'{base}-{suffix}'
            suffix += 1
        anchors.add(anchor)
    html_anchor = r"""<[A-Za-z][^<>]*?\s(?:id|name)\s*=\s*(["'])([^"'<>]*)\1"""
    anchors.update(match[2] for match in re.finditer(html_anchor, prose(text), re.I))
    return anchors


def inline_targets(text):
    """按正文顺序读取 Markdown 链接、图片和 HTML img 的 src。"""
    for match in re.finditer(r'(?P<img><img\b[^>]*>)|(?P<kind>!?)\[[^\]\n]*\]\((?P<url>[^)\n]+)\)', text, re.I):
        if match['img']:
            src = re.search(r"""\ssrc\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))""", match['img'], re.I)
            if src:
                yield '!', next(value for value in src.groups() if value is not None)
        else:
            yield match['kind'], match['url'].strip('<>')


def check(root):
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f'找不到知识库目录 {root}')
    module = review_module()
    example = bundled_example(root)
    result = check_vault(root, module, distribution=example is not None)
    if example:
        sample = check_vault(example, module)
        result['notes_checked'] += sample['notes_checked']
        for key in ('errors', 'warnings'):
            result[key].extend(f'{EXAMPLE.as_posix()}/{message}' for message in sample[key])
    return result


def check_vault(root, module, *, distribution=False):
    cfg = module.settings(root)
    dirs = tuple(dict.fromkeys(NOTE_DIRS + tuple(cfg['source_dirs']) + ('Guides', 'Prompts', 'assets')))
    notes = [p for d in dirs for p in files_under(root / d) if p.suffix == '.md']
    home = homepages(root)
    notes += [root / name for name in home + ('AGENTS.md', 'AGENTS.zh.md', 'CLAUDE.md', 'THIRD-PARTY.md') if (root / name).is_file()]
    portal = {root / name for name in PORTAL_PAGES} if (root / 'README.zh.md').is_file() else set()
    by_stem = {}
    for p in notes:
        by_stem.setdefault(p.stem, []).append(p)
    errors, warnings = [], []
    for p in notes:
        relative = p.relative_to(root)
        text = p.read_text(encoding='utf-8')
        fm = fields(text)
        kind = relative.parts[0]
        if kind in TYPES and fm.get('type') != TYPES[kind]:
            errors.append(f'{relative}：type 应为 {TYPES[kind]}')
        if kind in cfg['source_dirs'] and kind not in TYPES and not fm.get('type'):
            errors.append(f'{relative}：需要 type 说明资料类型')
        if kind in cfg['source_dirs'] and fm.get('type') not in ('concept', 'moc'):
            if not (fm.get('source_url') or fm.get('source_path')):
                errors.append(f'{relative}：需要 source_url 或仓库相对 source_path')
            if not fm.get('evidence_status'):
                errors.append(f'{relative}：需要 evidence_status')
            if fm.get('source_path'):
                target = (root / fm['source_path']).resolve()
                if not target.is_relative_to(root) or not target.is_file():
                    errors.append(f'{relative}：source_path 无法在当前目录内定位')
        body = prose(text)
        links = [(m.group(1).split('|')[0], True) for m in re.finditer(r'!?\[\[([^\]]+)\]\]', body)]
        links += [(url, False) for _, url in inline_targets(body)]
        for value, wiki in links:
            if not value or re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:', value):
                continue
            filepart, _, anchor = value.partition('#')
            filepart = unquote(filepart)
            if not filepart:
                hits = [p]
            elif wiki and '/' not in filepart:
                hits = by_stem.get(Path(filepart).stem, [])
            else:
                candidate = (root if wiki else p.parent) / filepart
                if not candidate.is_file() and not candidate.suffix:
                    candidate = candidate.with_suffix('.md')
                resolved = candidate.resolve()
                hits = [resolved] if resolved.is_relative_to(root) and resolved.is_file() else []
            if len(hits) != 1:
                errors.append(f'{relative}：链接需要唯一目标 {value}（{len(hits)} 处）')
            elif anchor and hits[0].suffix == '.md' and wiki and not anchor.startswith('^'):
                try:
                    module.section(hits[0].read_text(encoding='utf-8'), anchor)
                except ValueError:
                    errors.append(f'{relative}：章节无法唯一定位 {value}')
            elif (anchor and not wiki and not anchor.startswith('^') and hits[0].suffix == '.md'
                  and p in portal and (distribution or hits[0] in portal)):
                if unquote(anchor) not in heading_anchors(module, hits[0].read_text(encoding='utf-8')):
                    errors.append(f'{relative}：找不到章节 {value}')
    return {'notes_checked': len(notes), 'errors': sorted(set(errors)), 'warnings': warnings}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    commands = parser.add_subparsers(dest='command', required=True)
    init = commands.add_parser('init', help='复制通用工具与可选示例知识到空目录')
    init.add_argument('destination', type=Path)
    start = init.add_mutually_exclusive_group()
    start.add_argument('--empty', action='store_true', help='只保留指南与工具，从自己的材料开始')
    start.add_argument('--demo', action='store_true', help='带上示例来源和本地练习材料，从链接开始整理')
    commands.add_parser('check', help='只读检查本地链接和来源属性')
    args = parser.parse_args()
    result = initialize(args.root, args.destination, args.empty, demo=args.demo) if args.command == 'init' else check(args.root)
    ascii_output = not (sys.stdout.encoding or 'utf-8').lower().startswith('utf')
    print(json.dumps(result, ensure_ascii=ascii_output, indent=2))
    if result.get('errors'):
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError) as exc:
        sys.exit(f'操作未完成：{exc}')
