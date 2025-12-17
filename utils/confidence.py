"""
信心分數計算器模組

計算標籤的信心分數（0-1），用於表示標籤的可信度
"""

import math
from typing import Dict, Any


class ConfidenceCalculator:
    """信心分數計算器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化信心分數計算器
        
        Args:
            config: 配置字典
        """
        self.method = config.get('method', 'linear')
        self.min_confidence = config.get('min_confidence', 0.0)
        self.max_confidence = config.get('max_confidence', 1.0)
    
    def calculate(self, actual_value: float, threshold: float, max_value: float = 1.0) -> float:
        """
        計算信心分數
        
        Args:
            actual_value: 實際值
            threshold: 閾值
            max_value: 最大值
            
        Returns:
            信心分數 (0-1)
            
        Examples:
            >>> calc = ConfidenceCalculator({'method': 'linear'})
            >>> calc.calculate(0.55, 0.55, 1.0)  # 剛好達到閾值
            0.0
            >>> calc.calculate(0.70, 0.55, 1.0)  # 超過閾值
            0.33
            >>> calc.calculate(0.85, 0.55, 1.0)  # 遠超閾值
            0.67
        """
        # 如果未達到閾值，返回 0
        if actual_value < threshold:
            return self.min_confidence
        
        # 根據方法計算信心分數
        if self.method == 'linear':
            score = self._linear(actual_value, threshold, max_value)
        elif self.method == 'exponential':
            score = self._exponential(actual_value, threshold, max_value)
        elif self.method == 'sigmoid':
            score = self._sigmoid(actual_value, threshold, max_value)
        else:
            score = 1.0  # 默認滿分
        
        # 限制在範圍內
        return max(self.min_confidence, min(score, self.max_confidence))
    
    def _linear(self, actual_value: float, threshold: float, max_value: float) -> float:
        """
        線性計算
        
        信心分數與超過閾值的程度成線性關係
        """
        if max_value == threshold:
            return 1.0
        
        normalized = (actual_value - threshold) / (max_value - threshold)
        return min(normalized, 1.0)
    
    def _exponential(self, actual_value: float, threshold: float, max_value: float) -> float:
        """
        指數計算
        
        信心分數與超過閾值的程度成指數關係，增長較快
        """
        if max_value == threshold:
            return 1.0
        
        normalized = (actual_value - threshold) / (max_value - threshold)
        # 使用 x^2 作為指數函數
        return min(normalized ** 2, 1.0)
    
    def _sigmoid(self, actual_value: float, threshold: float, max_value: float) -> float:
        """
        Sigmoid 計算
        
        信心分數使用 sigmoid 函數，中間增長快，兩端增長慢
        """
        if max_value == threshold:
            return 1.0
        
        normalized = (actual_value - threshold) / (max_value - threshold)
        # 使用 sigmoid 函數: 1 / (1 + e^(-k*x))
        # k=6 使得在 x=0.5 時 y≈0.95
        k = 6
        x = normalized * 2 - 1  # 映射到 [-1, 1]
        return 1 / (1 + math.exp(-k * x))
    
    def calculate_ratio_confidence(self, ratio: float, threshold: float) -> float:
        """
        計算比例型指標的信心分數
        
        Args:
            ratio: 實際比例 (0-1)
            threshold: 閾值比例 (0-1)
            
        Returns:
            信心分數 (0-1)
        """
        return self.calculate(ratio, threshold, 1.0)
    
    def calculate_count_confidence(self, count: int, min_count: int, ideal_count: int = None) -> float:
        """
        計算計數型指標的信心分數
        
        Args:
            count: 實際計數
            min_count: 最小計數
            ideal_count: 理想計數（可選，默認為 min_count * 3）
            
        Returns:
            信心分數 (0-1)
        """
        if ideal_count is None:
            ideal_count = min_count * 3
        
        return self.calculate(count, min_count, ideal_count)
