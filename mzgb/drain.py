"""Drain3-based log template clustering for mzgb.

Wraps drain3 with a simple API and degrades gracefully when drain3 is not
installed (returns the raw message as the template, cluster_id=-1).
"""
from __future__ import annotations

from typing import Tuple

_DRAIN_AVAILABLE = False
_miner = None


def _get_miner():
    """Lazy-init the TemplateMiner singleton."""
    global _miner, _DRAIN_AVAILABLE
    if _miner is not None:
        return _miner
    try:
        from drain3 import TemplateMiner
        from drain3.template_miner_config import TemplateMinerConfig

        cfg = TemplateMinerConfig()
        cfg.drain_depth = 4
        cfg.drain_sim_th = 0.4
        cfg.drain_max_children = 100
        cfg.parametrize_numeric_tokens = True
        _miner = TemplateMiner(config=cfg)
        _DRAIN_AVAILABLE = True
    except ImportError:
        _miner = None
        _DRAIN_AVAILABLE = False
    return _miner


def is_available() -> bool:
    """Return True if drain3 is installed and the miner initialised OK."""
    return _get_miner() is not None


def cluster(message: str) -> Tuple[int, str]:
    """Feed a log message into the Drain miner and return (cluster_id, template).

    Args:
        message: Raw log message text (level + timestamp already stripped).

    Returns:
        (cluster_id, template_str) — cluster_id is -1 and template equals
        message when drain3 is unavailable.
    """
    miner = _get_miner()
    if miner is None:
        return (-1, message)
    result = miner.add_log_message(message)
    if result is None:
        return (-1, message)
    cluster_obj = result.get("cluster") if isinstance(result, dict) else result
    if cluster_obj is None:
        return (-1, message)
    return (cluster_obj.cluster_id, cluster_obj.get_template())
