from __future__ import annotations

import json
import posixpath
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).parent.resolve()
CONTENT_DIR = ROOT / "content"
TEMPLATE_DIR = ROOT / "templates"
ASSETS_DIR = ROOT / "assets"
PUBLIC_DIR = ROOT / "public"
DIST_DIR = ROOT / "dist"
CONFIG_PATH = ROOT / "site_config.yml"


@dataclass
class Page:
    source: Path
    rel_source: Path
    output_rel: Path
    language: str
    language_url: str
    title: str
    description: str
    section: str
    order: int
    tags: list[str]
    html: str
    text: str

    @property
    def url(self) -> str:
        return self.output_rel.as_posix()


def read_config() -> dict[str, Any]:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def parse_frontmatter(raw: str) -> tuple[dict[str, Any], str]:
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            meta = yaml.safe_load(parts[1]) or {}
            return meta, parts[2].lstrip()
    return {}, raw


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s-]+", "-", text)
    return text or "page"


def output_path_for(rel: Path) -> Path:
    if rel.name == "index.md":
        return rel.with_suffix(".html")
    return rel.with_suffix(".html")


def first_heading(markdown_text: str, fallback: str) -> str:
    for line in markdown_text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def extract_plain_text(md: str) -> str:
    text = re.sub(r"```.*?```", " ", md, flags=re.S)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"!\[[^\]]*\]\([^\)]*\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]*\)", r"\1", text)
    text = re.sub(r"[#>*_\-|]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def render_markdown(md: str) -> str:
    return markdown.markdown(
        md,
        extensions=[
            "extra",
            "toc",
            "tables",
            "fenced_code",
            "codehilite",
            "sane_lists",
        ],
        extension_configs={
            "codehilite": {"guess_lang": False, "noclasses": True},
            "toc": {"permalink": True},
        },
    )


def load_pages() -> list[Page]:
    pages: list[Page] = []
    for path in sorted(CONTENT_DIR.rglob("*.md")):
        rel = path.relative_to(CONTENT_DIR)
        language = "vi" if rel.parts[0] == "vi" else "en"
        content_rel = Path(*rel.parts[1:]) if language == "vi" else rel
        raw = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(raw)
        section = content_rel.parts[0] if len(content_rel.parts) > 1 else "home"
        title = str(meta.get("title") or first_heading(body, path.stem.replace("-", " ").title()))
        description = str(meta.get("description") or "")
        order = int(meta.get("order") or 999)
        tags = meta.get("tags") or []
        if isinstance(tags, str):
            tags = [tags]
        content_output = output_path_for(content_rel)
        output_rel = Path("vi") / content_output if language == "vi" else content_output
        language_url = content_output.as_posix() if language == "vi" else (Path("vi") / content_output).as_posix()
        pages.append(
            Page(
                source=path,
                rel_source=content_rel,
                output_rel=output_rel,
                language=language,
                language_url=language_url,
                title=title,
                description=description,
                section=section,
                order=order,
                tags=list(tags),
                html=render_markdown(body),
                text=extract_plain_text(body),
            )
        )
    return sorted(pages, key=lambda p: (p.section, p.order, p.rel_source.as_posix()))


def make_sidebar(pages: list[Page], current: Page) -> str:
    grouped: dict[str, list[Page]] = {}
    for p in pages:
        if p.language != current.language:
            continue
        grouped.setdefault(p.section, []).append(p)

    labels = {
        "en": {"home": "Start", "roadmap": "Roadmap", "skills": "Skills", "projects": "Projects"},
        "vi": {"home": "Bắt đầu", "roadmap": "Lộ trình", "skills": "Kỹ năng", "projects": "Dự án"},
    }
    section_labels = labels[current.language]
    order = ["home", "roadmap", "skills", "projects"]
    html_parts: list[str] = []
    for section in order + [s for s in grouped if s not in order]:
        if section not in grouped:
            continue
        html_parts.append(f'<div class="nav-section">{section_labels.get(section, section.title())}</div>')
        for p in sorted(grouped[section], key=lambda x: (x.order, x.rel_source.as_posix())):
            active = " active" if p.output_rel == current.output_rel else ""
            depth = len(p.rel_source.parts) - 1
            indent = "" if depth <= 1 else f"padding-left: {10 + depth * 10}px;"
            html_parts.append(f'<a class="nav-link{active}" style="{indent}" href="{root_prefix_for(current)}{p.url}">{p.title}</a>')
    return "\n".join(html_parts)


def root_prefix_for(page: Page) -> str:
    depth = len(page.output_rel.parts) - 1
    return "../" * depth


def copy_static() -> None:
    if ASSETS_DIR.exists():
        shutil.copytree(ASSETS_DIR, DIST_DIR / "assets", dirs_exist_ok=True)
    if PUBLIC_DIR.exists():
        shutil.copytree(PUBLIC_DIR, DIST_DIR, dirs_exist_ok=True)


def build() -> None:
    site = read_config()
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True)
    copy_static()

    pages = load_pages()
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("base.html")

    for page in pages:
        output_path = DIST_DIR / page.output_rel
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            template.render(
                site=site,
                title=page.title,
                description=page.description,
                content=page.html,
                sidebar=make_sidebar(pages, page),
                root_prefix=root_prefix_for(page),
                language=page.language,
                language_url=f"{root_prefix_for(page)}{page.language_url}",
                home_url=posixpath.relpath(
                    (Path("vi") if page.language == "vi" else Path()) / "index.html",
                    page.output_rel.parent.as_posix() or ".",
                ),
                language_label="English" if page.language == "vi" else "Tiếng Việt",
                site_name=site.get("site_name_vi", site["site_name"]) if page.language == "vi" else site["site_name"],
                search_placeholder="Tìm bài học..." if page.language == "vi" else "Search lessons...",
                theme_toggle="Đổi giao diện" if page.language == "vi" else "Toggle theme",
                meta_label="Markdown · HTML tĩnh · Python" if page.language == "vi" else "Markdown-first · Static HTML · Python build",
            ),
            encoding="utf-8",
        )

    search_index = [
        {
            "title": p.title,
            "description": p.description,
            "section": p.section,
            "language": p.language,
            "tags": p.tags,
            "url": p.url,
            "text": p.text[:5000],
        }
        for p in pages
    ]
    (DIST_DIR / "search-index.json").write_text(json.dumps(search_index, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Built {len(pages)} pages into {DIST_DIR}")


if __name__ == "__main__":
    build()
