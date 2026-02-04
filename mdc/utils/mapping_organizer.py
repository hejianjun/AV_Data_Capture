import os
import shutil
import typing
from pathlib import Path

from mdc.utils.actor_mapping import get_actor_mapping, get_info_mapping, normalize_nfo_xml


def _maybe_windows_long_path(path: Path) -> Path:
    if os.name != "nt":
        return path
    try:
        p = str(path)
        if p.startswith("\\\\?\\"):
            return path
        lp = "\\\\?\\" + p
        return Path(lp) if Path(lp).exists() else path
    except Exception:
        return path


def _iter_movie_dirs(root: Path) -> typing.Iterator[Path]:
    root_str = str(root)
    for dirpath, dirnames, filenames in os.walk(root_str, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in ("translated", ".git", "__pycache__")]
        if os.path.basename(dirpath) == "failed":
            dirnames[:] = []
            continue

        has_nfo = any(name.lower().endswith(".nfo") for name in filenames)
        has_child_dir = any(d != "translated" for d in dirnames)
        if has_nfo and not has_child_dir:
            yield Path(dirpath)
            dirnames[:] = []


def _pick_main_nfo(movie_dir: Path) -> typing.Optional[Path]:
    try:
        for entry in os.scandir(str(movie_dir)):
            if entry.is_file() and entry.name.lower().endswith(".nfo"):
                return movie_dir / entry.name
    except Exception:
        return None
    return None


def process_movie_dir(movie_dir: Path, dry_run: bool = False, mapping_mode: int = 1) -> dict:
    movie_dir = _maybe_windows_long_path(movie_dir)
    main_nfo = _pick_main_nfo(movie_dir)
    if main_nfo is None:
        return {"movie_dir": str(movie_dir), "skipped": True, "reason": "no_nfo"}

    try:
        xml_content = main_nfo.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "movie_dir": str(movie_dir),
            "skipped": True,
            "reason": f"read_nfo_failed:{e}",
        }

    actor_mapping = get_actor_mapping(mapping_mode)
    info_mapping = get_info_mapping(mapping_mode)
    try:
        new_content, new_actors, modified, conflict = normalize_nfo_xml(
            xml_content, actor_mapping, info_mapping
        )
    except Exception as e:
        return {
            "movie_dir": str(movie_dir),
            "skipped": True,
            "reason": f"normalize_failed:{e}",
        }

    if conflict:
        return {
            "movie_dir": str(movie_dir),
            "skipped": True,
            "reason": "actor_mapping_conflict",
        }

    if modified:
        if not dry_run:
            try:
                main_nfo.write_text(new_content, encoding="utf-8")
            except Exception as e:
                return {
                    "movie_dir": str(movie_dir),
                    "skipped": True,
                    "reason": f"write_nfo_failed:{e}",
                }

    moved = False
    dest_dir: typing.Optional[Path] = None
    new_actor_dir = ",".join(new_actors) if new_actors else ""
    if new_actor_dir:
        original_actor_dir = movie_dir.parent.name
        if new_actor_dir != original_actor_dir:
            base_path = movie_dir.parent.parent
            dest_dir = base_path / new_actor_dir / movie_dir.name
            if os.name == "nt" and len(str(dest_dir)) >= 250:
                return {
                    "movie_dir": str(movie_dir),
                    "modified_nfo": modified,
                    "moved": False,
                    "skipped": True,
                    "reason": f"dest_path_too_long:{len(str(dest_dir))}",
                }
            if not dry_run:
                try:
                    dest_dir.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(movie_dir), str(dest_dir))
                    moved = True
                except Exception as e:
                    return {
                        "movie_dir": str(movie_dir),
                        "modified_nfo": modified,
                        "moved": False,
                        "skipped": True,
                        "reason": f"move_failed:{e}",
                    }

    return {
        "movie_dir": str(movie_dir),
        "modified_nfo": modified,
        "moved": moved,
        "dest_dir": str(dest_dir) if dest_dir else "",
        "new_actor_dir": new_actor_dir,
        "skipped": False,
    }


def run_mode4(base_path: str, dry_run: bool = False, mapping_mode: int = 1) -> dict:
    root = Path(base_path)
    if not root.exists():
        raise FileNotFoundError(f"根目录不存在: {base_path}")

    root = _maybe_windows_long_path(root)

    processed = 0
    skipped = 0
    modified = 0
    moved = 0
    conflicts = 0
    for movie_dir in _iter_movie_dirs(root):
        processed += 1
        result = process_movie_dir(movie_dir, dry_run=dry_run, mapping_mode=mapping_mode)
        if result.get("skipped"):
            skipped += 1
            if result.get("reason") == "actor_mapping_conflict":
                conflicts += 1
            print(f"[-]Skip: {result.get('movie_dir')} | {result.get('reason')}")
            continue

        if result.get("modified_nfo"):
            modified += 1
            print(f"[+]NFO updated: {Path(result['movie_dir']).name} | {Path(result['movie_dir']).parent}")
        if result.get("moved"):
            moved += 1
            print(f"[+]Moved: {result.get('movie_dir')} -> {result.get('dest_dir')}")
        elif result.get("new_actor_dir") and not dry_run:
            pass

    summary = {
        "processed": processed,
        "skipped": skipped,
        "conflicts": conflicts,
        "modified_nfo": modified,
        "moved": moved,
        "dry_run": dry_run,
        "base_path": str(root),
    }
    print(
        f"[*]Mode4 summary: processed={processed} skipped={skipped} conflicts={conflicts} modified_nfo={modified} moved={moved}"
    )
    return summary

