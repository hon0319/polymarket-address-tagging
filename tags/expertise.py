"""
專長類別標籤器

包含以下標籤：
- 政治專家
- 體育專家
- 加密專家
- 娛樂專家
- 經濟專家
- 選舉專家
- NFL專家
- NBA專家
- 足球專家
- 全能型
"""

from typing import List, Dict, Any


class ExpertiseTagger:
    """專長類別標籤器"""
    
    def __init__(self, db, config: Dict[str, Any], confidence_calc):
        """
        初始化標籤器
        
        Args:
            db: 數據庫適配器
            config: 配置字典
            confidence_calc: 信心分數計算器
        """
        self.db = db
        self.config = config['tags']['專長類別']
        self.confidence_calc = confidence_calc
    
    def tag(self, address_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        為地址打上專長類別標籤
        
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
        
        # 基礎類別專家標籤
        for tag_name in ['政治專家', '體育專家', '加密專家', '娛樂專家', '經濟專家']:
            if self.config[tag_name]['enabled']:
                tag = self._tag_category_expert(address_id, total_trades, tag_name)
                if tag:
                    tags.append(tag)
        
        # 關鍵詞類別專家標籤
        for tag_name in ['選舉專家', 'NFL專家', 'NBA專家', '足球專家']:
            if self.config[tag_name]['enabled']:
                tag = self._tag_keyword_expert(address_id, total_trades, tag_name)
                if tag:
                    tags.append(tag)
        
        # 全能型
        if self.config['全能型']['enabled']:
            tag = self._tag_all_rounder(address_id, total_trades)
            if tag:
                tags.append(tag)
        
        return tags
    
    def _tag_category_expert(self, address_id: int, total_trades: int, tag_name: str) -> Dict[str, Any]:
        """
        基礎類別專家標籤
        
        條件：
        - 該類別交易佔比 >= 閾值
        - 該類別交易次數 >= 最小值
        """
        cfg = self.config[tag_name]
        category = cfg['category']
        
        category_trades = self.db.get_category_trades(address_id, category)
        category_ratio = category_trades / total_trades if total_trades > 0 else 0
        
        if (category_ratio >= cfg['ratio_threshold'] and
            category_trades >= cfg['min_category_trades']):
            # 計算信心分數：佔比越高，信心越高
            confidence = self.confidence_calc.calculate_ratio_confidence(
                category_ratio,
                cfg['ratio_threshold']
            )
            
            return {
                'category': '專長類別',
                'tag_name': tag_name,
                'confidence_score': confidence
            }
        
        return None
    
    def _tag_keyword_expert(self, address_id: int, total_trades: int, tag_name: str) -> Dict[str, Any]:
        """
        關鍵詞類別專家標籤
        
        條件：
        - 包含關鍵詞的市場交易佔比 >= 閾值
        - 包含關鍵詞的市場交易次數 >= 最小值
        """
        cfg = self.config[tag_name]
        keywords = cfg['keywords']
        parent_category = cfg.get('parent_category')
        
        keyword_trades = self.db.get_keyword_trades(address_id, keywords, parent_category)
        keyword_ratio = keyword_trades / total_trades if total_trades > 0 else 0
        
        if (keyword_ratio >= cfg['ratio_threshold'] and
            keyword_trades >= cfg['min_category_trades']):
            # 計算信心分數：佔比越高，信心越高
            confidence = self.confidence_calc.calculate_ratio_confidence(
                keyword_ratio,
                cfg['ratio_threshold']
            )
            
            return {
                'category': '專長類別',
                'tag_name': tag_name,
                'confidence_score': confidence
            }
        
        return None
    
    def _tag_all_rounder(self, address_id: int, total_trades: int) -> Dict[str, Any]:
        """
        全能型標籤
        
        條件：
        - 無明顯專長（最大類別佔比 < 閾值）
        - 至少涉及 N 個類別
        - 總交易次數 >= 最小值
        """
        cfg = self.config['全能型']
        
        if total_trades < cfg['min_trades']:
            return None
        
        # 獲取各類別的交易次數
        categories = ['Politics', 'Sports', 'Crypto', 'Entertainment', 'Economics']
        category_counts = {}
        
        for category in categories:
            count = self.db.get_category_trades(address_id, category)
            if count > 0:
                category_counts[category] = count
        
        if len(category_counts) < cfg['min_categories']:
            return None
        
        # 計算最大類別佔比
        max_category_ratio = max(category_counts.values()) / total_trades if total_trades > 0 else 0
        
        if max_category_ratio < cfg['max_category_ratio']:
            # 計算信心分數：類別越多且分布越均勻，信心越高
            confidence = self.confidence_calc.calculate_count_confidence(
                len(category_counts),
                cfg['min_categories'],
                len(categories)  # 理想情況是涉及所有類別
            )
            
            return {
                'category': '專長類別',
                'tag_name': '全能型',
                'confidence_score': confidence
            }
        
        return None
