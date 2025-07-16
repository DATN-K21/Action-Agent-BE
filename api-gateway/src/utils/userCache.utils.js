const DEFAULT_TIME_TO_LIVE = 24 * 60 * 60 * 1000; // 1 day in milliseconds

function simplifyCacheKey(key) {
	if(key.length <= 20) {
		return key;
	}
	return key.substring(0, 10) + '...' + key.substring(key.length - 10);
}

// User cache implementation with TTL
class UserCache {
  	constructor() {
		this.cache = new Map();
  	}

	get(cacheKey) {
		const cachedData = this.cache.get(cacheKey);
		const simplifiedKey = simplifyCacheKey(cacheKey);
		if(!cachedData) {
			console.info("[CACHE] Cache MISSED for user with token: ", simplifiedKey)
			return null;
		}
		if(cachedData?.expiredAt && Date.now() > cachedData?.expiredAt) {
			console.info("[CACHE] Cache EXPIRED for user with token: ", simplifiedKey)
			this.cache.delete(cacheKey);
			return null;
		}
		console.info("[CACHE] HIT for user with token: ", simplifiedKey);
		return cachedData.userData;
	}

	set(cacheKey, userData) {
		const expiredAt = Date.now() + DEFAULT_TIME_TO_LIVE;
		this.cache.set(cacheKey, {
			userData,
			expiredAt,
			createdAt: Date.now()
		});
		const simplifiedKey = simplifyCacheKey(cacheKey);
		console.info("[CACHE] SET for user with token: ", simplifiedKey, ", expired at: ", new Date(expiredAt).toISOString());
	}

	delete(cacheKey) {
		const simplifiedKey = simplifyCacheKey(cacheKey);
		if(this.cache.has(cacheKey)) {
			this.cache.delete(cacheKey);
			console.info("[CACHE] DELETED for user with token: ", simplifiedKey);
		} else {
			console.warn("[CACHE] No cache entry found to delete for user with token: ", simplifiedKey);
		}
	}

	cleanup() {
		const now = Date.now();
		let clearCount = 0;
		for (const [key, value] of this.cache.entries()) {
			if (value.expiredAt < now) {
				this.cache.delete(key);
				clearCount++;
			}
		}
		console.info(`[CACHE] Cleanup completed. Removed ${clearCount} expired entries.`);
	}

	clear() {
		const clearCount = this.cache.size;
		this.cache.clear();
		console.info("[CACHE] Cleared all cache entries. Total cleared: ", clearCount);
	}
};

const globalUserCache = new UserCache();
module.exports = globalUserCache;