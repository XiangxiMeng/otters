import redis

redis_conn = redis.Redis(host='mengtest.redis.cache.windows.net', port=6380, db=3, ssl=True,
                         password='uolxkypkApuInqzE8s9uUkFecd6wDkrcudpxGWSXHCY=')


