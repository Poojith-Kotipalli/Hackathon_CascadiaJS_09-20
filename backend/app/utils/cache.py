import time
from typing import Dict, Any, Optional
from collections import OrderedDict

class InMemoryCache:
    def __init__(self, max_size: int = 100, ttl: int = 300):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.ttl = ttl  # Time to live in seconds
    
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                return value
            else:
                # Expired
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        # Remove oldest if at capacity
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
        
        self.cache[key] = (value, time.time())
    
    def clear(self):
        self.cache.clear()

# Global cache instance
compliance_cache = InMemoryCache(max_size=500, ttl=600)