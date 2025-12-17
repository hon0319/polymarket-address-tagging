"""
風險偏好標籤器

包含以下標籤：
- 低風險
- 高風險
"""

from typing import List, Dict, Any


class RiskTagger:
    """風險偏好標籤器"""
    
    def __init__(self, db, config: Dict[str, Any], confidence_calc):
        """
        初始化標籤器
        
        Args:
            db: 數據庫適配器
            config: 配置字典
            confidence_calc: 信心分數計算器
        """
        self.db = db
        self.config = config['tags']['風險偏好']
        self.confidence_calc = confidence_calc
    
    def tag(self, address_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        為地址打上風險偏好標籤
        
        Args:
            address_data: 地址數據
            
        Returns:
            標籤列表
        """
        tags = []
        address_id = address_data['id']
        
        # 低風險
        if self.config['低風險']['enabled']:
            tag = self._tag_low_risk(address_id)
            if tag:
                tags.append(tag)
        
        # 高風險
        if self.config['高風險']['enabled']:
            tag = self._tag_high_risk(address_id)
            if tag:
                tags.append(tag)
        
        return tags
    
    def _tag_low_risk(self, address_id: int) -> Dict[str, Any]:
        """
        低風險標籤
        
        條件：
        - 交易價格在極端區間（<0.25 或 >0.75）的佔比 >= 閾值
        - 交易次數 >= 最小值
        """
        cfg = self.config['低風險']
        price_data = self.db.get_price_distribution(address_id)
        
        if not price_data or len(price_data) < cfg['min_trades']:
            return None
        
        # 計算極端價格交易的佔比
        extreme_count = sum(
            1 for p in price_data
            if p['price'] <= cfg['price_threshold_low'] or p['price'] >= cfg['price_threshold_high']
        )
        extreme_ratio = extreme_count / len(price_data)
        
        if extreme_ratio >= cfg['ratio_threshold']:
            # 計算信心分數：極端價格佔比越高，信心越高
            confidence = self.confidence_calc.calculate_ratio_confidence(
                extreme_ratio,
                cfg['ratio_threshold']
            )
            
            return {
                'category': '風險偏好',
                'tag_name': '低風險',
                'confidence_score': confidence
            }
        
        return None
    
    def _tag_high_risk(self, address_id: int) -> Dict[str, Any]:
        """
        高風險標籤
        
        條件：
        - 交易價格在中間區間（0.35-0.65）的佔比 >= 閾值
        - 交易次數 >= 最小值
        """
        cfg = self.config['高風險']
        price_data = self.db.get_price_distribution(address_id)
        
        if not price_data or len(price_data) < cfg['min_trades']:
            return None
        
        # 計算中間價格交易的佔比
        middle_count = sum(
            1 for p in price_data
            if cfg['price_range_low'] <= p['price'] <= cfg['price_range_high']
        )
        middle_ratio = middle_count / len(price_data)
        
        if middle_ratio >= cfg['ratio_threshold']:
            # 計算信心分數：中間價格佔比越高，信心越高
            confidence = self.confidence_calc.calculate_ratio_confidence(
                middle_ratio,
                cfg['ratio_threshold']
            )
            
            return {
                'category': '風險偏好',
                'tag_name': '高風險',
                'confidence_score': confidence
            }
        
        return None
