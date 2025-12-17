"""
數據適配器基礎類

定義了第二和第三階段需要的數據接口。
主管需要繼承此類並實作這些方法，連接到真實數據源。
"""

from typing import List, Dict, Any, Optional
from datetime import datetime


class DataAdapter:
    """
    數據適配器基礎類
    
    主管需要繼承此類並實作以下方法：
    - 第二階段方法：get_holding_period, get_trade_timestamps
    - 第三階段方法：get_market_news, get_address_social_activity, get_price_history
    """
    
    # ==================== 第二階段：持倉數據 ====================
    
    def get_holding_period(self, trade_id: int) -> Optional[int]:
        """
        獲取交易的持倉時長（秒）
        
        Args:
            trade_id: 交易 ID
            
        Returns:
            持倉時長（秒），如果交易未平倉則返回 None
            
        實作建議：
            # 如果有 exit_timestamp
            trade = db.query("SELECT entry_time, exit_timestamp FROM trades WHERE id = ?", trade_id)
            if trade.exit_timestamp:
                return (trade.exit_timestamp - trade.entry_time).total_seconds()
            
            # 如果沒有 exit_timestamp，使用市場結算時間
            trade = db.query("SELECT entry_time, market_end_date FROM trades WHERE id = ?", trade_id)
            return (trade.market_end_date - trade.entry_time).total_seconds()
        """
        raise NotImplementedError("主管需要實作此方法")
    
    def get_trade_timestamps(self, address_id: int) -> List[Dict[str, Any]]:
        """
        獲取地址的所有交易時間戳
        
        Args:
            address_id: 地址 ID
            
        Returns:
            交易時間戳列表，每個元素包含：
            {
                'trade_id': int,
                'entry_time': datetime,
                'exit_time': datetime or None,
                'market_created_at': datetime,
                'market_end_date': datetime
            }
            
        實作建議：
            return db.query('''
                SELECT 
                    t.id as trade_id,
                    t.timestamp as entry_time,
                    t.exit_timestamp as exit_time,
                    m.created_at as market_created_at,
                    m.end_date as market_end_date
                FROM address_trades t
                JOIN markets m ON t.market_id = m.id
                WHERE t.address_id = ?
            ''', address_id)
        """
        raise NotImplementedError("主管需要實作此方法")
    
    def get_position_changes(self, address_id: int) -> List[Dict[str, Any]]:
        """
        獲取地址的持倉變化記錄（用於對沖檢測）
        
        Args:
            address_id: 地址 ID
            
        Returns:
            持倉變化列表，每個元素包含：
            {
                'market_id': int,
                'timestamp': datetime,
                'side': str,  # 'buy' or 'sell'
                'amount': float,
                'outcome': str  # 'Yes' or 'No'
            }
            
        實作建議：
            return db.query('''
                SELECT 
                    market_id,
                    timestamp,
                    side,
                    amount,
                    outcome
                FROM address_trades
                WHERE address_id = ?
                ORDER BY timestamp
            ''', address_id)
        """
        raise NotImplementedError("主管需要實作此方法")
    
    # ==================== 第三階段：外部數據 ====================
    
    def get_market_news(self, market_id: int, days: int = 7) -> List[Dict[str, Any]]:
        """
        獲取市場相關新聞（最近 N 天）
        
        Args:
            market_id: 市場 ID
            days: 查詢最近幾天的新聞
            
        Returns:
            新聞列表，每個元素包含：
            {
                'title': str,
                'published_at': datetime,
                'source': str
            }
            
        實作建議：
            # 如果有新聞 API
            market = db.query("SELECT title FROM markets WHERE id = ?", market_id)
            response = requests.get(f"https://api.news.com/search?q={market.title}&days={days}")
            return response.json()
            
            # 如果沒有新聞 API，返回空列表（算法會使用簡化邏輯）
            return []
        """
        # 默認返回空列表，使用簡化邏輯
        return []
    
    def get_address_social_activity(self, address: str) -> Dict[str, Any]:
        """
        獲取地址的社交媒體活動
        
        Args:
            address: 地址（0x...）
            
        Returns:
            社交媒體活動數據：
            {
                'twitter_followers': int,
                'twitter_mentions': int,
                'discord_messages': int,
                'is_verified': bool
            }
            
        實作建議：
            # 如果有 Twitter API
            response = requests.get(f"https://api.twitter.com/users/search?q={address}")
            return {
                'twitter_followers': response.json()['followers_count'],
                'twitter_mentions': response.json()['mentions_count'],
                'discord_messages': 0,
                'is_verified': response.json()['verified']
            }
            
            # 如果沒有 API，返回默認值（算法會使用簡化邏輯）
            return {'twitter_followers': 0, 'twitter_mentions': 0, 'discord_messages': 0, 'is_verified': False}
        """
        # 默認返回空數據，使用簡化邏輯
        return {
            'twitter_followers': 0,
            'twitter_mentions': 0,
            'discord_messages': 0,
            'is_verified': False
        }
    
    def get_price_history(self, market_id: int) -> List[Dict[str, Any]]:
        """
        獲取市場的價格歷史（用於趨勢分析）
        
        Args:
            market_id: 市場 ID
            
        Returns:
            價格歷史列表，每個元素包含：
            {
                'timestamp': datetime,
                'price': float,
                'volume': float
            }
            
        實作建議：
            return db.query('''
                SELECT timestamp, price, volume
                FROM market_price_history
                WHERE market_id = ?
                ORDER BY timestamp
            ''', market_id)
            
            # 如果沒有價格歷史表，返回空列表（算法會使用簡化邏輯）
            return []
        """
        # 默認返回空列表，使用簡化邏輯
        return []
    
    def get_trade_pattern_stats(self, address_id: int) -> Dict[str, Any]:
        """
        獲取地址的交易模式統計（用於機器人檢測）
        
        Args:
            address_id: 地址 ID
            
        Returns:
            交易模式統計：
            {
                'trade_time_variance': float,  # 交易時間方差（秒）
                'trade_amount_variance': float,  # 交易金額方差
                'unique_trade_amounts': int,  # 不同交易金額的數量
                'avg_response_time': float  # 平均響應時間（秒）
            }
            
        實作建議：
            stats = db.query('''
                SELECT 
                    VARIANCE(UNIX_TIMESTAMP(timestamp)) as trade_time_variance,
                    VARIANCE(amount) as trade_amount_variance,
                    COUNT(DISTINCT amount) as unique_trade_amounts
                FROM address_trades
                WHERE address_id = ?
            ''', address_id)
            return stats
        """
        raise NotImplementedError("主管需要實作此方法")
    
    def get_linked_addresses(self, address_id: int) -> List[int]:
        """
        獲取與此地址關聯的其他地址（用於多帳號檢測）
        
        Args:
            address_id: 地址 ID
            
        Returns:
            關聯地址 ID 列表
            
        實作建議：
            # 基於相同 IP、相同設備指紋、資金轉移等檢測
            # 這需要額外的數據收集和分析
            return []  # 如果沒有此數據，返回空列表
        """
        # 默認返回空列表
        return []
