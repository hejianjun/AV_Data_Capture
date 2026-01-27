import io

from mdc.utils.logger import info, success, warn, error, debug


def test_logger_functions_accept_file_kwarg_and_write_plain_text():
    buf = io.StringIO()
    info("hello", file=buf)
    assert buf.getvalue() == "hello\n"

    buf = io.StringIO()
    success("<movie>", file=buf)
    assert buf.getvalue() == "<movie>\n"

    buf = io.StringIO()
    warn("WARNING: test", file=buf)
    assert buf.getvalue() == "WARNING: test\n"

    buf = io.StringIO()
    error("ERROR: test", file=buf)
    assert buf.getvalue() == "ERROR: test\n"

    buf = io.StringIO()
    debug("debug", file=buf)
    assert buf.getvalue() == "debug\n"
