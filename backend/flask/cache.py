from flask_caching import Cache

def get_app_cache(app):
    """
    Returns the cache from the app.

    :param app: The app.

    :returns: The cache.
    :rtype: Cache
    """

    return Cache(app)


def get_user_cache(cache, user_id):
    """
    Returns the user data from the cache.

    :param cache: The cache.
    :param user_id: The user_id.

    :returns: The user data.
    :rtype: dict
    """

    return UserDataCache(cache, user_id)


class UserDataCache:
    def __init__(self, cache, user_id):
        self.cache = cache
        self.user_id = user_id
        self.user_data = self.cache.get(self.user_id)

        if self.user_data is None:
            self.user_data = {}
            self.cache.set(self.user_id, self.user_data)
            self.reload()

    def reload(self):
        self.user_data = self.cache.get(self.user_id)

    def save(self):
        self.cache.set(self.user_id, self.user_data)

    def get(self, key):
        return self.user_data.get(key)

    def set(self, key, value):
        self.user_data[key] = value
        self.save()