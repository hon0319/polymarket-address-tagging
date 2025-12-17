"""標籤邏輯模組"""

from .trading_style import TradingStyleTagger
from .expertise import ExpertiseTagger
from .risk import RiskTagger
from .strategy import StrategyTagger

__all__ = ['TradingStyleTagger', 'ExpertiseTagger', 'RiskTagger', 'StrategyTagger']
