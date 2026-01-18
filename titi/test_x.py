import pytest
import asyncio
from computer.x.client import post_tweet_fn, get_mentions_fn, delete_all_tweets_fn
from computer import get_anchor

@pytest.mark.asyncio
async def test_x_client_mock():
    # Should default to mock when no credentials
    res = await post_tweet_fn("Hello X from Titi")
    assert res == "mock_id_123"
    
    mentions = await get_mentions_fn(None)
    assert mentions == ["mock mention 1", "mock mention 2"]
    
    # Test delete all
    delete_res = await delete_all_tweets_fn(None)
    assert "mock" in delete_res.lower()

def test_x_anchors():
    # Verify anchors are registered
    # Note: importing computer executes __init__.py which imports x which sets anchors
    post_fn = get_anchor("post_tweet")
    assert post_fn is not None
    assert callable(post_fn)
    
    get_mentions_fn_anchor = get_anchor("get_mentions")
    assert get_mentions_fn_anchor is not None
    
    delete_all_fn = get_anchor("delete_all_tweets")
    assert delete_all_fn is not None
    assert callable(delete_all_fn)
