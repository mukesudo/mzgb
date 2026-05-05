from collections import deque
from typing import Generator, Iterable, Tuple

from mzgb.parser import LogLine


def context_window(
    stream: Iterable[Tuple[str, LogLine]],
    pipeline,
    context: int,
) -> Generator[Tuple[LogLine, bool], None, None]:
    """Yield (LogLine, is_separator) pairs respecting before/after context.

    Args:
        stream:   Iterable of (raw, LogLine) pairs.
        pipeline: FilterPipeline — .match(LogLine) -> bool.
        context:  Number of lines to show before and after each match.

    Yields:
        (LogLine, is_separator) where is_separator=True signals a --- break.
    """
    buf: deque = deque(maxlen=context)
    after_remaining = 0
    last_yielded_idx = -1
    for idx, (_, parsed) in enumerate(stream):
        if pipeline.match(parsed):
            gap_start = idx - len(buf)
            if context > 0 and last_yielded_idx >= 0 and gap_start > last_yielded_idx + 1:
                yield (None, True)
            for prev in buf:
                yield (prev, False)
            buf.clear()
            yield (parsed, False)
            last_yielded_idx = idx
            after_remaining = context
        elif after_remaining > 0:
            yield (parsed, False)
            last_yielded_idx = idx
            after_remaining -= 1
        else:
            buf.append(parsed)
