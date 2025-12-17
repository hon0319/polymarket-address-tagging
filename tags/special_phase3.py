"""
特殊標記標籤器（第三階段）

新增標籤：
- 疑似內線
- 新聞追蹤
- 名人
- 機器人/腳本
- 多帳號操作
- 市場操縱嫌疑
- 專業機構
- 新手
- 休眠喚醒
- 單一市場專注

需要數據：
- 新聞 API、社交媒體 API、交易模式分析
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
import statistics


class SpecialPhase3Tagger:
    """特殊標記標籤器（第三階段）"""
    
    def __init__(self, db, data_adapter, config: Dict[str, Any], confidence_calc):
        self.db = db
        self.data_adapter = data_adapter
        self.config = config['tags']['特殊標記']
        self.confidence_calc = confidence_calc
    
    def tag(self, address_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """為地址打上特殊標記標籤（第三階段）"""
        tags = []
        address_id = address_data['id']
        address = address_data.get('address', '')
        
        # 疑似內線
        if self.config['疑似內線']['enabled']:
            tag = self._tag_insider(address_id)
            if tag:
                tags.append(tag)
        
        # 新聞追蹤
        if self.config['新聞追蹤']['enabled']:
            tag = self._tag_news_trader(address_id)
            if tag:
                tags.append(tag)
        
        # 名人
        if self.config['名人']['enabled']:
            tag = self._tag_celebrity(address)
            if tag:
                tags.append(tag)
        
        # 機器人/腳本
        if self.config['機器人/腳本']['enabled']:
            tag = self._tag_bot(address_id)
            if tag:
                tags.append(tag)
        
        # 多帳號操作
        if self.config['多帳號操作']['enabled']:
            tag = self._tag_multi_account(address_id)
            if tag:
                tags.append(tag)
        
        # 市場操縱嫌疑
        if self.config['市場操縱嫌疑']['enabled']:
            tag = self._tag_manipulation(address_id)
            if tag:
                tags.append(tag)
        
        # 專業機構
        if self.config['專業機構']['enabled']:
            tag = self._tag_institution(address_id, address_data)
            if tag:
                tags.append(tag)
        
        # 新手
        if self.config['新手']['enabled']:
            tag = self._tag_newbie(address_id, address_data)
            if tag:
                tags.append(tag)
        
        # 休眠喚醒
        if self.config['休眠喚醒']['enabled']:
            tag = self._tag_dormant_awakened(address_id)
            if tag:
                tags.append(tag)
        
        # 單一市場專注
        if self.config['單一市場專注']['enabled']:
            tag = self._tag_single_market_focus(address_id)
            if tag:
                tags.append(tag)
        
        return tags
    
    def _tag_insider(self, address_id: int) -> Dict[str, Any]:
        """
        疑似內線標籤
        
        條件：
        - 在重大事件前大額交易
        - 勝率異常高（> 80%）
        - 交易時機精準
        """
        cfg = self.config['疑似內線']
        
        try:
            trades = self.db.get_address_trades(address_id)
            address_data = self.db.get_address(address_id)
            
            if len(trades) < cfg['min_trades']:
                return None
            
            if address_data['win_rate'] < cfg['min_win_rate']:
                return None
            
            # 檢查交易是否在重大新聞前
            early_trades_count = 0
            for trade in trades:
                news = self.data_adapter.get_market_news(trade['market_id'], days=3)
                if not news:
                    continue
                
                # 檢查是否在新聞發布前交易
                for article in news:
                    time_diff = (article['published_at'] - trade['timestamp']).total_seconds()
                    if 0 < time_diff < 86400:  # 在新聞前 1 天內交易
                        early_trades_count += 1
                        break
            
            early_ratio = early_trades_count / len(trades)
            
            if early_ratio >= cfg['early_trade_ratio_threshold']:
                confidence = min(1.0, address_data['win_rate'] * early_ratio)
                
                return {
                    'category': '特殊標記',
                    'tag_name': '疑似內線',
                    'confidence_score': confidence
                }
        
        except (NotImplementedError, Exception):
            return self._tag_insider_simplified(address_id)
        
        return None
    
    def _tag_news_trader(self, address_id: int) -> Dict[str, Any]:
        """
        新聞追蹤標籤
        
        條件：
        - 交易時間與新聞發布高度相關
        - 在新聞後短時間內交易
        """
        cfg = self.config['新聞追蹤']
        
        try:
            trades = self.db.get_address_trades(address_id)
            if len(trades) < cfg['min_trades']:
                return None
            
            news_driven_count = 0
            for trade in trades:
                news = self.data_adapter.get_market_news(trade['market_id'], days=1)
                if not news:
                    continue
                
                # 檢查是否在新聞發布後短時間內交易
                for article in news:
                    time_diff = (trade['timestamp'] - article['published_at']).total_seconds()
                    if 0 < time_diff < 3600:  # 新聞後 1 小時內
                        news_driven_count += 1
                        break
            
            news_ratio = news_driven_count / len(trades)
            
            if news_ratio >= cfg['news_ratio_threshold']:
                confidence = self.confidence_calc.calculate(
                    news_ratio,
                    cfg['news_ratio_threshold'],
                    1.0
                )
                
                return {
                    'category': '特殊標記',
                    'tag_name': '新聞追蹤',
                    'confidence_score': confidence
                }
        
        except (NotImplementedError, Exception):
            return None
        
        return None
    
    def _tag_celebrity(self, address: str) -> Dict[str, Any]:
        """
        名人標籤
        
        條件：
        - Twitter 粉絲 > 10,000
        - 已驗證帳號
        """
        cfg = self.config['名人']
        
        try:
            social_data = self.data_adapter.get_address_social_activity(address)
            
            if (social_data['twitter_followers'] >= cfg['min_followers'] and
                social_data['is_verified']):
                
                # 根據粉絲數計算信心分數
                confidence = min(1.0, social_data['twitter_followers'] / 100000)
                
                return {
                    'category': '特殊標記',
                    'tag_name': '名人',
                    'confidence_score': confidence
                }
        
        except (NotImplementedError, Exception):
            return None
        
        return None
    
    def _tag_bot(self, address_id: int) -> Dict[str, Any]:
        """
        機器人/腳本標籤
        
        條件：
        - 交易時間規律（低方差）
        - 交易金額固定
        - 響應時間極快
        """
        cfg = self.config['機器人/腳本']
        
        try:
            stats = self.data_adapter.get_trade_pattern_stats(address_id)
            
            is_bot = (
                stats['trade_time_variance'] < cfg['max_time_variance'] and
                stats['unique_trade_amounts'] < cfg['max_unique_amounts'] and
                stats['avg_response_time'] < cfg['max_response_time']
            )
            
            if is_bot:
                # 根據規律性計算信心分數
                time_score = 1.0 - (stats['trade_time_variance'] / cfg['max_time_variance'])
                amount_score = 1.0 - (stats['unique_trade_amounts'] / cfg['max_unique_amounts'])
                response_score = 1.0 - (stats['avg_response_time'] / cfg['max_response_time'])
                
                confidence = (time_score + amount_score + response_score) / 3
                
                return {
                    'category': '特殊標記',
                    'tag_name': '機器人/腳本',
                    'confidence_score': confidence
                }
        
        except (NotImplementedError, Exception):
            return self._tag_bot_simplified(address_id)
        
        return None
    
    def _tag_multi_account(self, address_id: int) -> Dict[str, Any]:
        """
        多帳號操作標籤
        
        條件：
        - 有關聯地址
        - 交易模式相似
        """
        cfg = self.config['多帳號操作']
        
        try:
            linked_addresses = self.data_adapter.get_linked_addresses(address_id)
            
            if len(linked_addresses) >= cfg['min_linked_accounts']:
                confidence = min(1.0, len(linked_addresses) / 10)
                
                return {
                    'category': '特殊標記',
                    'tag_name': '多帳號操作',
                    'confidence_score': confidence
                }
        
        except (NotImplementedError, Exception):
            return None
        
        return None
    
    def _tag_manipulation(self, address_id: int) -> Dict[str, Any]:
        """
        市場操縱嫌疑標籤
        
        條件：
        - 大額交易影響價格
        - 短時間內反向操作
        - 異常交易模式
        """
        cfg = self.config['市場操縱嫌疑']
        
        try:
            trades = self.db.get_address_trades(address_id)
            address_data = self.db.get_address(address_id)
            
            if len(trades) < cfg['min_trades']:
                return None
            
            # 檢查大額交易佔比
            large_trades = sum(1 for t in trades if t['amount'] and t['amount'] > cfg['large_trade_threshold'])
            large_ratio = large_trades / len(trades)
            
            # 檢查反向操作
            position_changes = self.data_adapter.get_position_changes(address_id)
            reverse_ops = 0
            for i in range(len(position_changes) - 1):
                if position_changes[i]['side'] != position_changes[i+1]['side']:
                    time_diff = (position_changes[i+1]['timestamp'] - position_changes[i]['timestamp']).total_seconds()
                    if time_diff < 3600:  # 1 小時內反向
                        reverse_ops += 1
            
            reverse_ratio = reverse_ops / len(position_changes) if position_changes else 0
            
            if (large_ratio >= cfg['large_trade_ratio_threshold'] and
                reverse_ratio >= cfg['reverse_op_ratio_threshold']):
                
                confidence = (large_ratio + reverse_ratio) / 2
                
                return {
                    'category': '特殊標記',
                    'tag_name': '市場操縱嫌疑',
                    'confidence_score': confidence
                }
        
        except (NotImplementedError, Exception):
            return self._tag_manipulation_simplified(address_id)
        
        return None
    
    def _tag_institution(self, address_id: int, address_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        專業機構標籤
        
        條件：
        - 交易量極大（> $500K）
        - 勝率穩定（> 65%）
        - 交易次數多
        """
        cfg = self.config['專業機構']
        
        if (address_data['total_volume'] >= cfg['min_total_volume'] and
            address_data['win_rate'] >= cfg['min_win_rate'] and
            address_data['total_trades'] >= cfg['min_trades']):
            
            # 根據交易量計算信心分數
            confidence = min(1.0, address_data['total_volume'] / 1000000)
            
            return {
                'category': '特殊標記',
                'tag_name': '專業機構',
                'confidence_score': confidence
            }
        
        return None
    
    def _tag_newbie(self, address_id: int, address_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        新手標籤
        
        條件：
        - 註冊時間 < 30 天
        - 交易次數 < 10
        """
        cfg = self.config['新手']
        
        trades = self.db.get_address_trades(address_id)
        if not trades:
            return None
        
        first_trade_date = min(t['timestamp'] for t in trades)
        days_since_first_trade = (datetime.now() - first_trade_date).days
        
        if (days_since_first_trade <= cfg['max_days_since_first_trade'] and
            address_data['total_trades'] <= cfg['max_trades']):
            
            confidence = 1.0 - (days_since_first_trade / cfg['max_days_since_first_trade']) * 0.5 + 0.5
            
            return {
                'category': '特殊標記',
                'tag_name': '新手',
                'confidence_score': confidence
            }
        
        return None
    
    def _tag_dormant_awakened(self, address_id: int) -> Dict[str, Any]:
        """
        休眠喚醒標籤
        
        條件：
        - 長期不活躍（> 90 天）
        - 最近突然大量交易
        """
        cfg = self.config['休眠喚醒']
        
        trades = self.db.get_address_trades(address_id)
        if len(trades) < 2:
            return None
        
        # 按時間排序
        sorted_trades = sorted(trades, key=lambda x: x['timestamp'])
        
        # 檢查是否有長時間間隔
        max_gap_days = 0
        for i in range(len(sorted_trades) - 1):
            gap = (sorted_trades[i+1]['timestamp'] - sorted_trades[i]['timestamp']).days
            max_gap_days = max(max_gap_days, gap)
        
        # 檢查最近活躍度
        recent_trades = self.db.get_recent_trades_count(address_id, 30)
        
        if (max_gap_days >= cfg['min_dormant_days'] and
            recent_trades >= cfg['min_recent_trades']):
            
            confidence = min(1.0, max_gap_days / 180)
            
            return {
                'category': '特殊標記',
                'tag_name': '休眠喚醒',
                'confidence_score': confidence
            }
        
        return None
    
    def _tag_single_market_focus(self, address_id: int) -> Dict[str, Any]:
        """
        單一市場專注標籤
        
        條件：
        - 90% 以上交易集中在單一市場
        """
        cfg = self.config['單一市場專注']
        
        trades = self.db.get_address_trades(address_id)
        if len(trades) < cfg['min_trades']:
            return None
        
        # 統計每個市場的交易次數
        market_counts = {}
        for trade in trades:
            market_id = trade['market_id']
            market_counts[market_id] = market_counts.get(market_id, 0) + 1
        
        # 找出最多交易的市場
        max_market_count = max(market_counts.values())
        focus_ratio = max_market_count / len(trades)
        
        if focus_ratio >= cfg['focus_ratio_threshold']:
            confidence = self.confidence_calc.calculate(
                focus_ratio,
                cfg['focus_ratio_threshold'],
                1.0
            )
            
            return {
                'category': '特殊標記',
                'tag_name': '單一市場專注',
                'confidence_score': confidence
            }
        
        return None
    
    # ==================== 簡化版邏輯 ====================
    
    def _tag_insider_simplified(self, address_id: int) -> Dict[str, Any]:
        """疑似內線標籤（簡化版）- 僅基於勝率"""
        address_data = self.db.get_address(address_id)
        
        if (address_data['win_rate'] >= 0.80 and
            address_data['total_trades'] >= 10):
            
            return {
                'category': '特殊標記',
                'tag_name': '疑似內線',
                'confidence_score': 0.5  # 簡化版信心分數較低
            }
        
        return None
    
    def _tag_bot_simplified(self, address_id: int) -> Dict[str, Any]:
        """機器人/腳本標籤（簡化版）- 基於交易頻率和金額"""
        trades = self.db.get_address_trades(address_id)
        if len(trades) < 20:
            return None
        
        # 檢查交易金額是否固定
        amounts = [t['amount'] for t in trades if t['amount']]
        if not amounts:
            return None
        
        unique_amounts = len(set(round(a, 2) for a in amounts))
        
        # 檢查交易頻率
        recent_trades = self.db.get_recent_trades_count(address_id, 7)
        
        if unique_amounts <= 3 and recent_trades >= 20:
            return {
                'category': '特殊標記',
                'tag_name': '機器人/腳本',
                'confidence_score': 0.6
            }
        
        return None
    
    def _tag_manipulation_simplified(self, address_id: int) -> Dict[str, Any]:
        """市場操縱嫌疑標籤（簡化版）- 基於大額交易"""
        trades = self.db.get_address_trades(address_id)
        address_data = self.db.get_address(address_id)
        
        if len(trades) < 5:
            return None
        
        # 檢查大額交易佔比
        large_trades = sum(1 for t in trades if t['amount'] and t['amount'] > 50000)
        large_ratio = large_trades / len(trades)
        
        if large_ratio >= 0.5 and address_data['total_volume'] >= 500000:
            return {
                'category': '特殊標記',
                'tag_name': '市場操縱嫌疑',
                'confidence_score': 0.5
            }
        
        return None
