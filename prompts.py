from typing import List, Dict

def _fmt_hits(hits: List[Dict], label: str) -> str:
    if not hits:
        return ""
    out = [f"{label}:"]
    for h in hits:
        out.append(f"— {h['title']}: {h['snippet']} ({h['source']})")
    return "\n".join(out)

def TROUBLESHOOT_TEMPLATE(description: str, playbook: Dict, kb_hits: List[Dict], web_hits: List[Dict]) -> str:
    sections = [f"<b>Описание</b>: {description}"]
    if playbook:
        pb = [f"<b>{playbook.get('title','Плейбук')}</b>", "Сделать сейчас:"]
        pb += [f"  {i+1}) {s}" for i, s in enumerate(playbook.get("now", []))]
        if playbook.get("if_fail"):
            pb.append("Если не помогло:")
            pb += [f"  — {s}" for s in playbook["if_fail"]]
        if playbook.get("notes"):
            pb.append("Заметки:")
            pb += [f"  — {s}" for s in playbook["notes"]]
        sections.append("\n".join(pb))
    kb = _fmt_hits(kb_hits, "Из локальной базы")
    if kb: sections.append(kb)
    web = _fmt_hits(web_hits, "Из интернета")
    if web: sections.append(web)
    return "\n\n".join(sections)
