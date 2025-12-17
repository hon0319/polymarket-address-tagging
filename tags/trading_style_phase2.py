"""
交易風格標籤器（第二階段）

新增標籤：
- 波段交易者
- 長期持有者
- 閃電交易者

需要數據：
- 持倉時長（通過 DataAdapter.get_holding_period 獲取）
"""

from typing import List, Dict, Any


class TradingStylePhase2Tagger:
    """交易風格標籤器（第二階段）"""
    
    def __init__(self, db, data_adapter, config: Dict[str, Any], confidence_calc):
        """
        初始化標籤器
        
        Args:
            db: 數據庫適配器
            data_adapter: 數據適配器（提供持倉數據）
            config: 配置字典
            confidence_calc: 信心分數計算器
        """
        self.db = db
        self.data_adapter = data_adapter
        self.config = config['tags']['交易風格']
        self.confidence_calc = confidence_calc
    
    def tag(self, address_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        為地址打上交易風格標籤（第二階段）
        
        Args:
            address_data: 地址數據
            
        Returns:
            標籤列表
        """
        tags = []
        address_id = address_data['id']
        
        # 波段交易者
        if self.config['波段交易者']['enabled']:
            tag = self._tag_swing_trader(address_id)
            if tag:
                tags.append(tag)
        
        # 長期持有者
        if self.config['長期持有者']['enabled']:
            tag = self._tag_long_term_holder(address_id)
            if tag:
                tags.append(tag)
        
        # 閃電交易者
        if self.config['閃電交易者']['enabled']:
            tag = self._tag_flash_trader(address_id)
            if tag:
                tags.append(tag)
        
        return tags
    
    def _tag_swing_trader(self, address_id: int) -> Dict[str, Any]:
        """
        波段交易者標籤
        
        條件：
        - 平均持倉時長：7-30 天
        - 交易次數 >= 最小值
        """
        cfg = self.config['波段交易者']
        
        try:
            # 獲取所有交易的持倉時長
            trades = self.data_adapter.get_trade_timestamps(address_id)
            if len(trades) < cfg['min_trades']:
                return None
            
            # 計算平均持倉時長
            holding_periods = []
            for trade in trades:
                if trade['exit_time']:
                    holding_seconds = (trade['exit_time'] - trade['entry_time']).total_seconds()
                    holding_periods.append(holding_seconds)
                elif trade['market_end_date']:
                    # 如果沒有退出時間，使用市場結算時間
                    holding_seconds = (trade['market_end_date'] - trade['entry_time']).total_seconds()
                    holding_periods.append(holding_seconds)
            
            if not holding_periods:
                return None
            
            avg_holding_seconds = sum(holding_periods) / len(holding_periods)
            avg_holding_days = avg_holding_seconds / 86400
            
            # 判斷是否為波段交易者（7-30 天）
            if (cfg['min_holding_days'] <= avg_holding_days <= cfg['max_holding_days']):
                # 計算信心分數：越接近中間值（18.5 天），信心越高
                mid_point = (cfg['min_holding_days'] + cfg['max_holding_days']) / 2
                distance_from_mid = abs(avg_holding_days - mid_point)
                max_distance = (cfg['max_holding_days'] - cfg['min_holding_days']) / 2
                confidence = 1.0 - (distance_from_mid / max_distance) * 0.5  # 0.5-1.0
                
                return {
                    'category': '交易風格',
                    'tag_name': '波段交易者',
                    'confidence_score': confidence
                }
        
        except NotImplementedError:
            # 如果主管未實作 data_adapter，使用簡化邏輯
            return self._tag_swing_trader_simplified(address_id)
        
        return None
    
    def _tag_long_term_holder(self, address_id: int) -> Dict[str, Any]:
        """
        長期持有者標籤
        
        條件：
        - 平均持倉時長 > 30 天
        - 交易次數 >= 最小值
        """
        cfg = self.config['長期持有者']
        
        try:
            trades = self.data_adapter.get_trade_timestamps(address_id)
            if len(trades) < cfg['min_trades']:
                return None
            
            holding_periods = []
            for trade in trades:
                if trade['exit_time']:
                    holding_seconds = (trade['exit_time'] - trade['entry_time']).total_seconds()
                    holding_periods.append(holding_seconds)
                elif trade['market_end_date']:
                    holding_seconds = (trade['market_end_date'] - trade['entry_time']).total_seconds()
                    holding_periods.append(holding_seconds)
            
            if not holding_periods:
                return None
            
            avg_holding_seconds = sum(holding_periods) / len(holding_periods)
            avg_holding_days = avg_holding_seconds / 86400
            
            if avg_holding_days >= cfg['min_holding_days']:
                # 計算信心分數：持倉時間越長，信心越高
                confidence = self.confidence_calc.calculate(
                    avg_holding_days,
                    cfg['min_holding_days'],
                    cfg['min_holding_days'] * 3  # 90 天為滿分
                )
                
                return {
                    'category': '交易風格',
                    'tag_name': '長期持有者',
                    'confidence_score': confidence
                }
        
        except NotImplementedError:
            return self._tag_long_term_holder_simplified(address_id)
        
        return None
    
    def _tag_flash_trader(self, address_id: int) -> Dict[str, Any]:
        """
        閃電交易者標籤
        
        條件：
        - 平均持倉時長 < 24 小時
        - 交易次數 >= 最小值
        """
        cfg = self.config['閃電交易者']
        
        try:
            trades = self.data_adapter.get_trade_timestamps(address_id)
            if len(trades) < cfg['min_trades']:
                return None
            
            holding_periods = []
            for trade in trades:
                if trade['exit_time']:
                    holding_seconds = (trade['exit_time'] - trade['entry_time']).total_seconds()
                    holding_periods.append(holding_seconds)
            
            if not holding_periods:
                return None
            
            avg_holding_seconds = sum(holding_periods) / len(holding_periods)
            avg_holding_hours = avg_holding_seconds / 3600
            
            if avg_holding_hours <= cfg['max_holding_hours']:
                # 計算信心分數：持倉時間越短，信心越高
                confidence = 1.0 - (avg_holding_hours / cfg['max_holding_hours']) * 0.5 + 0.5
                
                return {
                    'category': '交易風格',
                    'tag_name': '閃電交易者',
                    'confidence_score': confidence
                }
        
        except NotImplementedError:
            return self._tag_flash_trader_simplified(address_id)
        
        return None
    
    # ==================== 簡化版邏輯（不依賴外部數據）====================
    
    def _tag_swing_trader_simplified(self, address_id: int) -> Dict[str, Any]:
        """
        波段交易者標籤（簡化版）
        
        使用交易頻率推測：
        - 每週 1-3 筆交易 → 可能是波段交易者
        """
        cfg = self.config['波段交易者']
        recent_trades = self.db.get_recent_trades_count(address_id, 30)
        
        trades_per_week = recent_trades / 4.3  # 30 天 ≈ 4.3 週
        
        if 1 <= trades_per_week <= 3:
            confidence = 0.6  # 簡化版信心分數較低
            return {
                'category': '交易風格',
                'tag_name': '波段交易者',
                'confidence_score': confidence
            }
        
        return None
    
    def _tag_long_term_holder_simplified(self, address_id: int) -> Dict[str, Any]:
        """
        長期持有者標籤（簡化版）
        
        使用交易頻率推測：
        - 每月 < 2 筆交易 → 可能是長期持有者
        """
        cfg = self.config['長期持有者']
        recent_trades = self.db.get_recent_trades_count(address_id, 90)
        
        trades_per_month = recent_trades / 3
        
        if trades_per_month < 2:
            confidence = 0.6  # 簡化版信心分數較低
            return {
                'category': '交易風格',
                'tag_name': '長期持有者',
                'confidence_score': confidence
            }
        
        return None
    
    def _tag_flash_trader_simplified(self, address_id: int) -> Dict[str, Any]:
        """
        閃電交易者標籤（簡化版）
        
        使用交易頻率推測：
        - 每天 > 3 筆交易 → 可能是閃電交易者
        """
        cfg = self.config['閃電交易者']
        recent_trades = self.db.get_recent_trades_count(address_id, 7)
        
        trades_per_day = recent_trades / 7
        
        if trades_per_day > 3:
            confidence = 0.6  # 簡化版信心分數較低
            return {
                'category': '交易風格',
                'tag_name': '閃電交易者',
                'confidence_score': confidence
            }
        
        return None
