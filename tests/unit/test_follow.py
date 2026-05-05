"""Unit tests — follow mode."""
import time
import threading
import pytest

from mzgb.follow import follow_file


class TestFollowFile:
    def test_yields_new_lines(self, tmp_path):
        f = tmp_path / "app.log"
        f.write_text("first\nsecond\n")

        gen = follow_file(str(f), poll_interval=0.01)

        results = []

        def _write():
            time.sleep(0.05)
            with open(f, "a") as fh:
                fh.write("third\n")

        writer = threading.Thread(target=_write)
        writer.start()

        line = next(gen)
        assert line == "third"
        writer.join()

    def test_strips_newline(self, tmp_path):
        f = tmp_path / "app.log"
        f.write_text("")

        gen = follow_file(str(f), poll_interval=0.01)

        def _write():
            time.sleep(0.05)
            with open(f, "a") as fh:
                fh.write("hello\n")

        writer = threading.Thread(target=_write)
        writer.start()
        line = next(gen)
        writer.join()
        assert line == "hello"
        assert "\n" not in line
