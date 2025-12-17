"""
模擬數據適配器

提供模擬數據供測試使用。
主管可以參考此實作來實作真實的數據適配器。
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random
from .base import DataAdapter


class MockDataAdapter(DataAdapter):
    """
    模擬數據適配器
    
    用於測試和演示。生成隨機但合理的模擬數據。
    """
    
    def __init__(self):
        """初始化模擬數據"""
        self.mock_data_cache = {}
    
    # ==================== 第二階段：持倉數據 ====================
    
    def get_holding_period(self, trade_id: int) -> Optional[int]:
        """
        返回模擬的持倉時長
        
        模擬策略：
        - 30% 的交易：短期持倉（< 1 天）
        - 40% 的交易：中期持倉（1-7 天）
        - 30% 的交易：長期持倉（> 7 天）
        """
        random.seed(trade_id)  # 確保同一 trade_id 返回相同結果
        
        rand = random.random()
        if rand < 0.3:
            # 短期持倉：1 小時 - 24 小時
            return random.randint(3600, 86400)
        elif rand < 0.7:
            # 中期持倉：1 天 - 7 天
            return random.randint(86400, 604800)
        else:
            # 長期持倉：7 天 - 30 天
            return random.randint(604800, 2592000)
    
    def get_trade_timestamps(self, address_id: int) -> List[Dict[str, Any]]:
        """
        返回模擬的交易時間戳
        
        模擬策略：
        - 生成 10-50 筆交易
        - 交易時間隨機分布在最近 3 個月
        """
        random.seed(address_id)
        
        num_trades = random.randint(10, 50)
        now = datetime.now()
        trades = []
        
        for i in range(num_trades):
            # 隨機生成進場時間（最近 3 個月）
            days_ago = random.randint(0, 90)
            entry_time = now - timedelta(days=days_ago)
            
            # 隨機生成市場創建時間（進場前 1-30 天）
            market_created_days_before = random.randint(1, 30)
            market_created_at = entry_time - timedelta(days=market_created_days_before)
            
            # 隨機生成市場結算時間（進場後 1-60 天）
            market_end_days_after = random.randint(1, 60)
            market_end_date = entry_time + timedelta(days=market_end_days_after)
            
            # 50% 的交易已平倉
            exit_time = None
            if random.random() < 0.5:
                holding_days = random.randint(1, min(30, market_end_days_after))
                exit_time = entry_time + timedelta(days=holding_days)
            
            trades.append({
                'trade_id': address_id * 1000 + i,
                'entry_time': entry_time,
                'exit_time': exit_time,
                'market_created_at': market_created_at,
                'market_end_date': market_end_date
            })
        
        return trades
    
    def get_position_changes(self, address_id: int) -> List[Dict[str, Any]]:
        """
        返回模擬的持倉變化記錄
        
        模擬策略：
        - 生成 20-100 筆持倉變化
        - 包含買入和賣出
        """
        random.seed(address_id)
        
        num_changes = random.randint(20, 100)
        now = datetime.now()
        changes = []
        
        for i in range(num_changes):
            days_ago = random.randint(0, 90)
            timestamp = now - timedelta(days=days_ago, hours=random.randint(0, 23))
            
            changes.append({
                'market_id': random.randint(1, 100),
                'timestamp': timestamp,
                'side': random.choice(['buy', 'sell']),
                'amount': random.uniform(100, 10000),
                'outcome': random.choice(['Yes', 'No'])
            })
        
        # 按時間排序
        changes.sort(key=lambda x: x['timestamp'])
        return changes
    
    # ==================== 第三階段：外部數據 ====================
    
    def get_market_news(self, market_id: int, days: int = 7) -> List[Dict[str, Any]]:
        """
        返回模擬的市場新聞
        
        模擬策略：
        - 20% 的市場有新聞
        - 有新聞的市場返回 1-5 條新聞
        """
        random.seed(market_id)
        
        # 80% 的市場沒有新聞
        if random.random() > 0.2:
            return []
        
        num_news = random.randint(1, 5)
        now = datetime.now()
        news = []
        
        for i in range(num_news):
            days_ago = random.randint(0, days)
            published_at = now - timedelta(days=days_ago)
            
            news.append({
                'title': f'Mock News {i+1} for Market {market_id}',
                'published_at': published_at,
                'source': random.choice(['CNN', 'BBC', 'Reuters', 'Bloomberg'])
            })
        
        return news
    
    def get_address_social_activity(self, address: str) -> Dict[str, Any]:
        """
        返回模擬的社交媒體活動
        
        模擬策略：
        - 10% 的地址有社交媒體活動
        - 5% 的地址是 KOL
        """
        # 使用地址的哈希值作為種子
        seed = sum(ord(c) for c in address)
        random.seed(seed)
        
        # 90% 的地址沒有社交媒體活動
        if random.random() > 0.1:
            return {
                'twitter_followers': 0,
                'twitter_mentions': 0,
                'discord_messages': 0,
                'is_verified': False
            }
        
        # 5% 的地址是 KOL
        is_kol = random.random() < 0.5
        
        if is_kol:
            return {
                'twitter_followers': random.randint(10000, 100000),
                'twitter_mentions': random.randint(100, 1000),
                'discord_messages': random.randint(50, 500),
                'is_verified': True
            }
        else:
            return {
                'twitter_followers': random.randint(100, 5000),
                'twitter_mentions': random.randint(10, 100),
                'discord_messages': random.randint(5, 50),
                'is_verified': False
            }
    
    def get_price_history(self, market_id: int) -> List[Dict[str, Any]]:
        """
        返回模擬的價格歷史
        
        模擬策略：
        - 生成最近 30 天的每日價格
        - 價格在 0.3-0.7 之間隨機波動
        """
        random.seed(market_id)
        
        now = datetime.now()
        history = []
        current_price = random.uniform(0.4, 0.6)
        
        for i in range(30):
            days_ago = 30 - i
            timestamp = now - timedelta(days=days_ago)
            
            # 價格隨機波動 ±5%
            price_change = random.uniform(-0.05, 0.05)
            current_price = max(0.01, min(0.99, current_price + price_change))
            
            history.append({
                'timestamp': timestamp,
                'price': current_price,
                'volume': random.uniform(1000, 100000)
            })
        
        return history
    
    def get_trade_pattern_stats(self, address_id: int) -> Dict[str, Any]:
        """
        返回模擬的交易模式統計
        
        模擬策略：
        - 10% 的地址是機器人（低方差）
        - 90% 的地址是人類（高方差）
        """
        random.seed(address_id)
        
        is_bot = random.random() < 0.1
        
        if is_bot:
            # 機器人：低方差，固定金額
            return {
                'trade_time_variance': random.uniform(100, 1000),  # 低方差
                'trade_amount_variance': random.uniform(10, 100),  # 低方差
                'unique_trade_amounts': random.randint(1, 3),  # 少量不同金額
                'avg_response_time': random.uniform(1, 5)  # 快速響應
            }
        else:
            # 人類：高方差，多樣金額
            return {
                'trade_time_variance': random.uniform(10000, 100000),  # 高方差
                'trade_amount_variance': random.uniform(1000, 10000),  # 高方差
                'unique_trade_amounts': random.randint(10, 50),  # 多種不同金額
                'avg_response_time': random.uniform(60, 600)  # 較慢響應
            }
    
    def get_linked_addresses(self, address_id: int) -> List[int]:
        """
        返回模擬的關聯地址
        
        模擬策略：
        - 5% 的地址有關聯地址（多帳號）
        - 有關聯的地址返回 1-5 個關聯地址
        """
        random.seed(address_id)
        
        # 95% 的地址沒有關聯地址
        if random.random() > 0.05:
            return []
        
        num_linked = random.randint(1, 5)
        return [address_id + i + 1 for i in range(num_linked)]
