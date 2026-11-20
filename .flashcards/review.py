#!/usr/bin/env python3
"""My Second Brain 卡片校验、每日选卡、快照与明确反馈的本地存储。"""

import argparse
from collections import Counter
from contextlib import closing
from datetime import date, datetime, timedelta
import hashlib
import html
import json
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
import uuid
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
INTERVALS = {"again": 1, "uncertain": 3, "familiar": 14}
DAILY_LIMIT = 10
NEW_LIMIT = 6
SOURCE_DIRS = {"Concepts", "MOCs", "Chats", "Papers", "Articles", "Videos"}
META = re.compile(r"<!-- card: (.*?) -->", re.S)


def dump(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def settings(root):
    """读取少量可选设置；目录与笔记内容保持普通文件。"""
    cfg = dict(timezone="Asia/Shanghai", daily_limit=DAILY_LIMIT, new_limit=NEW_LIMIT,
               concept_limit=2, interval_days=dict(INTERVALS), source_dirs=sorted(SOURCE_DIRS))
    path = root / '.secondbrain.json'
    if path.exists():
        data = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(data, dict) or set(data) - set(cfg):
            raise ValueError('配置包含未知字段，参见 Guides/工具与扩展.md')
        cfg.update(data)
    for key in ('daily_limit', 'new_limit', 'concept_limit'):
        if type(cfg[key]) is not int:
            raise ValueError('每日数量和概念上限必须是整数')
    if not (1 <= cfg['daily_limit'] <= 25 and 0 <= cfg['new_limit'] <= cfg['daily_limit'] and cfg['concept_limit'] >= 1):
        raise ValueError('每日上限应为 1–25，新卡上限不能超过每日上限')
    intervals = cfg['interval_days']
    if not isinstance(intervals, dict) or set(intervals) != set(INTERVALS) or any(type(v) is not int or v < 1 for v in intervals.values()):
        raise ValueError('三种反馈的间隔必须是正整数天数')
    dirs = cfg['source_dirs']
    if not isinstance(dirs, list) or not dirs or any(not isinstance(d, str) or not re.fullmatch(r'[^./\\\\][^/\\\\]*', d) or d in {'待学概念', 'Flashcards'} for d in dirs):
        raise ValueError('来源目录须为知识正文的顶层目录，待学概念和卡片不作来源')
    try:
        if cfg['timezone'] != 'local':
            ZoneInfo(cfg['timezone'])
    except (KeyError, ValueError, TypeError):
        raise ValueError('时区不可用，请检查 timezone 或安装 tzdata') from None
    return cfg


def today(timezone='Asia/Shanghai'):
    if timezone == 'local':
        return date.today().isoformat()
    return datetime.now(ZoneInfo(timezone)).date().isoformat()


def markdown_structure(text):
    """列出代码块之外的 Markdown 标题。"""
    lines = text.splitlines()
    headings, fence = [], None
    for i, line in enumerate(lines):
        marker = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
        if marker:
            run = marker[1]
            if fence is None:
                fence = run
            elif run[0] == fence[0] and len(run) >= len(fence):
                fence = None
            continue
        if fence is None and (m := re.match(r'^(#{1,6}) (.+?)\s*$', line)):
            headings.append((i, len(m[1]), m[2]))
    return lines, headings


def section(text, heading, *, required=True):
    """返回唯一的 Markdown 小节。可选小节缺失时返回空文本。"""
    lines, headings = markdown_structure(text)
    hits = [(i, level) for i, level, title in headings if title == heading]
    if not hits and not required:
        return ""
    if len(hits) != 1:
        raise ValueError(f"来源标题需要唯一匹配：{heading}，实际 {len(hits)} 处")
    start, level = hits[0]
    end = len(lines)
    for i, next_level, _ in headings:
        if i > start and next_level <= level:
            end = i
            break
    return "\n".join(lines[start:end]).strip()


def source_text(root, source):
    p = (root / source["path"]).resolve()
    if not p.is_relative_to(root.resolve()) or p.suffix != ".md":
        raise ValueError("来源必须是仓库内的 Markdown 文件")
    if p.relative_to(root.resolve()).parts[0] not in settings(root)['source_dirs']:
        raise ValueError("来源必须属于知识正文目录")
    return section(p.read_text(encoding="utf-8"), source["heading"])


def body_part(body, name, *, required=True):
    return section(body, name, required=required).partition("\n")[2].strip()


def read_discovery_card(root, relative):
    path = (root / relative).resolve()
    if path.suffix != '.md' or not path.is_relative_to(root / '待学概念'):
        raise ValueError('新概念卡须来自当前学习目录的「待学概念」Markdown 笔记')
    text = path.read_text(encoding='utf-8')
    _, headings = markdown_structure(text)
    title = next((title for _, level, title in headings if level == 1), path.stem)
    card = section(text, '知识卡')
    front = section(card, '正面').partition('\n')[2].strip()
    back = section(card, '简答').partition('\n')[2].strip()
    if not front or not back:
        raise ValueError(f'{path.name}：知识卡需要题目和简答')
    return {'path': path.relative_to(root).as_posix(), 'title': title, 'front': front, 'back': back}


def catalog(root):
    cards, errors = [], []
    seen, questions = set(), set()
    for p in sorted((root / "Flashcards").rglob("*.md")):
        if not p.resolve().is_relative_to(root.resolve()):
            errors.append('卡片文件不能指向学习目录之外')
            continue
        text = p.read_text(encoding="utf-8")
        if "type: flashcard_set\n" not in text:
            errors.append(f"{p.name}：缺少 type: flashcard_set")
            continue
        lines, headings = markdown_structure(text)
        starts = [(i, title) for i, level, title in headings if level == 2]
        if not starts:
            errors.append(f'{p.name}：需要二级标题和 <!-- card: {{...}} --> 卡片元数据')
        for start, title in starts:
            end = next((i for i, level, _ in headings if i > start and level <= 2), len(lines))
            block = '\n'.join(lines[start:end])
            matches = list(META.finditer(block))
            if len(matches) != 1:
                errors.append(f'{p.name}：{title} 需要一条 <!-- card: {{...}} --> 卡片元数据，实际 {len(matches)} 条')
                continue
            match = matches[0]
            try:
                c = json.loads(match[1])
                for key in ("id", "version", "status", "concept", "topic", "sources"):
                    if key not in c:
                        raise ValueError(f"缺少 {key}")
                if not re.fullmatch(r"sb-fc-[0-9]{4,}", c["id"]):
                    raise ValueError("卡片编号格式错误")
                if type(c["version"]) is not int or c["version"] < 1:
                    raise ValueError("版本必须是正整数")
                if c["status"] not in {"active", "paused", "retired"}:
                    raise ValueError("未知卡片状态")
                if c["id"] in seen:
                    raise ValueError(f"重复编号 {c['id']}")
                seen.add(c["id"])
                body = block[match.end():]
                c.update(front=body_part(body, "正面"), back=body_part(body, "简答"),
                         details=body_part(body, "展开", required=False), card_file=str(p.relative_to(root)))
                if not c["front"] or not c["back"] or not c["sources"]:
                    raise ValueError("正面、简答和来源均不能为空")
                key = re.sub(r"\s+", "", c["front"])
                if key in questions:
                    raise ValueError(f"重复问题：{c['front']}")
                questions.add(key)
                reasons = []
                for src in c["sources"]:
                    try:
                        if digest(source_text(root, src)) != src["sha256"]:
                            reasons.append(f"来源已变化：{src['path']}#{src['heading']}")
                    except (OSError, KeyError, ValueError) as exc:
                        reasons.append(f"来源不可用：{exc}")
                c["eligible"] = c["status"] == "active" and not reasons
                c["review_reasons"] = reasons
                cards.append(c)
            except (KeyError, ValueError, IndexError, TypeError) as exc:
                errors.append(f"{p.name}：{exc}")
    return cards, errors, []


def card_hash(c):
    return digest(dump({k: c[k] for k in ("id", "version", "concept", "topic", "front", "back", "details", "sources")}))


def connect(root, state_dir=None):
    folder = state_dir or root / ".flashcards/local"
    folder.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(folder / "review.sqlite3", timeout=30)
    db.row_factory = sqlite3.Row
    db.create_function('has_note', 1, lambda v: bool(v and v.strip()))
    db.executescript("""
        CREATE TABLE IF NOT EXISTS versions (
            card_id TEXT, version INTEGER, hash TEXT NOT NULL, payload TEXT NOT NULL,
            PRIMARY KEY(card_id, version));
        CREATE TABLE IF NOT EXISTS sessions (
            day TEXT PRIMARY KEY, payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS source_inventory (
            path TEXT PRIMARY KEY, hash TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS feedback (
            sequence INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT UNIQUE NOT NULL,
            day TEXT NOT NULL, card_id TEXT NOT NULL, version INTEGER NOT NULL,
            rating TEXT, note TEXT NOT NULL, received TEXT NOT NULL,
            applied INTEGER NOT NULL, payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS feedback_resolutions (
            sequence INTEGER PRIMARY KEY, handled TEXT NOT NULL, decision TEXT NOT NULL,
            target_id TEXT, target_version INTEGER);
        CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
    """)
    db.execute('INSERT OR IGNORE INTO metadata VALUES (?, ?)', ('workspace_id', str(uuid.uuid4())))
    db.commit()
    return db


def scan_sources(db, root):
    known = dict(db.execute("SELECT path, hash FROM source_inventory"))
    current = {str(p.relative_to(root)): digest(p.read_text(encoding="utf-8"))
               for directory in settings(root)['source_dirs'] for p in (root / directory).rglob("*.md")
               if p.resolve().is_relative_to(root.resolve())}
    return {"new": [p for p in current if p not in known],
            "changed": [p for p in current if p in known and current[p] != known[p]],
            "missing": [p for p in known if p not in current]}


def acknowledge_source(db, root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or path.relative_to(root.resolve()).parts[0] not in settings(root)['source_dirs'] or path.suffix != ".md":
        raise ValueError("处理记录必须指向知识正文")
    key = str(path.relative_to(root.resolve()))
    if path.exists():
        db.execute("INSERT OR REPLACE INTO source_inventory VALUES (?, ?)", (key, digest(path.read_text(encoding="utf-8"))))
    else:
        db.execute("DELETE FROM source_inventory WHERE path=?", (key,))


def register(db, cards):
    for c in cards:
        row = db.execute("SELECT hash FROM versions WHERE card_id=? AND version=?", (c["id"], c["version"])).fetchone()
        if row and row["hash"] != card_hash(c):
            raise ValueError(f"{c['id']} 内容已经修改，请递增 version")
        db.execute("INSERT OR IGNORE INTO versions VALUES (?, ?, ?, ?)",
                   (c["id"], c["version"], card_hash(c), dump(c)))


def make_session(db, cards, day, preferred_new=(), *, settings=None, allow_empty=False,
                 deliver=False, discovery=None, portal=False, discard_discovery=None):
    cfg = settings or dict(daily_limit=DAILY_LIMIT, new_limit=NEW_LIMIT, concept_limit=2,
                           interval_days=INTERVALS, timezone='Asia/Shanghai')
    date.fromisoformat(day)

    def finish(deck, reused):
        if deliver:
            db.execute("UPDATE metadata SET value=? WHERE key='agent_published_day'", (day,))
        if discovery is not None:
            remember_discovery(db, day, discovery)
        elif discard_discovery is not None:
            db.execute('DELETE FROM metadata WHERE key=? AND value=?', ('discovery:' + day, dump(discard_discovery)))
        if deck['cards'] or deliver or discovery is not None:
            db.commit()
        else:
            db.rollback()
        return deck, reused

    db.execute("BEGIN IMMEDIATE")
    try:
        if portal:
            from feedback_inbox import published_day
            issued = published_day(db)
            if issued is not None:
                row = db.execute("SELECT payload FROM sessions WHERE day=?", (issued,)).fetchone()
                deck = json.loads(row[0]) if row else {
                    'date': issued or day, 'timezone': cfg['timezone'], 'cards': [], 'new_count': 0, 'review_count': 0}
                if issued != day:
                    deck['awaiting_publication'] = day
                db.commit()
                return deck, True
        if deliver:
            from feedback_inbox import require_clear
            require_clear(db, day)
        register(db, cards)
        previous = db.execute("SELECT payload FROM sessions WHERE day=?", (day,)).fetchone()
        if previous:
            return finish(json.loads(previous["payload"]), True)
        if db.execute("SELECT 1 FROM sessions WHERE day>?", (day,)).fetchone():
            raise ValueError("不能在已有卡组之前补建历史卡组；请读取原快照")
        last, topics = {}, Counter()
        week = (date.fromisoformat(day) - timedelta(days=7)).isoformat()
        for row in db.execute("SELECT day, payload FROM sessions WHERE day<? ORDER BY day", (day,)):
            for c in json.loads(row["payload"])["cards"]:
                last[c["id"]] = row["day"]
                if row["day"] >= week:
                    topics[c["topic"]] += 1
        feedback = {}
        for row in db.execute("SELECT * FROM feedback WHERE applied=1 AND rating IS NOT NULL AND received<=? ORDER BY sequence", (day,)):
            feedback[(row["card_id"], row["version"])] = dict(row)
        new, old, priority = [], [], set()
        for c in cards:
            if not c["eligible"]:
                continue
            f = feedback.get((c["id"], c["version"]))
            if f:
                due = (date.fromisoformat(f["received"]) + timedelta(days=cfg['interval_days'][f["rating"]])).isoformat()
                if due > day:
                    continue
                if last.get(c["id"], "") < due:
                    priority.add(c["id"])
            (old if c["id"] in last else new).append(c)
        preferred_new = set(preferred_new)
        chosen, concepts = [], Counter()

        def take(pool, count, is_new):
            added = 0
            while added < count:
                available = [c for c in pool if concepts[c["concept"]] < cfg['concept_limit']]
                if not available:
                    break
                c = min(available, key=lambda c: (0 if c["id"] in priority else 1,
                            last.get(c["id"], "") if not is_new else "",
                            topics[c["topic"]], concepts[c["concept"]],
                            is_new and c["id"] not in preferred_new, c["id"]))
                pool.remove(c)
                chosen.append(dict(c, presentation="new" if is_new else "review", position=len(chosen) + 1))
                concepts[c["concept"]] += 1
                topics[c["topic"]] += 1
                added += 1
            return added

        new_count = take(new, cfg['new_limit'], True)
        review_limit = cfg['daily_limit'] - new_count
        take(old, review_limit, False)
        session = {"schema_version": 1, "date": day, "timezone": cfg.get('timezone', 'Asia/Shanghai'), "cards": chosen,
                   'limits': {key: cfg[key] for key in ('daily_limit', 'new_limit')},
                   'workspace_id': db.execute("SELECT value FROM metadata WHERE key='workspace_id'").fetchone()[0],
                   "new_count": sum(c["presentation"] == "new" for c in chosen),
                   "review_count": sum(c["presentation"] == "review" for c in chosen)}
        if not chosen:
            if allow_empty:
                return finish(session, False)
            raise ValueError("当天没有可用或到期的卡片；可等待下次复习，或检查来源与状态。")
        db.execute("INSERT INTO sessions VALUES (?, ?)", (day, dump(session)))
        return finish(session, False)
    except Exception:
        db.rollback()
        raise


def cards_for_feedback(root):
    # A partially edited card bank can still accept comments on issued snapshots.
    try:
        cards, errors, _ = catalog(root)
    except (OSError, UnicodeError):
        return []
    return [] if errors else cards


def save_feedback(db, cards, payload, received):
    date.fromisoformat(received)
    if not isinstance(payload, dict) or not isinstance(payload.get("session_date"), str):
        raise ValueError("请提供题组日期和反馈内容")
    day, batch = payload["session_date"], payload.get("batch_id")
    date.fromisoformat(day)
    if not isinstance(batch, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,160}", batch):
        raise ValueError("反馈批次编号无效")
    if day > received:
        raise ValueError("反馈接收日期不能早于卡组日期")
    entries = payload.get("entries")
    if not isinstance(entries, list) or not 1 <= len(entries) <= 26 or not all(isinstance(e, dict) for e in entries):
        raise ValueError("每批可以提交至多 25 张复习卡和一张待学卡")
    row = db.execute("SELECT payload FROM sessions WHERE day=?", (day,)).fetchone()
    session = json.loads(row['payload']) if row else {}
    study = {e['card_id'] for e in entries if isinstance(e.get('card_id'), str) and e['card_id'].startswith('study:')}
    if len(study) > 1 or len(entries) - len(study) > 25:
        raise ValueError('超出一次题组的反馈范围')
    if not session and not study:
        raise ValueError("找不到对应日期的卡组")
    workspace = session.get('workspace_id')
    if study:
        workspace = db.execute("SELECT value FROM metadata WHERE key='workspace_id'").fetchone()[0]
    if workspace and payload.get('workspace_id') != workspace:
        raise ValueError('反馈不属于当前学习目录，请使用原卡组导出的反馈')
    snapshot = {c["id"]: c for c in session.get("cards", [])}
    current = {c["id"]: c for c in cards}
    for cid in study:
        if not cid.startswith('study:' + day + ':') or not db.execute(
                'SELECT 1 FROM versions WHERE card_id=? AND version=1', (cid,)).fetchone():
            raise ValueError('找不到对应日期和版本的待学卡')
        snapshot[cid] = {'version': 1}
    count = duplicate = stale = 0
    db.execute("BEGIN IMMEDIATE")
    try:
        ids = set()
        for e in entries:
            cid, version = e.get("card_id"), e.get("version")
            if not isinstance(cid, str) or type(version) is not int:
                raise ValueError("需要有效的卡片编号和版本")
            if cid in ids:
                raise ValueError("同一批反馈中卡片重复")
            ids.add(cid)
            if cid not in snapshot or snapshot[cid]["version"] != version:
                raise ValueError(f"卡片与快照版本不匹配：{cid}")
            if "position" in e and e["position"] != snapshot[cid].get("position"):
                raise ValueError("卡片序号与编号不匹配")
            rating, note = e.get("rating"), e.get("note", "")
            if cid in study and rating is not None:
                raise ValueError('待学卡只接收文字留言')
            if rating is not None and (not isinstance(rating, str) or rating not in INTERVALS):
                raise ValueError("未知反馈选项")
            if not isinstance(note, str) or len(note) > 2000 or (rating is None and not note.strip()):
                raise ValueError("反馈需要一个评分或 1–2000 字符的说明")
            canonical = dump({"session_date": day, "card_id": cid, "version": version, "rating": rating, "note": note})
            eid = f"{batch}:{cid}"
            existing = db.execute("SELECT payload FROM feedback WHERE event_id=?", (eid,)).fetchone()
            if existing:
                if existing["payload"] != canonical:
                    raise ValueError("同一反馈编号包含不同内容，请使用新批次")
                duplicate += 1
                continue
            active = current.get(cid)
            applied = cid in study or bool(active and active["version"] == version and active["eligible"]
                                           and all(active.get(k) == snapshot[cid].get(k) for k in
                                                   ('front', 'back', 'details', 'sources', 'concept', 'topic')))
            db.execute("INSERT INTO feedback(event_id,day,card_id,version,rating,note,received,applied,payload) VALUES (?,?,?,?,?,?,?,?,?)",
                       (eid, day, cid, version, rating, note, received, int(applied), canonical))
            count += 1
            stale += not applied
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"saved": count, "duplicates": duplicate, "historical_only": stale}


def feedback_notes(root, state_dir=None):
    """读取最近保存的文字反馈及卡片原有版本。"""
    path = (state_dir or root / ".flashcards/local") / "review.sqlite3"
    if not path.exists():
        return []
    with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        db.row_factory = sqlite3.Row
        rows = db.execute("""
            SELECT f.day AS session_date, f.received, f.card_id, f.version, f.note, v.payload
            FROM feedback AS f
            LEFT JOIN versions AS v ON v.card_id = f.card_id AND v.version = f.version
            WHERE trim(f.note, char(9, 10, 13, 32)) <> ''
            ORDER BY f.received DESC, f.sequence DESC
            LIMIT 20
        """)
        notes = []
        for row in rows:
            entry = dict(row)
            card = json.loads(entry.pop("payload") or "{}")
            entry["question"] = card.get("front")
            entry["sources"] = [{"path": s["path"], "heading": s["heading"]} for s in card.get("sources", [])]
            notes.append(entry)
        return notes


def study_id(day, card):
    return 'study:' + day + ':' + digest(dump([card[k] for k in ('path', 'title', 'front', 'back')]))


def register_study(db, day, card):
    cid = study_id(day, card)
    context = {'kind': 'study', 'card_file': card['path'], 'front': card['front'], 'back': card['back'],
               'sources': [{'path': card['path'], 'heading': '知识卡'}]}
    db.execute('INSERT OR IGNORE INTO versions VALUES (?, 1, ?, ?)', (cid, cid, dump(context)))
    return cid


def remember_discovery(db, day, card):
    register_study(db, day, card)
    db.execute("INSERT OR REPLACE INTO metadata VALUES (?, ?)", ("discovery:" + day, dump(card)))


def selected_discovery(db, day):
    row = db.execute('SELECT value FROM metadata WHERE key=?', ('discovery:' + day,)).fetchone()
    return json.loads(row[0]) if row else None


def visible_cards(session, current, cfg):
    available = [c for c in session['cards'] if current.get(c['id'], {}).get('status') != 'retired']
    limits = session.get('limits', cfg)
    new = [c for c in available if c['presentation'] == 'new'][:limits['new_limit']]
    old = [c for c in available if c['presentation'] == 'review'][:limits['daily_limit'] - len(new)]
    return sorted(old + new, key=lambda c: c['position'])


def page_html(root, session, *, preview=False, standalone=True, discovery=None, saved_ids=None):
    assets = Path(__file__).parent if saved_ids is not None else root / ".flashcards"
    template = (assets / "viewer.html").read_text(encoding="utf-8")
    display = json.loads(dump(session))
    if preview:
        display["preview"] = True
    bank = cards_for_feedback(root) if saved_ids is not None else catalog(root)[0]
    current = {c["id"]: c for c in bank}
    display["cards"] = visible_cards(display, current, settings(root))
    display["omitted_count"] = len(session["cards"]) - len(display["cards"])
    if not display["cards"] and discovery is None and saved_ids is None:
        raise ValueError("当日卡组已全部退出复习范围，原快照仍可通过 show 查看")
    if discovery is not None:
        display['discovery'] = dict(discovery, feedback_id=study_id(session['date'], discovery))
    display["new_count"] = sum(c["presentation"] == "new" for c in display["cards"])
    display["review_count"] = sum(c["presentation"] == "review" for c in display["cards"])
    for c in display["cards"]:
        latest = current.get(c["id"])
        if not latest or not latest["eligible"] or latest["version"] != c["version"]:
            c["snapshot_warning"] = "来源或卡片已更新。这是当日快照，可查看原笔记核对。"
            if latest and latest["eligible"] and any(
                not (root / source["path"]).is_file() for source in c["sources"]
            ):
                c["sources"] = latest["sources"]
                c["snapshot_warning"] = "这里保留了当日的题目和答案。原笔记已移动，下方列出当前卡片可复查的章节。"
        for source in c['sources']:
            try:
                source['excerpt'] = source_text(root, source)[:8000]
            except (OSError, KeyError, ValueError):
                source['excerpt'] = ''
    display['vault_name'] = root.name
    if saved_ids is not None:
        display['saved_ids'] = saved_ids
    data = dump(display).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    root_id = "sb-flashcards-" + session["date"] + ("-revision" if preview else "")
    if session.get('workspace_id'):
        root_id += '-' + session['workspace_id'][:8]
    local_save = "null"
    if saved_ids is not None:
        local_save = (assets / "local-save.js").read_text(encoding="utf-8").strip()
    result = template.replace("__ROOT_ID__", root_id).replace("__LOCAL_SAVE__", local_save)
    if "__MATH_RENDERER__" in result:
        renderer = (assets / "vendor/katex-0.19.1.min.js").read_text(encoding="utf-8")
        renderer = re.sub(r"</script", r"<\\/script", renderer, flags=re.I)
        result = result.replace("__MATH_RENDERER__", "<script>" + renderer + "</script>")
    result = result.replace("__DECK_DATA__", data)
    if standalone:
        head = '<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        if saved_ids is not None:
            head += '<meta name="color-scheme" content="light dark"><style>body{margin:0;background:light-dark(#f3f6f8,#10161b)}</style>'
        title = html.escape(session['date']) + ' · My Second Brain 复习'
        result = '<!doctype html><html lang="zh-CN"><head>' + head + '<title>' + title + '</title></head><body>' + result + '</body></html>'
    if len(result.encode()) >= 1_000_000:
        raise ValueError("卡片界面超过 1 MB")
    return result, display


def render(root, session, output, *, preview=False, standalone=True, discovery=None):
    result, display = page_html(root, session, preview=preview, standalone=standalone, discovery=discovery)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=output.parent, suffix=".tmp", delete=False) as handle:
        handle.write(result)
        temporary = Path(handle.name)
    temporary.replace(output)
    return display


def print_result(value):
    ascii_output = not (sys.stdout.encoding or "utf-8").lower().startswith("utf")
    print(json.dumps(value, ensure_ascii=ascii_output, sort_keys=True))


def input_json(path):
    if str(path) == '-':
        return json.loads(sys.stdin.buffer.read().decode('utf-8-sig'))
    return json.loads(path.read_text(encoding='utf-8-sig'))


def main():
    import feedback_inbox as inbox

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--state-dir", type=Path)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("audit")
    sub.add_parser("scan")
    ack = sub.add_parser("ack-sources")
    ack.add_argument("paths", nargs="+")
    src = sub.add_parser("source-hash")
    src.add_argument("path"); src.add_argument("heading")
    ses = sub.add_parser("session")
    ses.add_argument("--date"); ses.add_argument("--output", type=Path)
    ses.add_argument('--fragment', action='store_true', help='输出可嵌入聊天的 HTML 片段')
    choice = ses.add_mutually_exclusive_group()
    choice.add_argument('--discovery', type=Path, metavar='NOTE', help='附上一篇待学笔记的新概念卡')
    choice.add_argument('--review-only', action='store_true', help='只展示复习题，省略当天已选的待学卡')
    ses.add_argument("--prefer-new", nargs="+", default=(), metavar="CARD_ID",
                     help="主题和概念覆盖相同时，优先首次推送这些卡片")
    live = sub.add_parser("today", help="打开或复用今日知识卡，本机浏览器直接保存反馈")
    live.add_argument("--no-open", action="store_true", help="仅返回入口地址，供助手和定时任务使用")
    live.add_argument("--chat-output", type=Path, metavar="FILE", help="同时生成同一题组的聊天交互片段")
    live.add_argument("--stop", action="store_true", help="关闭这个学习库的浏览器入口")
    live.add_argument("--discovery", type=Path, metavar="NOTE", help="为今天选定一篇待学笔记")
    live.add_argument("--prefer-new", nargs="+", default=(), metavar="CARD_ID")
    daily = sub.add_parser('daily', help='Agent 先取待处理留言，处理完再发布到私人网址')
    mode = daily.add_mutually_exclusive_group()
    mode.add_argument('--publish', action='store_true', help='核对反馈后发布今日题组，返回私人网址')
    mode.add_argument('--on-demand', action='store_true', help='恢复访问时选卡，保留全部复习记录')
    daily.add_argument('--after', type=int, default=0, metavar='ID', help='继续读取未处理留言')
    daily.add_argument('--discovery', type=Path, metavar='NOTE')
    daily.add_argument('--prefer-new', nargs='+', default=(), metavar='CARD_ID')
    daily.add_argument('--chat-output', type=Path, metavar='FILE', help='另外生成可交互的聊天片段')
    daily.set_defaults(stop=False, no_open=True)
    resolution = sub.add_parser('resolve', help='记录实际修订或答复，供用户在私人网址查看')
    resolution.add_argument('--input', type=Path, required=True, help='处理结果 JSON 文件，或 - 读取标准输入')
    feed = sub.add_parser("feedback")
    feed.add_argument("--input", type=Path, required=True, help="反馈文件，或用 - 从标准输入读取"); feed.add_argument("--received-date")
    sub.add_parser("notes", help="查看最近保存的卡片文字反馈")
    show = sub.add_parser("show")
    show.add_argument("--date")
    args = parser.parse_args()
    root = args.root.resolve()
    if args.command in ('daily', 'resolve'):
        with closing(connect(root, args.state_dir)) as db, db:
            day = today(settings(root)['timezone'])
            if args.command == 'resolve':
                print_result(inbox.resolve(db, root, input_json(args.input), day))
                return
            if args.after < 0 or (args.after and (args.publish or args.on_demand)):
                parser.error('--after 只用于继续读取待处理留言')
            if not args.publish and (args.discovery or args.prefer_new or args.chat_output):
                parser.error('发布选项需要 daily --publish')
            if args.on_demand:
                db.execute('DELETE FROM metadata WHERE key=?', (inbox.PUBLICATION,))
                print_result({'status': 'on_demand'})
                return
            brief = inbox.begin(db, day, args.after)
            if not args.publish or brief['pending_count']:
                print_result(brief)
                return
    if args.command in ('today', 'daily'):
        import today_server
        try:
            result = today_server.run(root, args, publish=args.command == 'daily')
        except inbox.PendingFeedback as exc:
            result = exc.report
        print_result(result)
        return
    if args.command == "notes":
        print_result(feedback_notes(root, args.state_dir))
        return
    cfg = settings(root)
    if hasattr(args, 'date') and args.date is None:
        args.date = today(cfg['timezone'])
    if args.command == 'feedback' and args.received_date is None:
        args.received_date = today(cfg['timezone'])
    if args.command == 'session' and args.output is None:
        args.output = (args.state_dir or root / '.flashcards/local') / 'views' / (args.date + '.html')
    if args.command == "source-hash":
        print(digest(source_text(root, {"path": args.path, "heading": args.heading})))
        return
    if args.command == 'feedback':
        with closing(connect(root, args.state_dir)) as db:
            print_result(save_feedback(db, cards_for_feedback(root), input_json(args.input), args.received_date))
        return
    discovery = read_discovery_card(root, args.discovery) if args.command == 'session' and args.discovery else None
    cards, errors, warnings = catalog(root)
    if args.command == "audit":
        print_result({"total": len(cards), "eligible": sum(c["eligible"] for c in cards),
                      "topics": dict(Counter(c["topic"] for c in cards)), "errors": errors, "warnings": warnings,
                      "needs_review": [{"id": c["id"], "reasons": c["review_reasons"]} for c in cards if c["review_reasons"]]})
        if errors:
            sys.exit(1)
        return
    if errors:
        raise ValueError("；".join(errors))
    with closing(connect(root, args.state_dir)) as db, db:
        if args.command == "scan":
            print_result(scan_sources(db, root))
        elif args.command == "ack-sources":
            for path in args.paths:
                acknowledge_source(db, root, path)
            print_result({"acknowledged": len(args.paths)})
        elif args.command == "session":
            if discovery is None and args.fragment and not args.review_only:
                discovery = selected_discovery(db, args.date)
            try:
                session, reused = make_session(db, cards, args.date, args.prefer_new, settings=cfg,
                                               allow_empty=discovery is not None, discovery=discovery,
                                               deliver=args.date == today(cfg['timezone']))
            except inbox.PendingFeedback as exc:
                print_result(exc.report)
                return
            display = render(root, session, args.output, standalone=not args.fragment, discovery=discovery)
            result = {"date": args.date, "count": len(display["cards"]), "new": display["new_count"],
                      "review": display["review_count"], "omitted": display["omitted_count"],
                      "reused": reused, "output": str(args.output.resolve())}
            if discovery is not None:
                result['discovery'] = discovery['path']
            print_result(result)
        elif args.command == "show":
            row = db.execute("SELECT payload FROM sessions WHERE day=?", (args.date,)).fetchone()
            if not row:
                raise ValueError("该日没有卡组")
            print_result(json.loads(row["payload"]))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, sqlite3.Error) as exc:
        print(f"卡片任务未完成：{exc}", file=sys.stderr)
        sys.exit(1)
