#!/usr/bin/env python3
"""
为 docs/ 下每个分区目录生成 index.md 列表页（从 frontmatter title）。

用法: python scripts/gen_index_pages.py [docs_dir]

行为：
  - 遍历 concepts/ entities/ comparisons/ 等子目录
  - 读取每个 .md 的 YAML frontmatter，提取 title（缺省用文件名）
  - 生成 <目录>/index.md：标题 + 按字母序的笔记链接列表
  - 已存在的 index.md 会被覆盖（每次同步后重生）
  - 顶层 index.md（首页）不动
"""
import sys
import re
from pathlib import Path

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
TITLE_RE = re.compile(r'^title:\s*["\']?(.*?)["\']?\s*$', re.MULTILINE)

# 要生成列表页的分区（排除顶级 index/log/SCHEMA 等散文件）
SECTIONS = ["concepts", "entities", "comparisons"]
SECTION_TITLES = {
    "concepts": "概念",
    "entities": "实体",
    "comparisons": "对比",
}


def read_title(md_path: Path) -> str:
    """从 frontmatter 读 title；失败则回退到文件名。"""
    try:
        text = md_path.read_text(encoding="utf-8")
    except Exception:
        return md_path.stem
    fm = FRONTMATTER_RE.match(text)
    if not fm:
        return md_path.stem
    m = TITLE_RE.search(fm.group(1))
    if not m:
        return md_path.stem
    title = m.group(1).strip().strip("\"'")
    return title or md_path.stem


def gen_index(docs_dir: Path, section: str) -> None:
    sec_dir = docs_dir / section
    if not sec_dir.is_dir():
        return
    title = SECTION_TITLES.get(section, section)
    lines = [f"# {title}", "", f"共 {sum(1 for _ in sec_dir.glob('*.md'))} 篇。", ""]
    notes = []
    for md in sorted(sec_dir.glob("*.md")):
        if md.name == "index.md":
            continue
        note_title = read_title(md)
        # wikilink 形式，roamlinks 会解析成正确链接
        notes.append((note_title, md.stem))
    notes.sort(key=lambda x: x[0])
    for note_title, stem in notes:
        lines.append(f"- [[{stem}|{note_title}]]")
    (sec_dir / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  ✓ {section}/index.md ({len(notes)} 篇)")


def main() -> None:
    docs_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("docs")
    if not docs_dir.is_dir():
        print(f"✗ docs 目录不存在: {docs_dir}", file=sys.stderr)
        sys.exit(1)
    print(f"生成列表页 ({docs_dir}):")
    for section in SECTIONS:
        gen_index(docs_dir, section)


if __name__ == "__main__":
    main()
