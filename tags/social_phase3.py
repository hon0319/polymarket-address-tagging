"""
社交影響力標籤器（第三階段）

新增標籤：
- KOL
- 社群領袖
- 跟單目標
- 隱形巨鯨

需要數據：
- 社交媒體 API（Twitter、Discord）
"""

from typing import List, Dict, Any


class SocialPhase3Tagger:
    """社交影響力標籤器（第三階段）"""
    
    def __init__(self, db, data_adapter, config: Dict[str, Any], confidence_calc):
        self.db = db
        self.data_adapter = data_adapter
        self.config = config['tags']['社交影響力']
        self.confidence_calc = confidence_calc
    
    def tag(self, address_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """為地址打上社交影響力標籤（第三階段）"""
        tags = []
        address_id = address_data['id']
        address = address_data.get('address', '')
        
        # KOL
        if self.config['KOL']['enabled']:
            tag = self._tag_kol(address)
            if tag:
                tags.append(tag)
        
        # 社群領袖
        if self.config['社群領袖']['enabled']:
            tag = self._tag_community_leader(address)
            if tag:
                tags.append(tag)
        
        # 跟單目標
        if self.config['跟單目標']['enabled']:
            tag = self._tag_copy_target(address_id, address_data)
            if tag:
                tags.append(tag)
        
        # 隱形巨鯨
        if self.config['隱形巨鯨']['enabled']:
            tag = self._tag_silent_whale(address, address_data)
            if tag:
                tags.append(tag)
        
        return tags
    
    def _tag_kol(self, address: str) -> Dict[str, Any]:
        """
        KOL 標籤
        
        條件：
        - Twitter 粉絲 > 50,000
        - Twitter 提及次數高
        - 已驗證帳號
        """
        cfg = self.config['KOL']
        
        try:
            social_data = self.data_adapter.get_address_social_activity(address)
            
            if (social_data['twitter_followers'] >= cfg['min_followers'] and
                social_data['twitter_mentions'] >= cfg['min_mentions'] and
                social_data['is_verified']):
                
                # 根據粉絲數和提及次數計算信心分數
                follower_score = min(1.0, social_data['twitter_followers'] / 100000)
                mention_score = min(1.0, social_data['twitter_mentions'] / 1000)
                confidence = (follower_score + mention_score) / 2
                
                return {
                    'category': '社交影響力',
                    'tag_name': 'KOL',
                    'confidence_score': confidence
                }
        
        except (NotImplementedError, Exception):
            return None
        
        return None
    
    def _tag_community_leader(self, address: str) -> Dict[str, Any]:
        """
        社群領袖標籤
        
        條件：
        - Discord 活躍度高
        - 社群互動多
        - 不一定有大量粉絲
        """
        cfg = self.config['社群領袖']
        
        try:
            social_data = self.data_adapter.get_address_social_activity(address)
            
            if (social_data['discord_messages'] >= cfg['min_discord_messages'] and
                social_data['twitter_mentions'] >= cfg['min_mentions']):
                
                # 根據社群活躍度計算信心分數
                discord_score = min(1.0, social_data['discord_messages'] / 500)
                mention_score = min(1.0, social_data['twitter_mentions'] / 100)
                confidence = (discord_score + mention_score) / 2
                
                return {
                    'category': '社交影響力',
                    'tag_name': '社群領袖',
                    'confidence_score': confidence
                }
        
        except (NotImplementedError, Exception):
            return None
        
        return None
    
    def _tag_copy_target(self, address_id: int, address_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        跟單目標標籤
        
        條件：
        - 勝率高（> 70%）
        - 交易量大
        - 有社交媒體存在感
        """
        cfg = self.config['跟單目標']
        
        if (address_data['win_rate'] >= cfg['min_win_rate'] and
            address_data['total_volume'] >= cfg['min_total_volume'] and
            address_data['total_trades'] >= cfg['min_trades']):
            
            # 檢查社交媒體
            address = address_data.get('address', '')
            try:
                social_data = self.data_adapter.get_address_social_activity(address)
                has_social_presence = (social_data['twitter_followers'] > 0 or
                                      social_data['discord_messages'] > 0)
            except:
                has_social_presence = False
            
            if has_social_presence or address_data['win_rate'] >= 0.75:
                # 根據勝率和交易量計算信心分數
                win_rate_score = address_data['win_rate']
                volume_score = min(1.0, address_data['total_volume'] / 1000000)
                confidence = (win_rate_score + volume_score) / 2
                
                return {
                    'category': '社交影響力',
                    'tag_name': '跟單目標',
                    'confidence_score': confidence
                }
        
        return None
    
    def _tag_silent_whale(self, address: str, address_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        隱形巨鯨標籤
        
        條件：
        - 交易量極大（> $1M）
        - 勝率穩定（> 65%）
        - 社交媒體無存在感
        """
        cfg = self.config['隱形巨鯨']
        
        if (address_data['total_volume'] >= cfg['min_total_volume'] and
            address_data['win_rate'] >= cfg['min_win_rate']):
            
            # 檢查社交媒體（應該沒有或很少）
            try:
                social_data = self.data_adapter.get_address_social_activity(address)
                is_silent = (social_data['twitter_followers'] < cfg['max_followers'] and
                           social_data['twitter_mentions'] < cfg['max_mentions'])
            except:
                is_silent = True  # 如果無法獲取社交數據，假設是隱形的
            
            if is_silent:
                # 根據交易量計算信心分數
                confidence = min(1.0, address_data['total_volume'] / 5000000)
                
                return {
                    'category': '社交影響力',
                    'tag_name': '隱形巨鯨',
                    'confidence_score': confidence
                }
        
        return None
