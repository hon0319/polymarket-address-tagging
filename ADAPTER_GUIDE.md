# 數據適配器使用指南

本文檔說明如何實作自己的數據適配器，以便將標籤算法整合到你的系統中。

---

## 📋 什麼是數據適配器？

數據適配器是一個接口，用於連接標籤算法和你的數據源（數據庫、API 等）。

**為什麼需要它？**
- 第二和第三階段的標籤需要額外的數據（持倉時間、價格歷史、新聞、社交媒體等）
- 不同系統的數據結構和 API 不同
- 適配器模式讓算法邏輯與數據源解耦

---

## 🎯 快速開始

### 1. 查看接口定義

所有數據適配器都需要繼承 `DataAdapter` 基類：

```python
from adapters.base import DataAdapter

class MyDataAdapter(DataAdapter):
    """你的數據適配器"""
    
    def get_price_history(self, market_id: int) -> List[Dict]:
        """獲取市場價格歷史"""
        # 實作你的邏輯
        pass
    
    # ... 實作其他方法
```

### 2. 實作必要的方法

根據你需要的標籤階段，實作相應的方法：

| 階段 | 需要實作的方法 | 標籤數量 |
|------|--------------|---------|
| 第一階段 | 無（使用現有數據） | 19 種 |
| 第二階段 | `get_price_history`, `get_position_changes` | +15 種 |
| 第三階段 | `get_market_news`, `get_address_social_activity` 等 | +16 種 |

### 3. 使用你的適配器

```python
from address_tagging_service import AddressTaggingService
from my_adapter import MyDataAdapter

# 創建你的適配器
adapter = MyDataAdapter()

# 初始化服務
service = AddressTaggingService(
    config_path='config.json',
    data_adapter=adapter
)

# 開始打標籤
service.tag_all_addresses()
```

---

## 📊 數據適配器接口詳解

### 第二階段方法

#### 1. `get_price_history(market_id: int) -> List[Dict]`

**用途：** 獲取市場的價格歷史，用於判斷順勢/逆勢操作

**返回格式：**
```python
[
    {
        'timestamp': datetime(2024, 1, 1, 12, 0, 0),
        'price': 0.65,  # Yes 的價格
        'volume': 1000
    },
    # ... 更多價格點
]
```

**實作示例：**
```python
def get_price_history(self, market_id: int) -> List[Dict]:
    # 從你的數據庫查詢
    query = """
        SELECT timestamp, price, volume
        FROM market_prices
        WHERE market_id = %s
        ORDER BY timestamp ASC
    """
    result = self.db.execute(query, (market_id,))
    return [dict(row) for row in result]
```

**如果沒有數據：**
```python
def get_price_history(self, market_id: int) -> List[Dict]:
    # 返回空列表，算法會使用簡化版邏輯
    return []
```

---

#### 2. `get_position_changes(address_id: int) -> List[Dict]`

**用途：** 獲取地址的持倉變化，用於計算持倉時長、對沖策略等

**返回格式：**
```python
[
    {
        'timestamp': datetime(2024, 1, 1, 12, 0, 0),
        'market_id': 123,
        'outcome': 'Yes',  # 或 'No'
        'side': 'buy',  # 或 'sell'
        'amount': 100,
        'price': 0.65
    },
    # ... 更多持倉變化
]
```

**實作示例：**
```python
def get_position_changes(self, address_id: int) -> List[Dict]:
    query = """
        SELECT timestamp, market_id, outcome, side, amount, price
        FROM position_changes
        WHERE address_id = %s
        ORDER BY timestamp ASC
    """
    result = self.db.execute(query, (address_id,))
    return [dict(row) for row in result]
```

---

### 第三階段方法

#### 3. `get_market_news(market_id: int, days: int = 7) -> List[Dict]`

**用途：** 獲取市場相關新聞，用於判斷事件驅動、新聞追蹤、疑似內線等

**返回格式：**
```python
[
    {
        'title': 'Breaking: Election Results Announced',
        'published_at': datetime(2024, 1, 1, 10, 0, 0),
        'source': 'CNN',
        'url': 'https://...'
    },
    # ... 更多新聞
]
```

**實作示例（使用新聞 API）：**
```python
def get_market_news(self, market_id: int, days: int = 7) -> List[Dict]:
    # 獲取市場關鍵詞
    market = self.db.get_market(market_id)
    keywords = market['title']
    
    # 調用新聞 API
    response = requests.get(
        'https://newsapi.org/v2/everything',
        params={
            'q': keywords,
            'from': (datetime.now() - timedelta(days=days)).isoformat(),
            'apiKey': self.news_api_key
        }
    )
    
    articles = response.json()['articles']
    return [
        {
            'title': a['title'],
            'published_at': datetime.fromisoformat(a['publishedAt']),
            'source': a['source']['name'],
            'url': a['url']
        }
        for a in articles
    ]
```

**如果沒有新聞 API：**
```python
def get_market_news(self, market_id: int, days: int = 7) -> List[Dict]:
    # 返回空列表，算法會跳過需要新聞的標籤
    return []
```

---

#### 4. `get_address_social_activity(address: str) -> Dict`

**用途：** 獲取地址的社交媒體活動，用於判斷 KOL、社群領袖、名人等

**返回格式：**
```python
{
    'twitter_followers': 50000,
    'twitter_mentions': 100,
    'discord_messages': 50,
    'is_verified': True
}
```

**實作示例（使用 Twitter API）：**
```python
def get_address_social_activity(self, address: str) -> Dict:
    # 搜索 Twitter 上提到該地址的推文
    response = requests.get(
        'https://api.twitter.com/2/tweets/search/recent',
        params={'query': address},
        headers={'Authorization': f'Bearer {self.twitter_token}'}
    )
    
    mentions = response.json()['meta']['result_count']
    
    # 如果有關聯的 Twitter 帳號，獲取粉絲數
    # （需要你的系統有地址 -> Twitter 的映射）
    twitter_handle = self.get_twitter_handle(address)
    if twitter_handle:
        user_response = requests.get(
            f'https://api.twitter.com/2/users/by/username/{twitter_handle}',
            headers={'Authorization': f'Bearer {self.twitter_token}'}
        )
        followers = user_response.json()['data']['public_metrics']['followers_count']
        is_verified = user_response.json()['data']['verified']
    else:
        followers = 0
        is_verified = False
    
    return {
        'twitter_followers': followers,
        'twitter_mentions': mentions,
        'discord_messages': 0,  # 如果有 Discord API 可以查詢
        'is_verified': is_verified
    }
```

**如果沒有社交媒體 API：**
```python
def get_address_social_activity(self, address: str) -> Dict:
    # 返回默認值，算法會跳過需要社交數據的標籤
    return {
        'twitter_followers': 0,
        'twitter_mentions': 0,
        'discord_messages': 0,
        'is_verified': False
    }
```

---

#### 5. `get_trade_pattern_stats(address_id: int) -> Dict`

**用途：** 獲取交易模式統計，用於判斷機器人/腳本

**返回格式：**
```python
{
    'trade_time_variance': 500,  # 交易時間間隔的方差（秒）
    'unique_trade_amounts': 3,  # 唯一交易金額數量
    'avg_response_time': 5  # 平均響應時間（秒）
}
```

**實作示例：**
```python
def get_trade_pattern_stats(self, address_id: int) -> Dict:
    trades = self.db.get_address_trades(address_id)
    
    # 計算交易時間間隔方差
    timestamps = [t['timestamp'] for t in trades]
    time_diffs = [(timestamps[i+1] - timestamps[i]).total_seconds() 
                  for i in range(len(timestamps)-1)]
    time_variance = statistics.variance(time_diffs) if len(time_diffs) > 1 else 0
    
    # 計算唯一交易金額數量
    amounts = set(round(t['amount'], 2) for t in trades if t['amount'])
    unique_amounts = len(amounts)
    
    # 計算平均響應時間（交易時間 - 市場創建時間）
    response_times = []
    for trade in trades:
        market = self.db.get_market(trade['market_id'])
        response_time = (trade['timestamp'] - market['created_at']).total_seconds()
        response_times.append(response_time)
    
    avg_response_time = statistics.mean(response_times) if response_times else 0
    
    return {
        'trade_time_variance': time_variance,
        'unique_trade_amounts': unique_amounts,
        'avg_response_time': avg_response_time
    }
```

---

#### 6. `get_linked_addresses(address_id: int) -> List[str]`

**用途：** 獲取關聯地址，用於判斷多帳號操作

**返回格式：**
```python
['0xabc...', '0xdef...', '0x123...']
```

**實作示例：**
```python
def get_linked_addresses(self, address_id: int) -> List[str]:
    # 基於交易模式相似度、IP 地址、資金流向等判斷
    # 這需要你的系統有相應的分析邏輯
    
    query = """
        SELECT linked_address
        FROM address_links
        WHERE address_id = %s
    """
    result = self.db.execute(query, (address_id,))
    return [row['linked_address'] for row in result]
```

**如果沒有關聯分析：**
```python
def get_linked_addresses(self, address_id: int) -> List[str]:
    # 返回空列表，算法會跳過多帳號操作標籤
    return []
```

---

## 🔧 完整示例

### 示例 1：最小實作（只支持第一階段）

```python
from adapters.base import DataAdapter

class MinimalAdapter(DataAdapter):
    """最小實作：只支持第一階段標籤（19 種）"""
    
    # 不需要實作任何方法，所有方法都有默認實作
    pass

# 使用
service = AddressTaggingService(data_adapter=MinimalAdapter())
service.tag_all_addresses()  # 只會打第一階段的 19 種標籤
```

### 示例 2：支持第二階段（持倉數據）

```python
from adapters.base import DataAdapter

class Phase2Adapter(DataAdapter):
    """支持第二階段：持倉數據"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def get_price_history(self, market_id: int) -> List[Dict]:
        query = "SELECT * FROM market_prices WHERE market_id = %s"
        return self.db.execute(query, (market_id,))
    
    def get_position_changes(self, address_id: int) -> List[Dict]:
        query = "SELECT * FROM position_changes WHERE address_id = %s"
        return self.db.execute(query, (address_id,))

# 使用
adapter = Phase2Adapter(my_db_connection)
service = AddressTaggingService(data_adapter=adapter)
service.tag_all_addresses()  # 會打第一和第二階段的 34 種標籤
```

### 示例 3：完整實作（所有 50 種標籤）

```python
from adapters.base import DataAdapter
import requests
from datetime import datetime, timedelta

class FullAdapter(DataAdapter):
    """完整實作：支持所有 50 種標籤"""
    
    def __init__(self, db_connection, news_api_key, twitter_token):
        self.db = db_connection
        self.news_api_key = news_api_key
        self.twitter_token = twitter_token
    
    # 第二階段方法
    def get_price_history(self, market_id: int) -> List[Dict]:
        query = "SELECT * FROM market_prices WHERE market_id = %s"
        return self.db.execute(query, (market_id,))
    
    def get_position_changes(self, address_id: int) -> List[Dict]:
        query = "SELECT * FROM position_changes WHERE address_id = %s"
        return self.db.execute(query, (address_id,))
    
    # 第三階段方法
    def get_market_news(self, market_id: int, days: int = 7) -> List[Dict]:
        market = self.db.get_market(market_id)
        response = requests.get(
            'https://newsapi.org/v2/everything',
            params={
                'q': market['title'],
                'from': (datetime.now() - timedelta(days=days)).isoformat(),
                'apiKey': self.news_api_key
            }
        )
        return response.json()['articles']
    
    def get_address_social_activity(self, address: str) -> Dict:
        # 調用 Twitter API
        response = requests.get(
            'https://api.twitter.com/2/tweets/search/recent',
            params={'query': address},
            headers={'Authorization': f'Bearer {self.twitter_token}'}
        )
        return {
            'twitter_followers': 0,  # 需要進一步查詢
            'twitter_mentions': response.json()['meta']['result_count'],
            'discord_messages': 0,
            'is_verified': False
        }
    
    def get_trade_pattern_stats(self, address_id: int) -> Dict:
        # 計算交易模式統計
        trades = self.db.get_address_trades(address_id)
        # ... 計算邏輯
        return {
            'trade_time_variance': 500,
            'unique_trade_amounts': 3,
            'avg_response_time': 5
        }
    
    def get_linked_addresses(self, address_id: int) -> List[str]:
        query = "SELECT linked_address FROM address_links WHERE address_id = %s"
        return [row['linked_address'] for row in self.db.execute(query, (address_id,))]

# 使用
adapter = FullAdapter(my_db, news_api_key='xxx', twitter_token='yyy')
service = AddressTaggingService(data_adapter=adapter)
service.tag_all_addresses()  # 會打所有 50 種標籤
```

---

## 💡 最佳實踐

### 1. 錯誤處理

```python
def get_market_news(self, market_id: int, days: int = 7) -> List[Dict]:
    try:
        # 調用 API
        response = requests.get(...)
        return response.json()['articles']
    except Exception as e:
        # 記錄錯誤並返回空列表
        print(f"獲取新聞失敗：{e}")
        return []
```

### 2. 緩存

```python
class CachedAdapter(DataAdapter):
    def __init__(self):
        self.price_cache = {}
    
    def get_price_history(self, market_id: int) -> List[Dict]:
        if market_id not in self.price_cache:
            self.price_cache[market_id] = self._fetch_price_history(market_id)
        return self.price_cache[market_id]
```

### 3. 批量查詢

```python
def get_price_history_batch(self, market_ids: List[int]) -> Dict[int, List[Dict]]:
    """批量獲取多個市場的價格歷史"""
    query = "SELECT * FROM market_prices WHERE market_id IN %s"
    result = self.db.execute(query, (tuple(market_ids),))
    
    # 按 market_id 分組
    grouped = {}
    for row in result:
        market_id = row['market_id']
        if market_id not in grouped:
            grouped[market_id] = []
        grouped[market_id].append(row)
    
    return grouped
```

---

## 🚀 測試你的適配器

### 1. 單元測試

```python
import unittest
from my_adapter import MyAdapter

class TestMyAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = MyAdapter()
    
    def test_get_price_history(self):
        result = self.adapter.get_price_history(123)
        self.assertIsInstance(result, list)
        if result:
            self.assertIn('timestamp', result[0])
            self.assertIn('price', result[0])
    
    def test_get_position_changes(self):
        result = self.adapter.get_position_changes(456)
        self.assertIsInstance(result, list)

if __name__ == '__main__':
    unittest.main()
```

### 2. 整合測試

```python
# 測試單個地址
service = AddressTaggingService(data_adapter=MyAdapter())
tags = service.tag_address(123)
print(f"獲得 {len(tags)} 個標籤")

# 測試小批量
stats = service.tag_all_addresses(limit=10)
print(f"處理了 {stats['tagged_addresses']} 個地址")
```

---

## ❓ 常見問題

### Q1: 我沒有新聞 API，能用嗎？

**A:** 可以！只需要讓相關方法返回空列表，算法會自動跳過需要新聞的標籤。

```python
def get_market_news(self, market_id: int, days: int = 7) -> List[Dict]:
    return []  # 算法會跳過「事件驅動」「新聞追蹤」「疑似內線」標籤
```

### Q2: 我的數據結構和你的不一樣怎麼辦？

**A:** 在適配器中轉換格式即可。

```python
def get_price_history(self, market_id: int) -> List[Dict]:
    # 你的數據格式
    my_data = self.db.query("SELECT time, yes_price, vol FROM prices WHERE mid = %s", market_id)
    
    # 轉換為算法需要的格式
    return [
        {
            'timestamp': row['time'],
            'price': row['yes_price'],
            'volume': row['vol']
        }
        for row in my_data
    ]
```

### Q3: 性能會不會很慢？

**A:** 建議使用緩存和批量查詢：

```python
class OptimizedAdapter(DataAdapter):
    def __init__(self):
        self.cache = {}
    
    def get_price_history(self, market_id: int) -> List[Dict]:
        if market_id not in self.cache:
            self.cache[market_id] = self._fetch_from_db(market_id)
        return self.cache[market_id]
```

### Q4: 可以只實作部分方法嗎？

**A:** 可以！未實作的方法會使用默認實作（返回空數據），算法會自動跳過相關標籤。

---

## 📚 參考資料

- [adapters/base.py](adapters/base.py) - 數據適配器基類
- [adapters/mock.py](adapters/mock.py) - 模擬數據適配器示例
- [ADDRESS_TAGGING_SYSTEM.md](ADDRESS_TAGGING_SYSTEM.md) - 完整的標籤體系和篩選邏輯
- [README.md](README.md) - 項目概述和快速開始

---

## 💬 需要幫助？

如果你在實作適配器時遇到問題，可以：

1. 查看 `adapters/mock.py` 的示例代碼
2. 參考上面的完整示例
3. 提交 Issue 或 Pull Request
