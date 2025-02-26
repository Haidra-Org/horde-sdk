def test_check_redis_cache_refreshed_on_shared_key_modified() -> None:
    """From the PR description:
    Redis cache is now refreshed when User is modified.

        Problem:
        After creating or deleting a shared key, it is not immediately reflected on /get_user endpoint as it serves
        now stale cached version.

        This adds functionality to bust the user cache - both by id and by api_key - ensuring the cached results
        are always fresh.

        How to test:
        call GET /api/v2/find_user, you should see [] under sharedkey_ids
        call GET /api/v2/users/:user_id, you should see [] under sharedkey_ids
        call PUT /api/v2/sharedkeys with body {}
        call GET /api/v2/find_user again, you should see ['5d81849a...'] under sharedkey_ids
        call GET /api/v2/users/:user_id again, you should also see ['5d81849a...'] under sharedkey_ids
        call DELETE /api/v2/sharedkeys/:keyId
        call GET /api/v2/find_user, you should see [] under sharedkey_ids
        call GET /api/v2/users/:user_id, you should see [] under sharedkey_ids
    """
