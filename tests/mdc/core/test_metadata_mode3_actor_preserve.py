from pathlib import Path
from typing import List, Optional

import pytest

from mdc.config import config as config_module
from mdc.config.config import Config
from mdc.core.metadata import print_files


def _write_config_ini(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "[common]",
                "main_mode = 3",
                "source_folder = ./",
                "failed_output_folder = failed",
                "success_output_folder = success",
                "link_mode = 0",
                "failed_move = 0",
                "jellyfin = 0",
                "actor_only_tag = 0",
                "translate_to_sc = 0",
                "multi_threading = 0",
                "del_empty_folder = 0",
                "ignore_failed_list = 0",
                "download_only_missing_images = 0",
                "mapping_table_validity = 30",
                "sleep = 0",
                "anonymous_fill = 1",
                "actor_gender = female",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_nfo_with_actors(path: Path, actors: Optional[List[str]]) -> None:
    actor_xml = ""
    if actors:
        actor_xml = "".join([f"<actor><name>{a}</name></actor>" for a in actors])
    path.write_text(
        f'<?xml version="1.0" encoding="UTF-8" ?>\n<movie>{actor_xml}</movie>\n',
        encoding="utf-8",
    )


@pytest.fixture()
def _mode3_config(tmp_path: Path):
    original = config_module.G_conf_override[0]
    try:
        config_module.G_conf_override[0] = None
        ini = tmp_path / "test.ini"
        _write_config_ini(ini)
        config_module.G_conf_override[0] = Config(str(ini))
        yield
    finally:
        config_module.G_conf_override[0] = original


def _json_data(number: str) -> dict:
    return {
        "title": number,
        "studio": "S",
        "year": "2020",
        "outline": "O",
        "runtime": "100",
        "director": "D",
        "actor_photo": {},
        "release": "2020-01-01",
        "number": number,
        "cover": "",
        "trailer": "",
        "website": "",
        "series": "",
        "label": "",
        "source": "javdb",
        "original_naming_rule": number,
    }


def test_mode3_anonymous_actor_does_not_override_existing_real_actor(
    tmp_path: Path, _mode3_config
):
    movie = tmp_path / "ABC-123.mp4"
    nfo = movie.with_suffix(".nfo")
    _write_nfo_with_actors(nfo, ["Alice"])

    print_files(
        path=str(tmp_path),
        leak_word="",
        c_word="",
        naming_rule="ABC-123",
        part="",
        cn_sub=False,
        json_data=_json_data("ABC-123"),
        filepath=str(movie),
        tag=[],
        actor_list=["佚名"],
        liuchu=False,
        uncensored=False,
        hack=False,
        hack_word="",
        _4k=False,
        fanart_path="fanart.jpg",
        poster_path="poster.jpg",
        thumb_path="thumb.jpg",
        iso=False,
    )

    out = nfo.read_text(encoding="utf-8")
    assert "<name>Alice</name>" in out
    assert "<name>佚名</name>" not in out


def test_mode3_anonymous_actor_written_when_old_nfo_has_no_actor(
    tmp_path: Path, _mode3_config
):
    movie = tmp_path / "ABC-124.mp4"
    nfo = movie.with_suffix(".nfo")
    _write_nfo_with_actors(nfo, None)

    print_files(
        path=str(tmp_path),
        leak_word="",
        c_word="",
        naming_rule="ABC-124",
        part="",
        cn_sub=False,
        json_data=_json_data("ABC-124"),
        filepath=str(movie),
        tag=[],
        actor_list=["佚名"],
        liuchu=False,
        uncensored=False,
        hack=False,
        hack_word="",
        _4k=False,
        fanart_path="fanart.jpg",
        poster_path="poster.jpg",
        thumb_path="thumb.jpg",
        iso=False,
    )

    out = nfo.read_text(encoding="utf-8")
    assert "<name>佚名</name>" in out
