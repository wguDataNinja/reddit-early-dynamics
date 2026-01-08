"""
create read-only Reddit client via PRAW.

- requires REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
- raises RuntimeError if any missing
"""

import os
import praw


def get_reddit_client():
    """Return configured PRAW Reddit client instance."""
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT")

    if not all([client_id, client_secret, user_agent]):
        raise RuntimeError("Missing Reddit API environment variables")

    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )