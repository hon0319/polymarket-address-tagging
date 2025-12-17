"""
交易風格標籤器

包含以下標籤：
- 高勝率
- 大交易量
- 高頻交易
- 穩定盈利
- 小額多單
"""

from typing import List, Dict, Any


class TradingStyleTagger:
    """交易風格標籤器"""
    
    def __init__(self, db, config: Dict[str, Any], confidence_calc):
        """
        初始化標籤器
        
        Args:
            db: 數據庫適配器
            config: 配置字典
            confidence_calc: 信心分數計算器
        """
        self.db = db
        self.config = config['tags']['交易風格']
        self.confidence_calc = confidence_calc
    
    def tag(self, address_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        為地址打上交易風格標籤
        
        Args:
            address_data: 地址數據
            
        Returns:
            標籤列表
        """
        tags = []
        address_id = address_data['id']
        
        # 高勝率
        if self.config['高勝率']['enabled']:
            tag = self._tag_high_win_rate(address_data)
            if tag:
                tags.append(tag)
        
        # 大交易量
        if self.config['大交易量']['enabled']:
            tag = self._tag_large_volume(address_data)
            if tag:
                tags.append(tag)
        
        # 高頻交易
        if self.config['高頻交易']['enabled']:
            tag = self._tag_high_frequency(address_id)
            if tag:
                tags.append(tag)
        
        # 穩定盈利
        if self.config['穩定盈利']['enabled']:
            tag = self._tag_stable_profit(address_id)
            if tag:
                tags.append(tag)
        
        # 小額多單
        if self.config['小額多單']['enabled']:
            tag = self._tag_small_frequent(address_data)
            if tag:
                tags.append(tag)
        
        return tags
    
    def _tag_high_win_rate(self, address_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        高勝率標籤
        
        條件：
        - 勝率 >= 閾值
        - 交易次數 >= 最小值
        """
        cfg = self.config['高勝率']
        win_rate = address_data.get('win_rate', 0)
        total_trades = address_data.get('total_trades', 0)
        
        if win_rate >= cfg['win_rate_threshold'] and total_trades >= cfg['min_trades']:
            # 計算信心分數：勝率越高，信心越高
            confidence = self.confidence_calc.calculate_ratio_confidence(
                win_rate,
                cfg['win_rate_threshold']
            )
            
            return {
                'category': '交易風格',
                'tag_name': '高勝率',
                'confidence_score': confidence
            }
        
        return None
    
    def _tag_large_volume(self, address_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        大交易量標籤
        
        條件：
        - 平均交易金額 >= 閾值
        - 或有 N 筆以上的大額交易
        """
        cfg = self.config['大交易量']
        avg_trade_size = address_data.get('avg_trade_size', 0)
        
        if avg_trade_size >= cfg['avg_trade_size_threshold']:
            # 計算信心分數：平均金額越大，信心越高
            confidence = self.confidence_calc.calculate(
                avg_trade_size,
                cfg['avg_trade_size_threshold'],
                cfg['avg_trade_size_threshold'] * 5  # 5 倍閾值為滿分
            )
            
            return {
                'category': '交易風格',
                'tag_name': '大交易量',
                'confidence_score': confidence
            }
        
        return None
    
    def _tag_high_frequency(self, address_id: int) -> Dict[str, Any]:
        """
        高頻交易標籤
        
        條件：
        - 最近 N 天的日均交易次數 >= 閾值
        """
        cfg = self.config['高頻交易']
        recent_trades = self.db.get_recent_trades_count(
            address_id,
            cfg['lookback_days']
        )
        
        trades_per_day = recent_trades / cfg['lookback_days']
        
        if trades_per_day >= cfg['trades_per_day_threshold']:
            # 計算信心分數：日均交易次數越多，信心越高
            confidence = self.confidence_calc.calculate(
                trades_per_day,
                cfg['trades_per_day_threshold'],
                cfg['trades_per_day_threshold'] * 3  # 3 倍閾值為滿分
            )
            
            return {
                'category': '交易風格',
                'tag_name': '高頻交易',
                'confidence_score': confidence
            }
        
        return None
    
    def _tag_stable_profit(self, address_id: int) -> Dict[str, Any]:
        """
        穩定盈利標籤
        
        條件：
        - 至少 N 個月有盈利
        - 總共至少 M 個月有交易
        """
        cfg = self.config['穩定盈利']
        monthly_pnl = self.db.get_monthly_pnl(address_id)
        
        if not monthly_pnl:
            return None
        
        total_months = len(monthly_pnl)
        profitable_months = sum(1 for m in monthly_pnl if m['monthly_pnl'] > 0)
        
        if (profitable_months >= cfg['min_profitable_months'] and
            total_months >= cfg['min_total_months']):
            # 計算信心分數：盈利月份比例越高，信心越高
            profit_ratio = profitable_months / total_months
            confidence = self.confidence_calc.calculate_ratio_confidence(
                profit_ratio,
                cfg['min_profitable_months'] / cfg['min_total_months']
            )
            
            return {
                'category': '交易風格',
                'tag_name': '穩定盈利',
                'confidence_score': confidence
            }
        
        return None
    
    def _tag_small_frequent(self, address_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        小額多單標籤
        
        條件：
        - 平均交易金額 < 閾值
        - 交易次數 >= 最小值
        """
        cfg = self.config['小額多單']
        avg_trade_size = address_data.get('avg_trade_size', 0)
        total_trades = address_data.get('total_trades', 0)
        
        if (avg_trade_size < cfg['max_avg_trade_size'] and
            total_trades >= cfg['min_trades']):
            # 計算信心分數：交易次數越多，信心越高
            confidence = self.confidence_calc.calculate_count_confidence(
                total_trades,
                cfg['min_trades']
            )
            
            return {
                'category': '交易風格',
                'tag_name': '小額多單',
                'confidence_score': confidence
            }
        
        return None
