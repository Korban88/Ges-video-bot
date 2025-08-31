# prompts.py
from typing import List, Dict
import html

def _esc(s: str) -> str:
    return html.escape(s or "", quote=False)

def _fmt_hits_local(hits: List[Dict]) -> str:
    if not hits:
        return ""
    lines = ["<b>Из локальной базы</b>:"]
    for h in hits:
        title = _esc(h.get("title", ""))
        snip = _esc(h.get("snippet", ""))[:600]
        src = _esc(h.get("source", ""))
        lines.append(f"• <b>{title}</b>\n{snip}\n— {src}")
    return "\n".join(lines)

def _fmt_hits_web(hits: List[Dict]) -> str:
    if not hits:
        return ""
    lines = ["<b>Из интернета</b>:"]
    for h in hits:
        title = _esc(h.get("title", ""))
        snip = _esc(h.get("snippet", ""))[:700]
        url = _esc(h.get("url", ""))
        lines.append(f"• <b>{title}</b>\n{snip}\n{url}")
    return "\n".join(lines)

def TROUBLESHOOT_TEMPLATE(description: str, playbook: Dict, kb_hits: List[Dict], web_hits: List[Dict]) -> str:
    parts = [f"<b>Описание</b>: {_esc(description)}"]

    if playbook:
        now_steps = "\n".join([f"  {i+1}) {_esc(s)}" for i, s in enumerate(playbook.get('now', []))])
        if_fail = "\n".join([f"  — {_esc(s)}" for s in playbook.get('if_fail', [])]) if playbook.get('if_fail') else ""
        notes = "\n".join([f"  — {_esc(s)}" for s in playbook.get('notes', [])]) if playbook.get('notes') else ""
        block = [f"<b>{_esc(playbook.get('title','Плейбук'))}</b>",
                 "Сделать сейчас:", now_steps]
        if if_fail:
            block += ["Если не помогло:", if_fail]
        if notes:
            block += ["Заметки:", notes]
        parts.append("\n".join(block))
    else:
        parts.append("Подходящий плейбук не найден — перехожу к поиску.")

    kb = _fmt_hits_local(kb_hits)
    if kb:
        parts.append(kb)
    web = _fmt_hits_web(web_hits)
    if web:
        parts.append(web)

    return "\n\n".join([p for p in parts if p.strip()])
