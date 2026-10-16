import os
from functools import partial

import anyio

# PDF work is CPU- and memory-heavy, so it runs off the event loop; the limiter caps how
# many jobs run at once to keep peak memory predictable.
_processing_limiter = anyio.CapacityLimiter(max(1, min(4, os.cpu_count() or 1)))


async def run_processing(func, *args, **kwargs):
    """Run a blocking service function in a worker thread so the server stays responsive."""
    return await anyio.to_thread.run_sync(
        partial(func, *args, **kwargs), limiter=_processing_limiter
    )
