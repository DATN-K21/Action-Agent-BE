const DEFAULT_TIME_TO_LIVE = 24 * 60 * 60 * 1000; // 1 day in milliseconds

// User cache implementation with TTL
class UserCache {
  	constructor() {
		this.cache = new Map();
  	}

	get(cacheKey) {
		const cachedData = this.cache.get(cacheKey);
		if(!cachedData) {
			console.info("[CACHE] Cache MISSED for user: ", cacheKey)
			return null;
		}
		if(Date.now() > this.cachedData.expiredAt) {
			console.info("[CACHE] Cache EXPIRED for user: ", cacheKey)
			this.cache.delete(cacheKey);
			return null;
		}
		console.info("[CACHE] HIT for user: ", cacheKey)
	}

	set(cacheKey, userData) {
		const expiredAt = Date.now() + DEFAULT_TIME_TO_LIVE;
		this.cache.set(cacheKey, {
			userData,
			expiredAt,
			createdAt: Date.now()
		});
		console.info("[CACHE] SET for user: ", cacheKey, ", expired at: ", new Date(expiredAt).toISOString());
	}

	delete(cacheKey) {
		if(this.cache.has(cacheKey)) {
			this.cache.delete(cacheKey);
			console.info("[CACHE] DELETED for user: ", cacheKey);
		} else {
			console.warn("[CACHE] No cache entry found to delete for user: ", cacheKey);
		}
	}

	cleanup() {
		const now = Date.now();
		const clearCount = 0;
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