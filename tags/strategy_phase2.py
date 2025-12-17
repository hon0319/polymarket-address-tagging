"""
策略類型標籤器（第二階段）

新增標籤：
- 逆勢操作
- 順勢操作
- 價值捕手
- 套利者
- 事件驅動
- 對沖交易者
- 做市商
- 趨勢追蹤者
- 均值回歸者
- 狙擊手

需要數據：
- 價格歷史、持倉變化（通過 DataAdapter 獲取）
"""

from typing import List, Dict, Any
import statistics


class StrategyPhase2Tagger:
    """策略類型標籤器（第二階段）"""
    
    def __init__(self, db, data_adapter, config: Dict[str, Any], confidence_calc):
        self.db = db
        self.data_adapter = data_adapter
        self.config = config['tags']['策略類型']
        self.confidence_calc = confidence_calc
    
    def tag(self, address_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """為地址打上策略類型標籤（第二階段）"""
        tags = []
        address_id = address_data['id']
        
        # 逆勢操作
        if self.config['逆勢操作']['enabled']:
            tag = self._tag_contrarian(address_id)
            if tag:
                tags.append(tag)
        
        # 順勢操作
        if self.config['順勢操作']['enabled']:
            tag = self._tag_momentum(address_id)
            if tag:
                tags.append(tag)
        
        # 價值捕手
        if self.config['價值捕手']['enabled']:
            tag = self._tag_value_hunter(address_id)
            if tag:
                tags.append(tag)
        
        # 套利者
        if self.config['套利者']['enabled']:
            tag = self._tag_arbitrageur(address_id)
            if tag:
                tags.append(tag)
        
        # 事件驅動
        if self.config['事件驅動']['enabled']:
            tag = self._tag_event_driven(address_id)
            if tag:
                tags.append(tag)
        
        # 對沖交易者
        if self.config['對沖交易者']['enabled']:
            tag = self._tag_hedger(address_id)
            if tag:
                tags.append(tag)
        
        # 做市商
        if self.config['做市商']['enabled']:
            tag = self._tag_market_maker(address_id)
            if tag:
                tags.append(tag)
        
        # 趨勢追蹤者
        if self.config['趨勢追蹤者']['enabled']:
            tag = self._tag_trend_follower(address_id)
            if tag:
                tags.append(tag)
        
        # 均值回歸者
        if self.config['均值回歸者']['enabled']:
            tag = self._tag_mean_reversion(address_id)
            if tag:
                tags.append(tag)
        
        # 狙擊手
        if self.config['狙擊手']['enabled']:
            tag = self._tag_sniper(address_id)
            if tag:
                tags.append(tag)
        
        return tags
    
    def _tag_contrarian(self, address_id: int) -> Dict[str, Any]:
        """
        逆勢操作標籤
        
        條件：
        - 在價格上漲時賣出，價格下跌時買入
        - 逆勢交易佔比 >= 閾值
        """
        cfg = self.config['逆勢操作']
        
        try:
            trades = self.db.get_address_trades(address_id)
            if len(trades) < cfg['min_trades']:
                return None
            
            contrarian_count = 0
            for trade in trades:
                # 獲取該市場的價格歷史
                price_history = self.data_adapter.get_price_history(trade['market_id'])
                if not price_history:
                    continue
                
                # 判斷價格趨勢
                recent_prices = [p['price'] for p in price_history[-5:]]
                if len(recent_prices) < 2:
                    continue
                
                price_trend = recent_prices[-1] - recent_prices[0]
                
                # 逆勢：價格上漲時賣出，價格下跌時買入
                if (price_trend > 0 and trade['side'] == 'sell') or \
                   (price_trend < 0 and trade['side'] == 'buy'):
                    contrarian_count += 1
            
            contrarian_ratio = contrarian_count / len(trades)
            
            if contrarian_ratio >= cfg['contrarian_ratio_threshold']:
                confidence = self.confidence_calc.calculate(
                    contrarian_ratio,
                    cfg['contrarian_ratio_threshold'],
                    1.0
                )
                
                return {
                    'category': '策略類型',
                    'tag_name': '逆勢操作',
                    'confidence_score': confidence
                }
        
        except (NotImplementedError, Exception):
            return self._tag_contrarian_simplified(address_id)
        
        return None
    
    def _tag_momentum(self, address_id: int) -> Dict[str, Any]:
        """
        順勢操作標籤
        
        條件：
        - 在價格上漲時買入，價格下跌時賣出
        - 順勢交易佔比 >= 閾值
        """
        cfg = self.config['順勢操作']
        
        try:
            trades = self.db.get_address_trades(address_id)
            if len(trades) < cfg['min_trades']:
                return None
            
            momentum_count = 0
            for trade in trades:
                price_history = self.data_adapter.get_price_history(trade['market_id'])
                if not price_history:
                    continue
                
                recent_prices = [p['price'] for p in price_history[-5:]]
                if len(recent_prices) < 2:
                    continue
                
                price_trend = recent_prices[-1] - recent_prices[0]
                
                # 順勢：價格上漲時買入，價格下跌時賣出
                if (price_trend > 0 and trade['side'] == 'buy') or \
                   (price_trend < 0 and trade['side'] == 'sell'):
                    momentum_count += 1
            
            momentum_ratio = momentum_count / len(trades)
            
            if momentum_ratio >= cfg['momentum_ratio_threshold']:
                confidence = self.confidence_calc.calculate(
                    momentum_ratio,
                    cfg['momentum_ratio_threshold'],
                    1.0
                )
                
                return {
                    'category': '策略類型',
                    'tag_name': '順勢操作',
                    'confidence_score': confidence
                }
        
        except (NotImplementedError, Exception):
            return self._tag_momentum_simplified(address_id)
        
        return None
    
    def _tag_value_hunter(self, address_id: int) -> Dict[str, Any]:
        """
        價值捕手標籤
        
        條件：
        - 主要在價格 0.2-0.4 或 0.6-0.8 之間交易（被低估或高估）
        - 持倉直到價格回歸合理值
        """
        cfg = self.config['價值捕手']
        
        trades = self.db.get_address_trades(address_id)
        if len(trades) < cfg['min_trades']:
            return None
        
        value_trades = sum(1 for t in trades if t['price'] and (
            (cfg['undervalued_min'] <= t['price'] <= cfg['undervalued_max']) or
            (cfg['overvalued_min'] <= t['price'] <= cfg['overvalued_max'])
        ))
        
        value_ratio = value_trades / len(trades)
        
        if value_ratio >= cfg['value_ratio_threshold']:
            confidence = self.confidence_calc.calculate(
                value_ratio,
                cfg['value_ratio_threshold'],
                1.0
            )
            
            return {
                'category': '策略類型',
                'tag_name': '價值捕手',
                'confidence_score': confidence
            }
        
        return None
    
    def _tag_arbitrageur(self, address_id: int) -> Dict[str, Any]:
        """
        套利者標籤
        
        條件：
        - 同時在相關市場進行相反操作
        - 持倉時間短
        - 利潤穩定但較小
        """
        cfg = self.config['套利者']
        
        try:
            position_changes = self.data_adapter.get_position_changes(address_id)
            if len(position_changes) < cfg['min_trades']:
                return None
            
            # 檢測套利模式：在短時間內進行相反操作
            arbitrage_count = 0
            for i in range(len(position_changes) - 1):
                current = position_changes[i]
                next_trade = position_changes[i + 1]
                
                # 時間間隔 < 1 小時
                time_diff = (next_trade['timestamp'] - current['timestamp']).total_seconds()
                if time_diff > 3600:
                    continue
                
                # 相反操作
                if current['side'] != next_trade['side']:
                    arbitrage_count += 1
            
            arbitrage_ratio = arbitrage_count / len(position_changes)
            
            if arbitrage_ratio >= cfg['arbitrage_ratio_threshold']:
                confidence = self.confidence_calc.calculate(
                    arbitrage_ratio,
                    cfg['arbitrage_ratio_threshold'],
                    1.0
                )
                
                return {
                    'category': '策略類型',
                    'tag_name': '套利者',
                    'confidence_score': confidence
                }
        
        except (NotImplementedError, Exception):
            return None
        
        return None
    
    def _tag_event_driven(self, address_id: int) -> Dict[str, Any]:
        """
        事件驅動標籤
        
        條件：
        - 交易時間與新聞發布時間高度相關
        - 交易量在事件前後激增
        """
        cfg = self.config['事件驅動']
        
        try:
            trades = self.db.get_address_trades(address_id)
            if len(trades) < cfg['min_trades']:
                return None
            
            event_driven_count = 0
            for trade in trades:
                # 獲取該市場的新聞
                news = self.data_adapter.get_market_news(trade['market_id'], days=1)
                if not news:
                    continue
                
                # 檢查交易是否在新聞發布後短時間內
                for article in news:
                    time_diff = abs((trade['timestamp'] - article['published_at']).total_seconds())
                    if time_diff < 3600:  # 1 小時內
                        event_driven_count += 1
                        break
            
            event_ratio = event_driven_count / len(trades)
            
            if event_ratio >= cfg['event_ratio_threshold']:
                confidence = self.confidence_calc.calculate(
                    event_ratio,
                    cfg['event_ratio_threshold'],
                    1.0
                )
                
                return {
                    'category': '策略類型',
                    'tag_name': '事件驅動',
                    'confidence_score': confidence
                }
        
        except (NotImplementedError, Exception):
            return self._tag_event_driven_simplified(address_id)
        
        return None
    
    def _tag_hedger(self, address_id: int) -> Dict[str, Any]:
        """
        對沖交易者標籤
        
        條件：
        - 同時持有相反倉位
        - 在同一市場的 Yes 和 No 都有倉位
        """
        cfg = self.config['對沖交易者']
        
        try:
            position_changes = self.data_adapter.get_position_changes(address_id)
            if len(position_changes) < cfg['min_trades']:
                return None
            
            # 按市場分組
            market_positions = {}
            for change in position_changes:
                market_id = change['market_id']
                if market_id not in market_positions:
                    market_positions[market_id] = {'Yes': 0, 'No': 0}
                
                if change['side'] == 'buy':
                    market_positions[market_id][change['outcome']] += change['amount']
                else:
                    market_positions[market_id][change['outcome']] -= change['amount']
            
            # 檢測對沖：同時持有 Yes 和 No
            hedged_markets = sum(1 for positions in market_positions.values()
                                if positions['Yes'] > 0 and positions['No'] > 0)
            
            hedge_ratio = hedged_markets / len(market_positions)
            
            if hedge_ratio >= cfg['hedge_ratio_threshold']:
                confidence = self.confidence_calc.calculate(
                    hedge_ratio,
                    cfg['hedge_ratio_threshold'],
                    1.0
                )
                
                return {
                    'category': '策略類型',
                    'tag_name': '對沖交易者',
                    'confidence_score': confidence
                }
        
        except (NotImplementedError, Exception):
            return None
        
        return None
    
    def _tag_market_maker(self, address_id: int) -> Dict[str, Any]:
        """
        做市商標籤
        
        條件：
        - 頻繁買賣，提供流動性
        - 買賣次數接近 1:1
        - 交易量大
        """
        cfg = self.config['做市商']
        
        trades = self.db.get_address_trades(address_id)
        if len(trades) < cfg['min_trades']:
            return None
        
        buy_count = sum(1 for t in trades if t['side'] == 'buy')
        sell_count = sum(1 for t in trades if t['side'] == 'sell')
        
        if buy_count == 0 or sell_count == 0:
            return None
        
        buy_sell_ratio = min(buy_count, sell_count) / max(buy_count, sell_count)
        total_volume = sum(t['amount'] for t in trades if t['amount'])
        
        if (buy_sell_ratio >= cfg['buy_sell_ratio_threshold'] and
            total_volume >= cfg['min_volume']):
            
            confidence = buy_sell_ratio * 0.7 + 0.3
            
            return {
                'category': '策略類型',
                'tag_name': '做市商',
                'confidence_score': confidence
            }
        
        return None
    
    def _tag_trend_follower(self, address_id: int) -> Dict[str, Any]:
        """
        趨勢追蹤者標籤
        
        條件：
        - 在明確趨勢中交易
        - 持倉時間較長
        - 順勢操作佔比高
        """
        # 類似順勢操作，但更強調長期趨勢
        return self._tag_momentum(address_id)
    
    def _tag_mean_reversion(self, address_id: int) -> Dict[str, Any]:
        """
        均值回歸者標籤
        
        條件：
        - 在價格偏離均值時交易
        - 等待價格回歸
        """
        # 類似價值捕手
        return self._tag_value_hunter(address_id)
    
    def _tag_sniper(self, address_id: int) -> Dict[str, Any]:
        """
        狙擊手標籤
        
        條件：
        - 在關鍵時刻大額交易
        - 交易次數少但金額大
        - 勝率高
        """
        cfg = self.config['狙擊手']
        
        trades = self.db.get_address_trades(address_id)
        address_data = self.db.get_address(address_id)
        
        if (len(trades) <= cfg['max_trades'] and
            address_data['avg_trade_size'] >= cfg['min_avg_trade_size'] and
            address_data['win_rate'] >= cfg['min_win_rate']):
            
            confidence = address_data['win_rate'] * 0.7 + 0.3
            
            return {
                'category': '策略類型',
                'tag_name': '狙擊手',
                'confidence_score': confidence
            }
        
        return None
    
    # ==================== 簡化版邏輯 ====================
    
    def _tag_contrarian_simplified(self, address_id: int) -> Dict[str, Any]:
        """逆勢操作標籤（簡化版）- 基於價格分布"""
        trades = self.db.get_address_trades(address_id)
        if len(trades) < 5:
            return None
        
        # 簡化邏輯：主要在極端價格交易
        extreme_trades = sum(1 for t in trades if t['price'] and (t['price'] < 0.2 or t['price'] > 0.8))
        extreme_ratio = extreme_trades / len(trades)
        
        if extreme_ratio >= 0.5:
            return {
                'category': '策略類型',
                'tag_name': '逆勢操作',
                'confidence_score': 0.5
            }
        
        return None
    
    def _tag_momentum_simplified(self, address_id: int) -> Dict[str, Any]:
        """順勢操作標籤（簡化版）- 基於交易頻率"""
        trades = self.db.get_address_trades(address_id)
        if len(trades) < 10:
            return None
        
        # 簡化邏輯：高頻交易者可能是順勢操作
        recent_trades = self.db.get_recent_trades_count(address_id, 7)
        if recent_trades >= 10:
            return {
                'category': '策略類型',
                'tag_name': '順勢操作',
                'confidence_score': 0.5
            }
        
        return None
    
    def _tag_event_driven_simplified(self, address_id: int) -> Dict[str, Any]:
        """事件驅動標籤（簡化版）- 基於交易時間集中度"""
        trades = self.db.get_address_trades(address_id)
        if len(trades) < 5:
            return None
        
        # 簡化邏輯：交易時間高度集中
        timestamps = [t['timestamp'] for t in trades]
        if len(timestamps) < 2:
            return None
        
        time_diffs = [(timestamps[i+1] - timestamps[i]).total_seconds() 
                     for i in range(len(timestamps)-1)]
        
        if time_diffs:
            avg_time_diff = statistics.mean(time_diffs)
            # 如果平均間隔 < 1 天，可能是事件驅動
            if avg_time_diff < 86400:
                return {
                    'category': '策略類型',
                    'tag_name': '事件驅動',
                    'confidence_score': 0.5
                }
        
        return None
