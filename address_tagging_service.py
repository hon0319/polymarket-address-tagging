#!/usr/bin/env python3
"""
Polymarket 地址標籤自動標記服務

這個服務會根據地址的交易行為自動打上標籤，包括：
- 交易風格（高勝率、大交易量等）
- 專長類別（政治專家、體育專家等）
- 風險偏好（低風險、高風險等）
- 策略類型（掃尾盤、早期進場等）

使用方式：
    python address_tagging_service.py --init              # 初始化標籤
    python address_tagging_service.py --update            # 更新標籤
    python address_tagging_service.py --address 0x123...  # 標記單個地址
    python address_tagging_service.py --report            # 生成報告
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional

from utils.database import DatabaseAdapter
from utils.confidence import ConfidenceCalculator
from utils.logger import setup_logger
from tags.trading_style import TradingStyleTagger
from tags.expertise import ExpertiseTagger
from tags.risk import RiskTagger
from tags.strategy import StrategyTagger


class AddressTaggingService:
    """地址標籤自動標記服務"""
    
    def __init__(self, config_path: str = 'config.json'):
        """
        初始化服務
        
        Args:
            config_path: 配置文件路徑
        """
        # 載入配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # 設置日誌
        self.logger = setup_logger(
            self.config.get('logging', {}).get('level', 'INFO'),
            self.config.get('logging', {}).get('file', 'address_tagging.log')
        )
        
        # 初始化數據庫適配器
        self.db = DatabaseAdapter(self.config)
        
        # 初始化信心分數計算器
        self.confidence_calc = ConfidenceCalculator(self.config.get('confidence', {}))
        
        # 初始化標籤器
        self.taggers = {
            '交易風格': TradingStyleTagger(self.db, self.config, self.confidence_calc),
            '專長類別': ExpertiseTagger(self.db, self.config, self.confidence_calc),
            '風險偏好': RiskTagger(self.db, self.config, self.confidence_calc),
            '策略類型': StrategyTagger(self.db, self.config, self.confidence_calc),
        }
        
        self.logger.info("地址標籤服務初始化完成")
    
    def init_database(self):
        """初始化數據庫表結構"""
        self.logger.info("開始初始化數據庫表結構...")
        
        # 創建 address_tags 表
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS address_tags (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            address_id BIGINT NOT NULL,
            category VARCHAR(50) NOT NULL COMMENT '標籤類別：交易風格、專長類別等',
            tag_name VARCHAR(50) NOT NULL COMMENT '標籤名稱',
            confidence_score DECIMAL(3,2) DEFAULT 1.00 COMMENT '信心分數 0-1',
            is_manual BOOLEAN DEFAULT FALSE COMMENT '是否手動標記',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uk_address_tag (address_id, tag_name),
            INDEX idx_address (address_id),
            INDEX idx_tag (tag_name),
            INDEX idx_category (category)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='地址標籤表';
        """
        
        try:
            self.db.execute(create_table_sql)
            self.logger.info("數據庫表結構初始化完成")
        except Exception as e:
            self.logger.error(f"數據庫表結構初始化失敗: {e}")
            raise
    
    def tag_address(self, address_id: int) -> List[Dict[str, Any]]:
        """
        為單個地址打標籤
        
        Args:
            address_id: 地址 ID
            
        Returns:
            標籤列表，每個標籤包含 category, tag_name, confidence_score
        """
        all_tags = []
        
        # 獲取地址數據
        address_data = self.db.get_address_data(address_id)
        if not address_data:
            self.logger.warning(f"地址 {address_id} 不存在")
            return []
        
        # 使用每個標籤器打標籤
        for category, tagger in self.taggers.items():
            try:
                tags = tagger.tag(address_data)
                all_tags.extend(tags)
            except Exception as e:
                self.logger.error(f"標籤器 {category} 處理地址 {address_id} 時出錯: {e}")
        
        return all_tags
    
    def save_tags(self, address_id: int, tags: List[Dict[str, Any]]):
        """
        保存標籤到數據庫
        
        Args:
            address_id: 地址 ID
            tags: 標籤列表
        """
        if not tags:
            return
        
        for tag in tags:
            try:
                sql = """
                INSERT INTO address_tags 
                (address_id, category, tag_name, confidence_score, is_manual)
                VALUES (%s, %s, %s, %s, FALSE)
                ON DUPLICATE KEY UPDATE
                    confidence_score = %s,
                    updated_at = NOW()
                """
                self.db.execute(sql, (
                    address_id,
                    tag['category'],
                    tag['tag_name'],
                    tag['confidence_score'],
                    tag['confidence_score']
                ))
            except Exception as e:
                self.logger.error(f"保存標籤失敗 - 地址: {address_id}, 標籤: {tag['tag_name']}, 錯誤: {e}")
    
    def tag_all_addresses(self, limit: Optional[int] = None):
        """
        為所有地址打標籤
        
        Args:
            limit: 限制處理的地址數量（用於測試）
        """
        self.logger.info("開始為所有地址打標籤...")
        
        # 獲取所有地址 ID
        address_ids = self.db.get_all_address_ids(limit)
        total = len(address_ids)
        
        self.logger.info(f"共有 {total} 個地址需要處理")
        
        tagged_count = 0
        tag_count = 0
        
        for i, address_id in enumerate(address_ids, 1):
            try:
                # 打標籤
                tags = self.tag_address(address_id)
                
                # 保存標籤
                if tags:
                    self.save_tags(address_id, tags)
                    tagged_count += 1
                    tag_count += len(tags)
                
                # 進度報告
                if i % 100 == 0 or i == total:
                    self.logger.info(
                        f"進度: {i}/{total} ({i*100//total}%) - "
                        f"已標記 {tagged_count} 個地址，共 {tag_count} 個標籤"
                    )
            
            except Exception as e:
                self.logger.error(f"處理地址 {address_id} 時出錯: {e}")
        
        self.logger.info(
            f"標籤處理完成！共為 {tagged_count} 個地址打上 {tag_count} 個標籤 "
            f"(覆蓋率: {tagged_count*100//total}%)"
        )
    
    def update_tags(self):
        """更新所有地址的標籤（增量更新）"""
        self.logger.info("開始更新標籤...")
        
        # 獲取最近有交易的地址（例如最近 7 天）
        address_ids = self.db.get_recently_active_addresses(days=7)
        
        if not address_ids:
            self.logger.info("沒有需要更新的地址")
            return
        
        self.logger.info(f"共有 {len(address_ids)} 個地址需要更新")
        
        updated_count = 0
        
        for address_id in address_ids:
            try:
                # 重新打標籤
                tags = self.tag_address(address_id)
                
                # 保存標籤
                if tags:
                    self.save_tags(address_id, tags)
                    updated_count += 1
            
            except Exception as e:
                self.logger.error(f"更新地址 {address_id} 時出錯: {e}")
        
        self.logger.info(f"標籤更新完成！共更新 {updated_count} 個地址")
    
    def generate_report(self) -> Dict[str, Any]:
        """
        生成標籤統計報告
        
        Returns:
            統計報告字典
        """
        self.logger.info("生成標籤統計報告...")
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_addresses': 0,
            'tagged_addresses': 0,
            'total_tags': 0,
            'categories': {}
        }
        
        # 總地址數
        report['total_addresses'] = self.db.get_total_addresses()
        
        # 有標籤的地址數
        report['tagged_addresses'] = self.db.get_tagged_addresses_count()
        
        # 總標籤數
        report['total_tags'] = self.db.get_total_tags_count()
        
        # 按類別統計
        for category in self.taggers.keys():
            tag_stats = self.db.get_tags_by_category(category)
            report['categories'][category] = tag_stats
        
        # 覆蓋率
        if report['total_addresses'] > 0:
            report['coverage'] = f"{report['tagged_addresses'] * 100 / report['total_addresses']:.1f}%"
        else:
            report['coverage'] = "0%"
        
        return report
    
    def print_report(self, report: Dict[str, Any]):
        """打印報告"""
        print("\n" + "="*60)
        print("地址標籤統計報告")
        print("="*60)
        print(f"生成時間: {report['generated_at']}")
        print(f"總地址數: {report['total_addresses']:,}")
        print(f"有標籤的地址數: {report['tagged_addresses']:,}")
        print(f"覆蓋率: {report['coverage']}")
        print(f"總標籤數: {report['total_tags']:,}")
        print()
        
        for category, tags in report['categories'].items():
            print(f"【{category}】")
            for tag_name, count in tags.items():
                percentage = count * 100 / report['total_addresses'] if report['total_addresses'] > 0 else 0
                print(f"  - {tag_name}: {count:,} ({percentage:.1f}%)")
            print()
        
        print("="*60)
    
    def export_to_json(self, output_path: str):
        """導出標籤到 JSON 文件"""
        self.logger.info(f"導出標籤到 {output_path}...")
        
        tags_data = self.db.get_all_tags()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(tags_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"導出完成！共 {len(tags_data)} 條記錄")
    
    def export_to_csv(self, output_path: str):
        """導出標籤到 CSV 文件"""
        import csv
        
        self.logger.info(f"導出標籤到 {output_path}...")
        
        tags_data = self.db.get_all_tags()
        
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            if tags_data:
                writer = csv.DictWriter(f, fieldnames=tags_data[0].keys())
                writer.writeheader()
                writer.writerows(tags_data)
        
        self.logger.info(f"導出完成！共 {len(tags_data)} 條記錄")


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='Polymarket 地址標籤自動標記服務')
    
    parser.add_argument('--config', default='config.json', help='配置文件路徑')
    parser.add_argument('--init', action='store_true', help='初始化數據庫並為所有地址打標籤')
    parser.add_argument('--update', action='store_true', help='更新最近活躍地址的標籤')
    parser.add_argument('--address', type=str, help='為指定地址打標籤')
    parser.add_argument('--report', action='store_true', help='生成標籤統計報告')
    parser.add_argument('--export-json', type=str, help='導出標籤到 JSON 文件')
    parser.add_argument('--export-csv', type=str, help='導出標籤到 CSV 文件')
    parser.add_argument('--limit', type=int, help='限制處理的地址數量（用於測試）')
    
    args = parser.parse_args()
    
    try:
        # 初始化服務
        service = AddressTaggingService(args.config)
        
        # 執行操作
        if args.init:
            service.init_database()
            service.tag_all_addresses(limit=args.limit)
        
        elif args.update:
            service.update_tags()
        
        elif args.address:
            address_id = int(args.address) if args.address.isdigit() else args.address
            tags = service.tag_address(address_id)
            service.save_tags(address_id, tags)
            print(f"\n地址 {address_id} 的標籤:")
            for tag in tags:
                print(f"  - [{tag['category']}] {tag['tag_name']} (信心: {tag['confidence_score']:.2f})")
        
        elif args.report:
            report = service.generate_report()
            service.print_report(report)
        
        elif args.export_json:
            service.export_to_json(args.export_json)
        
        elif args.export_csv:
            service.export_to_csv(args.export_csv)
        
        else:
            parser.print_help()
    
    except Exception as e:
        logging.error(f"執行失敗: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
