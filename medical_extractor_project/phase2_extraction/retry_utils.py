import asyncio
import logging

async def retry_with_backoff(coro_func, max_retries=3, initial_delay=2, backoff_factor=2, *args, **kwargs):
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            return await coro_func(*args, **kwargs)
        except Exception as e:
            logging.warning(f"Attempt {attempt+1} failed: {e}")
            if attempt == max_retries - 1:
                logging.error(f"Max retries reached. Giving up.")
                raise
            await asyncio.sleep(delay)
            delay *= backoff_factor
