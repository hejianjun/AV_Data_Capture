import json

import mdc.scraping.parser as parser_mod
from mdc.config import config as config_mod
from mdc.scraping.parser import Parser


class DummyParser(Parser):
    source = "dummy"

    def getCover(self, htmltree):
        raise ValueError("can not find image")


def test_known_scrape_error_no_traceback(monkeypatch):
    conf = config_mod.getInstance()
    conf.set_override("debug_mode:switch=1")
    try:
        parser = DummyParser()
        parser.init()
        parser.detailurl = "http://example.test"

        def _boom(*args, **kwargs):
            raise AssertionError("traceback.print_exception should not be called")

        monkeypatch.setattr(parser_mod.traceback, "print_exception", _boom)

        data = json.loads(parser.dictformat(None))
        assert data["title"] == ""
    finally:
        conf.set_override("debug_mode:switch=0")
