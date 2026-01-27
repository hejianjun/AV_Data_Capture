from pathlib import Path

from mdc.file.file_utils import mode3_should_execute_by_nfo


def _write_nfo(path: Path, title, outline, plot=None, year="2023"):
    title_xml = f"<title>{title}</title>" if title is not None else ""
    outline_xml = f"<outline>{outline}</outline>" if outline is not None else ""
    plot_xml = f"<plot>{plot}</plot>" if plot is not None else ""
    year_xml = f"<year>{year}</year>" if year is not None else ""
    path.write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<movie>{title_xml}{outline_xml}{plot_xml}{year_xml}</movie>\n',
        encoding="utf-8",
    )


def test_mode3_should_execute_when_nfo_missing(tmp_path: Path):
    assert mode3_should_execute_by_nfo(str(tmp_path / "a.nfo")) is True


def test_mode3_should_execute_when_title_has_kana(tmp_path: Path):
    nfo = tmp_path / "a.nfo"
    _write_nfo(nfo, title="あいう", outline="有内容")
    assert mode3_should_execute_by_nfo(str(nfo)) is True


def test_mode3_should_execute_when_outline_empty(tmp_path: Path):
    nfo = tmp_path / "a.nfo"
    _write_nfo(nfo, title="ABC-123", outline="")
    assert mode3_should_execute_by_nfo(str(nfo)) is True


def test_mode3_should_skip_when_title_not_jp_and_outline_present(tmp_path: Path):
    nfo = tmp_path / "a.nfo"
    _write_nfo(nfo, title="ABC-123 中文标题", outline="简介")
    assert mode3_should_execute_by_nfo(str(nfo)) is False


def test_mode3_should_execute_when_year_empty(tmp_path: Path):
    nfo = tmp_path / "a.nfo"
    _write_nfo(nfo, title="ABC-123 中文标题", outline="简介", year="")
    assert mode3_should_execute_by_nfo(str(nfo)) is True


def test_mode3_should_execute_when_year_missing(tmp_path: Path):
    nfo = tmp_path / "a.nfo"
    _write_nfo(nfo, title="ABC-123 中文标题", outline="简介", year=None)
    assert mode3_should_execute_by_nfo(str(nfo)) is True


def test_mode3_should_use_plot_when_outline_missing(tmp_path: Path):
    nfo = tmp_path / "a.nfo"
    _write_nfo(nfo, title="ABC-123 中文标题", outline=None, plot="剧情")
    assert mode3_should_execute_by_nfo(str(nfo)) is False
