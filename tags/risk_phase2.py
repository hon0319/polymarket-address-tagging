"""
風險偏好標籤器（第二階段）

新增標籤：
- 均衡型
- 保守型
- 激進型

需要數據：
- 持倉時長和價格分布（通過 DataAdapter 獲取）
"""

from typing import List, Dict, Any
import statistics


class RiskPhase2Tagger:
    """風險偏好標籤器（第二階段）"""
    
    def __init__(self, db, data_adapter, config: Dict[str, Any], confidence_calc):
        self.db = db
        self.data_adapter = data_adapter
        self.config = config['tags']['風險偏好']
        self.confidence_calc = confidence_calc
    
    def tag(self, address_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """為地址打上風險偏好標籤（第二階段）"""
        tags = []
        address_id = address_data['id']
        
        # 均衡型
        if self.config['均衡型']['enabled']:
            tag = self._tag_balanced(address_id)
            if tag:
                tags.append(tag)
        
        # 保守型
        if self.config['保守型']['enabled']:
            tag = self._tag_conservative(address_id)
            if tag:
                tags.append(tag)
        
        # 激進型
        if self.config['激進型']['enabled']:
            tag = self._tag_aggressive(address_id)
            if tag:
                tags.append(tag)
        
        return tags
    
    def _tag_balanced(self, address_id: int) -> Dict[str, Any]:
        """
        均衡型標籤
        
        條件：
        - 價格分布均勻（0.3-0.7 之間）
        - 持倉時長適中（7-30 天）
        - 交易金額適中
        """
        cfg = self.config['均衡型']
        
        try:
            # 獲取交易價格分布
            trades = self.db.get_address_trades(address_id)
            if len(trades) < cfg['min_trades']:
                return None
            
            prices = [t['price'] for t in trades if t['price']]
            if not prices:
                return None
            
            # 計算價格分布
            price_in_range = sum(1 for p in prices if cfg['price_range_min'] <= p <= cfg['price_range_max'])
            price_ratio = price_in_range / len(prices)
            
            # 獲取持倉時長
            timestamps = self.data_adapter.get_trade_timestamps(address_id)
            holding_periods = []
            for trade in timestamps:
                if trade['exit_time']:
                    holding_days = (trade['exit_time'] - trade['entry_time']).days
                    holding_periods.append(holding_days)
            
            if not holding_periods:
                return None
            
            avg_holding_days = statistics.mean(holding_periods)
            
            # 判斷是否均衡型
            if (price_ratio >= cfg['price_ratio_threshold'] and
                cfg['holding_days_min'] <= avg_holding_days <= cfg['holding_days_max']):
                
                confidence = price_ratio * 0.7 + 0.3
                
                return {
                    'category': '風險偏好',
                    'tag_name': '均衡型',
                    'confidence_score': confidence
                }
        
        except NotImplementedError:
            return self._tag_balanced_simplified(address_id)
        
        return None
    
    def _tag_conservative(self, address_id: int) -> Dict[str, Any]:
        """
        保守型標籤
        
        條件：
        - 主要交易高概率市場（價格 > 0.7）
        - 持倉時長較長（> 14 天）
        - 交易金額較小
        """
        cfg = self.config['保守型']
        
        try:
            trades = self.db.get_address_trades(address_id)
            if len(trades) < cfg['min_trades']:
                return None
            
            # 計算高概率交易佔比
            high_prob_trades = sum(1 for t in trades if t['price'] and t['price'] > cfg['price_threshold'])
            high_prob_ratio = high_prob_trades / len(trades)
            
            # 獲取持倉時長
            timestamps = self.data_adapter.get_trade_timestamps(address_id)
            holding_periods = []
            for trade in timestamps:
                if trade['exit_time']:
                    holding_days = (trade['exit_time'] - trade['entry_time']).days
                    holding_periods.append(holding_days)
            
            if not holding_periods:
                return None
            
            avg_holding_days = statistics.mean(holding_periods)
            
            # 判斷是否保守型
            if (high_prob_ratio >= cfg['high_prob_ratio_threshold'] and
                avg_holding_days >= cfg['min_holding_days']):
                
                confidence = high_prob_ratio * 0.7 + 0.3
                
                return {
                    'category': '風險偏好',
                    'tag_name': '保守型',
                    'confidence_score': confidence
                }
        
        except NotImplementedError:
            return self._tag_conservative_simplified(address_id)
        
        return None
    
    def _tag_aggressive(self, address_id: int) -> Dict[str, Any]:
        """
        激進型標籤
        
        條件：
        - 主要交易低概率市場（價格 < 0.3）
        - 持倉時長較短（< 7 天）
        - 交易金額較大
        """
        cfg = self.config['激進型']
        
        try:
            trades = self.db.get_address_trades(address_id)
            if len(trades) < cfg['min_trades']:
                return None
            
            # 計算低概率交易佔比
            low_prob_trades = sum(1 for t in trades if t['price'] and t['price'] < cfg['price_threshold'])
            low_prob_ratio = low_prob_trades / len(trades)
            
            # 獲取持倉時長
            timestamps = self.data_adapter.get_trade_timestamps(address_id)
            holding_periods = []
            for trade in timestamps:
                if trade['exit_time']:
                    holding_days = (trade['exit_time'] - trade['entry_time']).days
                    holding_periods.append(holding_days)
            
            if not holding_periods:
                return None
            
            avg_holding_days = statistics.mean(holding_periods)
            
            # 判斷是否激進型
            if (low_prob_ratio >= cfg['low_prob_ratio_threshold'] and
                avg_holding_days <= cfg['max_holding_days']):
                
                confidence = low_prob_ratio * 0.7 + 0.3
                
                return {
                    'category': '風險偏好',
                    'tag_name': '激進型',
                    'confidence_score': confidence
                }
        
        except NotImplementedError:
            return self._tag_aggressive_simplified(address_id)
        
        return None
    
    # ==================== 簡化版邏輯 ====================
    
    def _tag_balanced_simplified(self, address_id: int) -> Dict[str, Any]:
        """均衡型標籤（簡化版）"""
        cfg = self.config['均衡型']
        trades = self.db.get_address_trades(address_id)
        
        if len(trades) < cfg['min_trades']:
            return None
        
        prices = [t['price'] for t in trades if t['price']]
        if not prices:
            return None
        
        price_in_range = sum(1 for p in prices if 0.3 <= p <= 0.7)
        price_ratio = price_in_range / len(prices)
        
        if price_ratio >= 0.5:
            return {
                'category': '風險偏好',
                'tag_name': '均衡型',
                'confidence_score': 0.6
            }
        
        return None
    
    def _tag_conservative_simplified(self, address_id: int) -> Dict[str, Any]:
        """保守型標籤（簡化版）"""
        cfg = self.config['保守型']
        trades = self.db.get_address_trades(address_id)
        
        if len(trades) < cfg['min_trades']:
            return None
        
        high_prob_trades = sum(1 for t in trades if t['price'] and t['price'] > 0.7)
        high_prob_ratio = high_prob_trades / len(trades)
        
        if high_prob_ratio >= 0.6:
            return {
                'category': '風險偏好',
                'tag_name': '保守型',
                'confidence_score': 0.6
            }
        
        return None
    
    def _tag_aggressive_simplified(self, address_id: int) -> Dict[str, Any]:
        """激進型標籤（簡化版）"""
        cfg = self.config['激進型']
        trades = self.db.get_address_trades(address_id)
        
        if len(trades) < cfg['min_trades']:
            return None
        
        low_prob_trades = sum(1 for t in trades if t['price'] and t['price'] < 0.3)
        low_prob_ratio = low_prob_trades / len(trades)
        
        if low_prob_ratio >= 0.5:
            return {
                'category': '風險偏好',
                'tag_name': '激進型',
                'confidence_score': 0.6
            }
        
        return None
