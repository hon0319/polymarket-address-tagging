"""
策略類型標籤器

包含以下標籤（第一階段）：
- 掃尾盤
- 早期進場
"""

from typing import List, Dict, Any


class StrategyTagger:
    """策略類型標籤器"""
    
    def __init__(self, db, config: Dict[str, Any], confidence_calc):
        """
        初始化標籤器
        
        Args:
            db: 數據庫適配器
            config: 配置字典
            confidence_calc: 信心分數計算器
        """
        self.db = db
        self.config = config['tags']['策略類型']
        self.confidence_calc = confidence_calc
    
    def tag(self, address_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        為地址打上策略類型標籤
        
        Args:
            address_data: 地址數據
            
        Returns:
            標籤列表
        """
        tags = []
        address_id = address_data['id']
        total_trades = address_data.get('total_trades', 0)
        
        if total_trades == 0:
            return tags
        
        # 掃尾盤
        if self.config['掃尾盤']['enabled']:
            tag = self._tag_late_entry(address_id, total_trades)
            if tag:
                tags.append(tag)
        
        # 早期進場
        if self.config['早期進場']['enabled']:
            tag = self._tag_early_entry(address_id, total_trades)
            if tag:
                tags.append(tag)
        
        return tags
    
    def _tag_late_entry(self, address_id: int, total_trades: int) -> Dict[str, Any]:
        """
        掃尾盤標籤
        
        條件：
        - 在市場結算前 N 天內進場的交易佔比 >= 閾值
        - 交易次數 >= 最小值
        """
        cfg = self.config['掃尾盤']
        late_trades = self.db.get_late_entry_trades(
            address_id,
            cfg['days_before_close']
        )
        
        late_ratio = late_trades / total_trades if total_trades > 0 else 0
        
        if (late_ratio >= cfg['ratio_threshold'] and
            late_trades >= cfg['min_trades']):
            # 計算信心分數：掃尾盤佔比越高，信心越高
            confidence = self.confidence_calc.calculate_ratio_confidence(
                late_ratio,
                cfg['ratio_threshold']
            )
            
            return {
                'category': '策略類型',
                'tag_name': '掃尾盤',
                'confidence_score': confidence
            }
        
        return None
    
    def _tag_early_entry(self, address_id: int, total_trades: int) -> Dict[str, Any]:
        """
        早期進場標籤
        
        條件：
        - 在市場創建後 N 小時內進場的交易佔比 >= 閾值
        - 交易次數 >= 最小值
        """
        cfg = self.config['早期進場']
        early_trades = self.db.get_early_entry_trades(
            address_id,
            cfg['hours_after_creation']
        )
        
        early_ratio = early_trades / total_trades if total_trades > 0 else 0
        
        if (early_ratio >= cfg['ratio_threshold'] and
            early_trades >= cfg['min_trades']):
            # 計算信心分數：早期進場佔比越高，信心越高
            confidence = self.confidence_calc.calculate_ratio_confidence(
                early_ratio,
                cfg['ratio_threshold']
            )
            
            return {
                'category': '策略類型',
                'tag_name': '早期進場',
                'confidence_score': confidence
            }
        
        return None
