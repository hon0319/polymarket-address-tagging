"""
Polymarket 地址標籤自動標記服務 V2

完整版本：支持所有 50 種標籤（第一、二、三階段）

使用適配器模式，主管只需實作數據適配器即可使用。
"""

import json
import argparse
from typing import List, Dict, Any, Optional
from datetime import datetime

# 導入工具模組
from utils.database import DatabaseAdapter
from utils.confidence import ConfidenceCalculator
from utils.logger import Logger

# 導入數據適配器
from adapters import DataAdapter, MockDataAdapter

# 導入標籤器（第一階段）
from tags.trading_style import TradingStyleTagger
from tags.expertise import ExpertiseTagger
from tags.risk import RiskTagger
from tags.strategy import StrategyTagger

# 導入標籤器（第二階段）
from tags.trading_style_phase2 import TradingStylePhase2Tagger
from tags.risk_phase2 import RiskPhase2Tagger
from tags.strategy_phase2 import StrategyPhase2Tagger

# 導入標籤器（第三階段）
from tags.special_phase3 import SpecialPhase3Tagger
from tags.social_phase3 import SocialPhase3Tagger


class AddressTaggingService:
    """
    地址標籤自動標記服務
    
    支持所有 50 種標籤的自動標記。
    使用適配器模式，可以靈活配置數據源。
    """
    
    def __init__(self, config_path: str = 'config.json', data_adapter: Optional[DataAdapter] = None):
        """
        初始化服務
        
        Args:
            config_path: 配置文件路徑
            data_adapter: 數據適配器（如果為 None，使用 MockDataAdapter）
        """
        # 載入配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # 初始化日誌
        self.logger = Logger(self.config['logging'])
        self.logger.info("=== 地址標籤自動標記服務啟動 ===")
        
        # 初始化數據庫適配器
        self.db = DatabaseAdapter(self.config['database'])
        self.logger.info(f"數據庫連接：{self.config['database']['url']}")
        
        # 初始化數據適配器
        if data_adapter is None:
            self.logger.warning("未提供數據適配器，使用 MockDataAdapter（模擬數據）")
            self.data_adapter = MockDataAdapter()
        else:
            self.data_adapter = data_adapter
            self.logger.info(f"使用數據適配器：{type(data_adapter).__name__}")
        
        # 初始化信心分數計算器
        self.confidence_calc = ConfidenceCalculator(self.config['confidence'])
        
        # 初始化標籤器
        self._init_taggers()
        
        self.logger.info(f"已載入 {len(self.taggers)} 個標籤器")
    
    def _init_taggers(self):
        """初始化所有標籤器"""
        self.taggers = []
        
        # 第一階段標籤器（19 種）
        self.taggers.append(TradingStyleTagger(self.db, self.config, self.confidence_calc))
        self.taggers.append(ExpertiseTagger(self.db, self.config, self.confidence_calc))
        self.taggers.append(RiskTagger(self.db, self.config, self.confidence_calc))
        self.taggers.append(StrategyTagger(self.db, self.config, self.confidence_calc))
        
        # 第二階段標籤器（15 種）
        self.taggers.append(TradingStylePhase2Tagger(self.db, self.data_adapter, self.config, self.confidence_calc))
        self.taggers.append(RiskPhase2Tagger(self.db, self.data_adapter, self.config, self.confidence_calc))
        self.taggers.append(StrategyPhase2Tagger(self.db, self.data_adapter, self.config, self.confidence_calc))
        
        # 第三階段標籤器（16 種）
        self.taggers.append(SpecialPhase3Tagger(self.db, self.data_adapter, self.config, self.confidence_calc))
        self.taggers.append(SocialPhase3Tagger(self.db, self.data_adapter, self.config, self.confidence_calc))
    
    def tag_address(self, address_id: int) -> List[Dict[str, Any]]:
        """
        為單個地址打標籤
        
        Args:
            address_id: 地址 ID
            
        Returns:
            標籤列表
        """
        self.logger.info(f"開始為地址 {address_id} 打標籤...")
        
        # 獲取地址數據
        address_data = self.db.get_address(address_id)
        if not address_data:
            self.logger.warning(f"地址 {address_id} 不存在")
            return []
        
        # 應用所有標籤器
        all_tags = []
        for tagger in self.taggers:
            try:
                tags = tagger.tag(address_data)
                all_tags.extend(tags)
            except Exception as e:
                self.logger.error(f"標籤器 {type(tagger).__name__} 出錯：{str(e)}")
        
        self.logger.info(f"地址 {address_id} 獲得 {len(all_tags)} 個標籤")
        return all_tags
    
    def tag_all_addresses(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        為所有地址打標籤
        
        Args:
            limit: 限制處理的地址數量（用於測試）
            
        Returns:
            統計信息
        """
        self.logger.info("=== 開始批量打標籤 ===")
        
        # 獲取所有地址
        addresses = self.db.get_all_addresses(limit=limit)
        total_addresses = len(addresses)
        self.logger.info(f"共 {total_addresses} 個地址待處理")
        
        # 統計信息
        stats = {
            'total_addresses': total_addresses,
            'tagged_addresses': 0,
            'total_tags': 0,
            'tag_distribution': {},
            'start_time': datetime.now(),
            'end_time': None
        }
        
        # 逐個處理
        for i, address in enumerate(addresses, 1):
            address_id = address['id']
            
            # 打標籤
            tags = self.tag_address(address_id)
            
            if tags:
                stats['tagged_addresses'] += 1
                stats['total_tags'] += len(tags)
                
                # 保存到數據庫
                self.db.save_tags(address_id, tags)
                
                # 統計標籤分布
                for tag in tags:
                    tag_name = tag['tag_name']
                    stats['tag_distribution'][tag_name] = stats['tag_distribution'].get(tag_name, 0) + 1
            
            # 進度報告
            if i % 100 == 0:
                self.logger.info(f"進度：{i}/{total_addresses} ({i/total_addresses*100:.1f}%)")
        
        stats['end_time'] = datetime.now()
        duration = (stats['end_time'] - stats['start_time']).total_seconds()
        
        self.logger.info("=== 批量打標籤完成 ===")
        self.logger.info(f"處理時間：{duration:.2f} 秒")
        self.logger.info(f"已標記地址：{stats['tagged_addresses']}/{total_addresses}")
        self.logger.info(f"總標籤數：{stats['total_tags']}")
        
        return stats
    
    def update_tags(self) -> Dict[str, Any]:
        """
        更新最近活躍地址的標籤
        
        Returns:
            統計信息
        """
        self.logger.info("=== 開始更新標籤 ===")
        
        # 獲取最近活躍的地址（最近 7 天有交易）
        active_addresses = self.db.get_recently_active_addresses(days=7)
        self.logger.info(f"共 {len(active_addresses)} 個活躍地址需要更新")
        
        # 刪除舊標籤並重新打標籤
        stats = {
            'updated_addresses': 0,
            'total_tags': 0,
            'start_time': datetime.now(),
            'end_time': None
        }
        
        for address in active_addresses:
            address_id = address['id']
            
            # 刪除舊標籤
            self.db.delete_tags(address_id)
            
            # 重新打標籤
            tags = self.tag_address(address_id)
            
            if tags:
                self.db.save_tags(address_id, tags)
                stats['updated_addresses'] += 1
                stats['total_tags'] += len(tags)
        
        stats['end_time'] = datetime.now()
        duration = (stats['end_time'] - stats['start_time']).total_seconds()
        
        self.logger.info("=== 更新標籤完成 ===")
        self.logger.info(f"處理時間：{duration:.2f} 秒")
        self.logger.info(f"已更新地址：{stats['updated_addresses']}")
        self.logger.info(f"總標籤數：{stats['total_tags']}")
        
        return stats
    
    def generate_report(self) -> Dict[str, Any]:
        """
        生成標籤統計報告
        
        Returns:
            報告數據
        """
        self.logger.info("=== 生成統計報告 ===")
        
        report = self.db.get_tag_statistics()
        
        self.logger.info(f"總地址數：{report['total_addresses']}")
        self.logger.info(f"已標記地址：{report['tagged_addresses']}")
        self.logger.info(f"標記率：{report['coverage_rate']*100:.1f}%")
        self.logger.info(f"總標籤數：{report['total_tags']}")
        self.logger.info(f"平均每地址標籤數：{report['avg_tags_per_address']:.2f}")
        
        self.logger.info("\n標籤分布 TOP 10：")
        for tag_name, count in list(report['tag_distribution'].items())[:10]:
            self.logger.info(f"  {tag_name}: {count}")
        
        return report
    
    def export_json(self, output_path: str):
        """導出標籤為 JSON 格式"""
        self.logger.info(f"導出標籤到 {output_path}...")
        tags = self.db.export_all_tags()
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(tags, f, indent=2, ensure_ascii=False, default=str)
        self.logger.info(f"✅ 已導出 {len(tags)} 條標籤記錄")
    
    def export_csv(self, output_path: str):
        """導出標籤為 CSV 格式"""
        import csv
        self.logger.info(f"導出標籤到 {output_path}...")
        tags = self.db.export_all_tags()
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            if tags:
                writer = csv.DictWriter(f, fieldnames=tags[0].keys())
                writer.writeheader()
                writer.writerows(tags)
        
        self.logger.info(f"✅ 已導出 {len(tags)} 條標籤記錄")


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='Polymarket 地址標籤自動標記服務')
    
    # 基本參數
    parser.add_argument('--config', default='config.json', help='配置文件路徑')
    
    # 操作模式
    parser.add_argument('--init', action='store_true', help='初始化：為所有地址打標籤')
    parser.add_argument('--update', action='store_true', help='更新：為最近活躍地址更新標籤')
    parser.add_argument('--address', type=int, help='為指定地址打標籤')
    parser.add_argument('--report', action='store_true', help='生成統計報告')
    
    # 導出選項
    parser.add_argument('--export-json', help='導出標籤為 JSON 文件')
    parser.add_argument('--export-csv', help='導出標籤為 CSV 文件')
    
    # 測試選項
    parser.add_argument('--limit', type=int, help='限制處理的地址數量（用於測試）')
    parser.add_argument('--use-mock', action='store_true', help='使用模擬數據適配器（用於測試）')
    
    args = parser.parse_args()
    
    # 初始化服務
    data_adapter = MockDataAdapter() if args.use_mock else None
    service = AddressTaggingService(config_path=args.config, data_adapter=data_adapter)
    
    # 執行操作
    if args.init:
        stats = service.tag_all_addresses(limit=args.limit)
        print(f"\n✅ 初始化完成")
        print(f"   已標記地址：{stats['tagged_addresses']}/{stats['total_addresses']}")
        print(f"   總標籤數：{stats['total_tags']}")
    
    elif args.update:
        stats = service.update_tags()
        print(f"\n✅ 更新完成")
        print(f"   已更新地址：{stats['updated_addresses']}")
        print(f"   總標籤數：{stats['total_tags']}")
    
    elif args.address:
        tags = service.tag_address(args.address)
        print(f"\n地址 {args.address} 的標籤：")
        for tag in tags:
            print(f"  [{tag['category']}] {tag['tag_name']} (信心: {tag['confidence_score']:.2f})")
    
    elif args.report:
        report = service.generate_report()
        print(f"\n📊 標籤統計報告")
        print(f"   總地址數：{report['total_addresses']}")
        print(f"   已標記地址：{report['tagged_addresses']}")
        print(f"   標記率：{report['coverage_rate']*100:.1f}%")
        print(f"   總標籤數：{report['total_tags']}")
        print(f"   平均每地址標籤數：{report['avg_tags_per_address']:.2f}")
    
    elif args.export_json:
        service.export_json(args.export_json)
        print(f"\n✅ 已導出到 {args.export_json}")
    
    elif args.export_csv:
        service.export_csv(args.export_csv)
        print(f"\n✅ 已導出到 {args.export_csv}")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
