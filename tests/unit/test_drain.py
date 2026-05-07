"""Unit tests for mzgb.drain and cluster_line integration."""
from __future__ import annotations

import sys
from unittest.mock import MagicMock

import mzgb.drain as drain_module
from mzgb.parser import LogLine, cluster_line


# ── Helpers ──────────────────────────────────────────────────────────────────

def _reset_drain() -> None:
    """Reset module-level singletons so each test starts clean."""
    drain_module._miner = None
    drain_module._DRAIN_AVAILABLE = False


# ── cluster() — fallback when drain3 not installed ───────────────────────────

class TestClusterFallback:
    """Tests for cluster() when drain3 is not installed."""

    def setup_method(self) -> None:
        """Reset drain state before each test."""
        _reset_drain()

    def test_returns_minus_one_when_unavailable(self, monkeypatch) -> None:
        """cluster() returns -1 cluster_id when drain3 is absent."""
        monkeypatch.setitem(sys.modules, "drain3", None)
        cluster_id, template = drain_module.cluster("connection refused")
        assert cluster_id == -1

    def test_returns_raw_message_as_template_when_unavailable(self, monkeypatch) -> None:
        """cluster() returns the raw message as template when drain3 is absent."""
        monkeypatch.setitem(sys.modules, "drain3", None)
        msg = "disk full on /dev/sda"
        _, template = drain_module.cluster(msg)
        assert template == msg

    def test_is_available_false_when_unavailable(self, monkeypatch) -> None:
        """is_available() returns False when drain3 cannot be imported."""
        monkeypatch.setitem(sys.modules, "drain3", None)
        _reset_drain()
        assert drain_module.is_available() is False


# ── cluster() — with a mocked drain3 ─────────────────────────────────────────

class TestClusterWithMockedDrain3:
    """Tests for cluster() with a stubbed drain3 installed."""

    def setup_method(self) -> None:
        """Reset drain state before each test."""
        _reset_drain()

    def _install_mock_drain3(self) -> MagicMock:
        """Inject a minimal drain3 mock into sys.modules and return mock_miner."""
        cluster_obj = MagicMock()
        cluster_obj.cluster_id = 7
        cluster_obj.get_template.return_value = "connection <*> refused"

        result_dict = {"cluster": cluster_obj}

        mock_miner = MagicMock()
        mock_miner.add_log_message.return_value = result_dict

        mock_template_miner_cls = MagicMock(return_value=mock_miner)
        mock_config_cls = MagicMock()

        mock_drain3 = MagicMock()
        mock_drain3.TemplateMiner = mock_template_miner_cls
        mock_config_mod = MagicMock()
        mock_config_mod.TemplateMinerConfig = mock_config_cls

        sys.modules["drain3"] = mock_drain3
        sys.modules["drain3.template_miner_config"] = mock_config_mod

        return mock_miner

    def test_cluster_returns_id_and_template(self) -> None:
        """cluster() returns (cluster_id, template) from drain3 result."""
        self._install_mock_drain3()
        _reset_drain()

        cid, tmpl = drain_module.cluster("connection 10.0.0.1 refused")
        assert cid == 7
        assert tmpl == "connection <*> refused"

    def test_is_available_true_with_drain3(self) -> None:
        """is_available() returns True when drain3 mock is installed."""
        self._install_mock_drain3()
        _reset_drain()
        assert drain_module.is_available() is True

    def test_none_result_falls_back(self) -> None:
        """cluster() returns (-1, message) when add_log_message returns None."""
        mock_miner = self._install_mock_drain3()
        mock_miner.add_log_message.return_value = None
        _reset_drain()

        cid, tmpl = drain_module.cluster("some log line")
        assert cid == -1
        assert tmpl == "some log line"

    def teardown_method(self) -> None:
        """Remove mock drain3 modules and reset drain state."""
        for key in ("drain3", "drain3.template_miner_config"):
            sys.modules.pop(key, None)
        _reset_drain()


# ── cluster_line() in parser.py ───────────────────────────────────────────────

class TestClusterLine:
    """Tests for the cluster_line() helper in mzgb.parser."""

    def test_uses_message_when_present(self, monkeypatch) -> None:
        """cluster_line() feeds LogLine.message into drain.cluster()."""
        monkeypatch.setattr("mzgb.drain.cluster", lambda text: (42, "tmpl: <*>"))
        log = LogLine(raw="raw line", message="structured message")
        result = cluster_line(log)
        assert result.cluster_id == 42
        assert result.template == "tmpl: <*>"

    def test_falls_back_to_raw_when_no_message(self, monkeypatch) -> None:
        """cluster_line() uses LogLine.raw when message is None."""
        monkeypatch.setattr("mzgb.drain.cluster", lambda text: (1, text))
        log = LogLine(raw="fallback raw", message=None)
        result = cluster_line(log)
        assert result.cluster_id == 1
        assert result.template == "fallback raw"

    def test_returns_same_logline_object(self, monkeypatch) -> None:
        """cluster_line() mutates and returns the same LogLine instance."""
        monkeypatch.setattr("mzgb.drain.cluster", lambda text: (0, "t"))
        log = LogLine(raw="x")
        returned = cluster_line(log)
        assert returned is log

    def test_default_cluster_id_is_minus_one(self) -> None:
        """Fresh LogLine has cluster_id=-1 and template=None."""
        log = LogLine(raw="any line")
        assert log.cluster_id == -1
        assert log.template is None
