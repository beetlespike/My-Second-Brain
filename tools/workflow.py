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
NOTE_DIRS = ('Papers', 'Articles', 'Videos', 'Chats', 'Concepts', 'MOCs', '待学概念', 'Flashcards')
TYPES = dict(Papers='paper', Articles='article', Videos='video', Chats='chat', Concepts='concept', MOCs='moc', Flashcards='flashcard_set')
SUPPORT = ('README.md', 'README.en.md', 'LICENSE', 'AGENTS.md', 'THIRD-PARTY.md', '.gitignore', '.secondbrain.json', 'Guides', 'Prompts', 'tools', '.flashcards')
DEMO_SOURCES = ('assets/demo/教学字幕.vtt', 'assets/demo/文章原文.md')


def files_under(path):
    """只遍历实体文件，跳过运行状态、环境与版本历史。"""
    if path.is_file() and not path.is_symlink():
        return [path]
    skip = {'local', '.local', '.git', '.obsidian', '__pycache__', '.venv'}
    return [p for p in path.rglob('*') if p.is_file() and not p.is_symlink()
            and not skip.intersection(p.relative_to(path).parts)
            and not any(q.is_symlink() for q in p.parents if q != path.parent)]


def review_module(root):
    spec = importlib.util.spec_from_file_location('review_check', root / '.flashcards/review.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def initialize(source, destination, empty=False, *, demo=False):
    source, destination = source.resolve(), destination.resolve()
    if empty and demo:
        raise ValueError('请选择空白目录或示例原文')
    if destination == source or destination.is_relative_to(source):
        raise ValueError('请在项目之外选择独立目录，避免嵌套知识库')
    if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
        raise ValueError('目标目录必须为空，已有内容不会被覆盖')
    cfg = review_module(source).settings(source)
    note_dirs = tuple(dict.fromkeys(NOTE_DIRS + tuple(cfg['source_dirs'])))
    extra = ()
    if demo:
        for name in DEMO_SOURCES:
            path = source / name
            if not path.is_file() or path.resolve() != path:
                raise ValueError(f'缺少示例原文 {name}，请从完整模板运行 init --demo')
        extra = DEMO_SOURCES
    elif not empty:
        extra = note_dirs + ('assets',)
    selected = [(p, p.relative_to(source)) for name in SUPPORT + extra for p in files_under(source / name)]
    destination.mkdir(parents=True, exist_ok=True)
    try:
        for p, relative in selected:
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, target)
        if empty or demo:
            for name in note_dirs:
                (destination / name).mkdir(exist_ok=True)
            (destination / 'MOCs/知识库入口.md').write_text(
                '---\ntype: moc\nstatus: active\n---\n\n# 知识库入口\n\n'
                '把最近想弄懂的问题和相关笔记留在这里。主题多起来后，可以再加阅读路径。\n',
                encoding='utf-8')
            demo_zh = ('从 [教学字幕](assets/demo/教学字幕.vtt) 和 [短文](assets/demo/文章原文.md) 开始。'
                       '这两份是合成材料，可以按 [第一次使用](Guides/第一次使用.md) 试一遍。\n\n') if demo else ''
            demo_en = ('Start with the synthetic [transcript](assets/demo/教学字幕.vtt) and [article](assets/demo/文章原文.md). '
                       'Follow the [first-use guide](Guides/First-Run.md) to work through them.\n\n') if demo else ''
            (destination / 'README.md').write_text(
                '# My Second Brain\n\n简体中文 | [English](README.en.md) · [MIT](LICENSE)\n\n'
                f'{demo_zh}'
                '用 Obsidian 和 Codex 打开这个目录。给 Codex 一份材料和一个想弄懂的问题，参考 [整理材料](Prompts/整理材料.md) 把概念写入笔记。整理后从 [知识库入口](MOCs/知识库入口.md) 看这些概念怎样相连。\n\n'
                '再拿一份材料补充已有概念，或从已有笔记里找一个值得继续学的问题。带学、制卡和复习的做法见 [第一次使用](Guides/第一次使用.md)。\n\n'
                '[读取工具](Guides/来源与工具.md) · [本地命令](Guides/工具与扩展.md) · [定期整理](Guides/自动整理与维护.md)\n\n'
                '模板采用 [MIT 许可证](LICENSE)。第三方组件和导入的材料适用各自的许可。\n',
                encoding='utf-8')
            (destination / 'README.en.md').write_text(
                '# My Second Brain\n\n[简体中文](README.md) | English · [MIT](LICENSE)\n\n'
                f'{demo_en}'
                'Open this folder in Obsidian and Codex. Give Codex a source and a question, then use the [intake prompt](Prompts/整理材料.md) to write concept notes. Browse the resulting notes from the [knowledge index](MOCs/知识库入口.md).\n\n'
                'Bring in another source to add to those concepts, or look for a follow-up question in your existing notes. The [first-use guide](Guides/First-Run.md) walks through studying that question and turning it into a review card.\n\n'
                '[Reading tools](Guides/Sources-and-tools.md) · [Commands and settings](Guides/工具与扩展.md) · [Scheduled review](Guides/Automation.md)\n\n'
                'The template uses the [MIT License](LICENSE). Third-party components and materials you import retain their own licenses.\n',
                encoding='utf-8')
    except Exception:
        # 已写入的文件保留，便于核查失败原因；不会删除用户目录。
        raise
    return {'created': str(destination), 'example_notes': not (empty or demo)}


def prose(text):
    """链接检查跳过示例代码和隐藏的机器记录。"""
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    text = re.sub(r'^(`{3,}|~{3,}).*?^\1\s*$', '', text, flags=re.S | re.M)
    return re.sub(r'`[^`\n]*`', '', text)


def fields(text):
    if not text.startswith('---\n') or '\n---' not in text[4:]:
        return {}
    header = text.split('---', 2)[1]
    return {k: v.strip().strip('\"\'') for k, v in re.findall(r'^([\w_]+):[ \t]*([^\n]*)$', header, re.M)}


def check(root):
    root = root.resolve()
    module = review_module(root)
    cfg = module.settings(root)
    dirs = tuple(dict.fromkeys(NOTE_DIRS + tuple(cfg['source_dirs']) + ('Guides', 'Prompts', 'assets')))
    notes = [p for d in dirs for p in files_under(root / d) if p.suffix == '.md']
    notes += [root / name for name in ('README.md', 'README.en.md', 'AGENTS.md', 'THIRD-PARTY.md') if (root / name).exists()]
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
        links += [(m.group(1).strip('<>'), False) for m in re.finditer(r'!?\[[^\]\n]*\]\(([^)\n]+)\)', body)]
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
    return {'notes_checked': len(notes), 'errors': sorted(set(errors)), 'warnings': warnings}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    commands = parser.add_subparsers(dest='command', required=True)
    init = commands.add_parser('init', help='复制通用工具与可选示例知识到空目录')
    init.add_argument('destination', type=Path)
    start = init.add_mutually_exclusive_group()
    start.add_argument('--empty', action='store_true', help='只保留指南与工具，从自己的材料开始')
    start.add_argument('--demo', action='store_true', help='带上两份示例原文，从头练习整理')
    commands.add_parser('check', help='只读检查本地链接和来源属性')
    args = parser.parse_args()
    result = initialize(args.root, args.destination, args.empty, demo=args.demo) if args.command == 'init' else check(args.root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get('errors'):
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError) as exc:
        sys.exit(f'操作未完成：{exc}')
