"""
API Key Manager - Quản lý và xoay vòng nhiều Gemini API keys
"""

import os
import time
import threading
from typing import List, Optional

class APIKeyManager:
    """Quản lý nhiều API keys với rotation và fallback"""
    
    def __init__(self, keys_file: str = 'api_keys.txt'):
        """
        Khởi tạo Key Manager
        
        Args:
            keys_file: Đường dẫn tới file chứa API keys
        """
        self.keys_file = keys_file
        self.keys: List[str] = []
        self.current_index = 0
        self.lock = threading.Lock()
        self.key_stats = {}  # Track usage per key
        
        self._load_keys()
    
    def _load_keys(self):
        """Load API keys từ file"""
        try:
            # Key trong biến môi trường GEMINI_API_KEY (có thể nhiều key, ngăn bởi dấu phẩy)
            for key in os.getenv('GEMINI_API_KEY', '').split(','):
                self._add_key(key.strip())

            if not os.path.exists(self.keys_file):
                if not self.keys:
                    print(f"⚠️ File {self.keys_file} không tồn tại")
                return
            
            with open(self.keys_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Parse keys, bỏ qua comment và dòng trống
            for line in lines:
                line = line.strip()
                
                # Bỏ qua comment và dòng trống
                if not line or line.startswith('#'):
                    continue
                
                # Clean key (remove trailing dots, spaces)
                self._add_key(line.rstrip('.'))
            
            print(f"✅ Loaded {len(self.keys)} API keys")
            if self.keys:
                print(f"📊 Estimated quota: {len(self.keys) * 15} requests/minute")
        
        except Exception as e:
            print(f"❌ Lỗi khi load keys: {str(e)}")
    
    def _add_key(self, key: str):
        """Thêm key hợp lệ, bỏ qua key trùng"""
        if key.startswith('AIza') and key not in self.key_stats:
            self.keys.append(key)
            self.key_stats[key] = {
                'uses': 0,
                'last_used': None,
                'errors': 0
            }
    
    def get_next_key(self) -> Optional[str]:
        """
        Lấy key tiếp theo theo round-robin
        
        Returns:
            API key hoặc None nếu không có key
        """
        with self.lock:
            if not self.keys:
                print("❌ Không có API key nào!")
                return None
            
            # Round-robin: xoay vòng qua các keys
            key = self.keys[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.keys)
            
            # Update stats
            self.key_stats[key]['uses'] += 1
            self.key_stats[key]['last_used'] = time.time()
            
            return key
    
    def report_error(self, key: str):
        """Báo lỗi cho một key"""
        with self.lock:
            if key in self.key_stats:
                self.key_stats[key]['errors'] += 1
    
    def get_stats(self) -> dict:
        """Lấy thống kê sử dụng"""
        with self.lock:
            return {
                'total_keys': len(self.keys),
                'current_index': self.current_index,
                'key_stats': self.key_stats.copy()
            }
    
    def print_stats(self):
        """In thống kê ra console"""
        stats = self.get_stats()
        print("\n" + "="*60)
        print("📊 API KEY STATISTICS")
        print("="*60)
        print(f"Total keys: {stats['total_keys']}")
        print(f"Current rotation index: {stats['current_index']}")
        print("\nPer-key usage:")
        
        for i, (key, data) in enumerate(stats['key_stats'].items(), 1):
            key_short = key[:8] + "..."
            print(f"  Key {i} ({key_short}): {data['uses']} uses, {data['errors']} errors")
        
        print("="*60 + "\n")


# Global key manager instance
_key_manager = None

def get_key_manager(keys_file: Optional[str] = None) -> APIKeyManager:
    """Get hoặc tạo singleton instance của KeyManager"""
    global _key_manager
    
    if _key_manager is None:
        if keys_file is None:
            import config
            keys_file = config.API_KEYS_FILE
        _key_manager = APIKeyManager(keys_file)
    
    return _key_manager


if __name__ == "__main__":
    # Test key manager
    manager = get_key_manager()
    
    print("\nTesting key rotation:")
    for i in range(7):
        key = manager.get_next_key()
        if key:
            print(f"Request {i+1}: {key[:8]}...")
    
    manager.print_stats()
