"""Unit tests for mzgb.drain and cluster_line integration."""
from __future__ import annotations

import importlib
import sys
from unittest.mock import MagicMock, patch

import pytest

import mzgb.drain as drain_module
from mzgb.parser import LogLine, cluster_line


# ── Helpers ──────────────────────────────────────────────────────────────────

def _reset_drain():
    """Reset module-level singletons so each test starts clean."""
    drain_module._miner = None
    drain_module._DRAIN_AVAILABLE = False


# ── cluster() — fallback when drain3 not installed ───────────────────────────

class TestClusterFallback:
    def setup_method(self):
        _reset_drain()

    def test_returns_minus_one_when_unavailable(self, monkeypatch):
        monkeypatch.setitem(sys.modules, "drain3", None)
        cluster_id, template = drain_module.cluster("connection refused")
        assert cluster_id == -1

    def test_returns_raw_message_as_template_when_unavailable(self, monkeypatch):
        monkeypatch.setitem(sys.modules, "drain3", None)
        msg = "disk full on /dev/sda"
        _, template = drain_module.cluster(msg)
        assert template == msg

    def test_is_available_false_when_unavailable(self, monkeypatch):
        monkeypatch.setitem(sys.modules, "drain3", None)
        _reset_drain()
        assert drain_module.is_available() is False


# ── cluster() — with a mocked drain3 ─────────────────────────────────────────

class TestClusterWithMockedDrain3:
    def setup_method(self):
        _reset_drain()

    def _install_mock_drain3(self):
        """Inject a minimal drain3 mock into sys.modules."""
        cluster_obj = MagicMock()
        cluster_obj.cluster_id = 7
        cluster_obj.get_template.return_value = "connection <*> refused"

        result_dict = {"cluster": cluster_obj}

        mock_miner = MagicMock()
        mock_miner.add_log_message.return_value = result_dict

        MockTemplateMiner = MagicMock(return_value=mock_miner)
        MockConfig = MagicMock()

        mock_drain3 = MagicMock()
        mock_drain3.TemplateMiner = MockTemplateMiner
        mock_config_mod = MagicMock()
        mock_config_mod.TemplateMinerConfig = MockConfig

        sys.modules["drain3"] = mock_drain3
        sys.modules["drain3.template_miner_config"] = mock_config_mod

        return mock_miner

    def test_cluster_returns_id_and_template(self):
        mock_miner = self._install_mock_drain3()
        _reset_drain()

        cid, tmpl = drain_module.cluster("connection 10.0.0.1 refused")
        assert cid == 7
        assert tmpl == "connection <*> refused"

    def test_is_available_true_with_drain3(self):
        self._install_mock_drain3()
        _reset_drain()
        assert drain_module.is_available() is True

    def test_none_result_falls_back(self):
        mock_miner = self._install_mock_drain3()
        mock_miner.add_log_message.return_value = None
        _reset_drain()

        cid, tmpl = drain_module.cluster("some log line")
        assert cid == -1
        assert tmpl == "some log line"

    def teardown_method(self):
        for key in ("drain3", "drain3.template_miner_config"):
            sys.modules.pop(key, None)
        _reset_drain()


# ── cluster_line() in parser.py ───────────────────────────────────────────────

class TestClusterLine:
    def test_uses_message_when_present(self, monkeypatch):
        monkeypatch.setattr("mzgb.drain.cluster", lambda text: (42, "tmpl: <*>"))
        log = LogLine(raw="raw line", message="structured message")
        result = cluster_line(log)
        assert result.cluster_id == 42
        assert result.template == "tmpl: <*>"

    def test_falls_back_to_raw_when_no_message(self, monkeypatch):
        monkeypatch.setattr("mzgb.drain.cluster", lambda text: (1, text))
        log = LogLine(raw="fallback raw", message=None)
        result = cluster_line(log)
        assert result.cluster_id == 1
        assert result.template == "fallback raw"

    def test_returns_same_logline_object(self, monkeypatch):
        monkeypatch.setattr("mzgb.drain.cluster", lambda text: (0, "t"))
        log = LogLine(raw="x")
        returned = cluster_line(log)
        assert returned is log

    def test_default_cluster_id_is_minus_one(self):
        log = LogLine(raw="any line")
        assert log.cluster_id == -1
        assert log.template is None
