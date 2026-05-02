"""Unit tests — context buffer (Phase 7)."""
import pytest


class TestContextBuffer:
    @pytest.mark.skip(reason="ContextBuffer not yet implemented — Phase 7.1")
    def test_pre_context_collected(self):
        from logsnap.buffer import ContextBuffer
        buf = ContextBuffer(n=3)
        for line in ["a", "b", "c", "d", "e"]:
            buf.feed(line)
        assert buf.pre_context() == ["c", "d", "e"]

    @pytest.mark.skip(reason="ContextBuffer not yet implemented — Phase 7.1")
    def test_pre_context_respects_maxlen(self):
        from logsnap.buffer import ContextBuffer
        buf = ContextBuffer(n=2)
        for line in ["a", "b", "c"]:
            buf.feed(line)
        assert len(buf.pre_context()) == 2

    @pytest.mark.skip(reason="ContextBuffer not yet implemented — Phase 7.2")
    def test_post_context_countdown(self):
        from logsnap.buffer import ContextBuffer
        buf = ContextBuffer(n=2)
        buf.start_post_context()
        results = [buf.in_post_context() for _ in range(4)]
        assert results == [True, True, False, False]

    @pytest.mark.skip(reason="ContextBuffer not yet implemented — Phase 7.3")
    def test_overlapping_windows_no_separator(self):
        from logsnap.buffer import ContextBuffer
        buf = ContextBuffer(n=3)
        assert buf.needs_separator(last_match_pos=5, current_pos=7) is False

    @pytest.mark.skip(reason="ContextBuffer not yet implemented — Phase 7.3")
    def test_non_overlapping_windows_separator(self):
        from logsnap.buffer import ContextBuffer
        buf = ContextBuffer(n=2)
        assert buf.needs_separator(last_match_pos=1, current_pos=10) is True
