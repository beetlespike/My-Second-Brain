"""Read optional attribution and glossary entries from a card."""

import json
import re


def study_comment(prose, first_heading):
    """Read the single-line JSON comment before the study card's first subsection."""
    metadata = None
    for number, line in prose:
        if not re.match(r'^\s*<!--\s*reading\s*:', line):
            continue
        if number >= first_heading:
            raise ValueError('reading 注释应在知识卡的第一个小节标题之前')
        if metadata is not None:
            raise ValueError('同一张知识卡内的 reading 注释重复')
        match = re.fullmatch(r'\s*<!--\s*reading\s*:\s*(.*?)\s*-->\s*', line)
        if not match:
            raise ValueError('reading 注释须在同一行写完：<!-- reading: {...} -->')
        try:
            metadata = json.loads(match[1])
        except ValueError as exc:
            raise ValueError(f'reading 注释中的 JSON 无效：{exc}') from exc
        if not isinstance(metadata, dict):
            raise ValueError('reading 注释需要 JSON 对象')
    return metadata or {}


def section_entries(lines):
    entries = []
    for number, line in lines:
        if not line.strip():
            continue
        match = re.fullmatch(r'\s*[-*]\s+([^:：]+?)\s*[:：]\s*(.*)', line)
        if not match:
            raise ValueError(f'术语小节第 {number + 1} 行需要「- 术语：定义」')
        entries.append({'term': match[1], 'definition': match[2]})
    if not entries:
        raise ValueError('术语小节需要至少一个词条')
    return entries


def reading_fields(metadata, section_lines):
    fields = {}
    if 'author' in metadata:
        if not isinstance(metadata['author'], str):
            raise ValueError('author 必须为字符串')
        fields['author'] = metadata['author'].strip()
    if section_lines is not None:
        if 'glossary' in metadata:
            raise ValueError('glossary 重复：元数据和术语小节只能使用一处')
        entries = section_entries(section_lines)
    elif 'glossary' in metadata:
        entries = metadata['glossary']
    else:
        return fields
    if not isinstance(entries, list):
        raise ValueError('glossary 必须为词条列表')

    glossary = []
    terms, ids = set(), set()
    for number, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            raise ValueError(f'glossary 第 {number} 个词条必须为对象')
        values = {'id': entry.get('term'), **entry}
        item = {}
        for key in ('term', 'definition', 'id'):
            value = values.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f'glossary 第 {number} 个词条的 {key} 需要非空字符串')
            item[key] = value.strip()
        term = item['term'].casefold()
        if term in terms or item['id'] in ids:
            raise ValueError(f"glossary 第 {number} 个词条的术语或 id 重复：{item['term']} ({item['id']})")
        terms.add(term)
        ids.add(item['id'])
        glossary.append(item)
    fields['glossary'] = glossary
    return fields
