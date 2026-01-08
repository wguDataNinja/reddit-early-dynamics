"""
praw client helper with request counting

- wraps the praw requester
- counts outgoing requests
- used for run-level http counts
"""

from __future__ import annotations

import os
import praw
import prawcore


class CountingRequestor(prawcore.requestor.Requestor):
    """
    - increments request_count on each request
    - approximate accounting only
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request_count = 0

    def request(self, *args, **kwargs):
        self.request_count += 1
        return super().request(*args, **kwargs)


def get_reddit_client_with_counter() -> tuple[praw.Reddit, CountingRequestor]:
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT")

    if not all([client_id, client_secret, user_agent]):
        raise RuntimeError("Missing Reddit API environment variables")

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
        requestor_class=CountingRequestor,
    )

    # requestor instance is attached to the core
    req = reddit._core._requestor  # type: ignore[attr-defined]
    return reddit, req