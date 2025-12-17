"""
數據庫適配器模組

提供數據庫連接和查詢功能，支持不同的表名和欄位名配置
"""

import mysql.connector
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse


class DatabaseAdapter:
    """數據庫適配器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化數據庫適配器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.db_config = config['database']
        self.tables = self.db_config['tables']
        self.columns = self.db_config['columns']
        
        # 解析數據庫 URL
        self.connection = self._create_connection()
    
    def _create_connection(self):
        """創建數據庫連接"""
        url = self.db_config['url']
        parsed = urlparse(url)
        
        return mysql.connector.connect(
            host=parsed.hostname,
            port=parsed.port or 3306,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path.lstrip('/'),
            autocommit=True
        )
    
    def execute(self, sql: str, params: tuple = None) -> Any:
        """
        執行 SQL 語句
        
        Args:
            sql: SQL 語句
            params: 參數
            
        Returns:
            執行結果
        """
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(sql, params)
            if sql.strip().upper().startswith('SELECT'):
                return cursor.fetchall()
            else:
                return cursor.rowcount
        finally:
            cursor.close()
    
    def get_table_name(self, table_key: str) -> str:
        """獲取實際的表名"""
        return self.tables.get(table_key, table_key)
    
    def get_column_name(self, table_key: str, column_key: str) -> str:
        """獲取實際的欄位名"""
        return self.columns.get(table_key, {}).get(column_key, column_key)
    
    def get_address_data(self, address_id: int) -> Optional[Dict[str, Any]]:
        """
        獲取地址數據
        
        Args:
            address_id: 地址 ID
            
        Returns:
            地址數據字典
        """
        table = self.get_table_name('addresses')
        sql = f"SELECT * FROM {table} WHERE id = %s"
        
        result = self.execute(sql, (address_id,))
        return result[0] if result else None
    
    def get_all_address_ids(self, limit: Optional[int] = None) -> List[int]:
        """
        獲取所有地址 ID
        
        Args:
            limit: 限制數量
            
        Returns:
            地址 ID 列表
        """
        table = self.get_table_name('addresses')
        sql = f"SELECT id FROM {table}"
        
        if limit:
            sql += f" LIMIT {limit}"
        
        result = self.execute(sql)
        return [row['id'] for row in result]
    
    def get_recently_active_addresses(self, days: int = 7) -> List[int]:
        """
        獲取最近活躍的地址 ID
        
        Args:
            days: 天數
            
        Returns:
            地址 ID 列表
        """
        trades_table = self.get_table_name('address_trades')
        timestamp_col = self.get_column_name('address_trades', 'timestamp')
        address_id_col = self.get_column_name('address_trades', 'address_id')
        
        sql = f"""
        SELECT DISTINCT {address_id_col} as address_id
        FROM {trades_table}
        WHERE {timestamp_col} >= DATE_SUB(NOW(), INTERVAL {days} DAY)
        """
        
        result = self.execute(sql)
        return [row['address_id'] for row in result]
    
    def get_total_addresses(self) -> int:
        """獲取總地址數"""
        table = self.get_table_name('addresses')
        sql = f"SELECT COUNT(*) as count FROM {table}"
        
        result = self.execute(sql)
        return result[0]['count'] if result else 0
    
    def get_tagged_addresses_count(self) -> int:
        """獲取有標籤的地址數"""
        sql = "SELECT COUNT(DISTINCT address_id) as count FROM address_tags"
        
        result = self.execute(sql)
        return result[0]['count'] if result else 0
    
    def get_total_tags_count(self) -> int:
        """獲取總標籤數"""
        sql = "SELECT COUNT(*) as count FROM address_tags"
        
        result = self.execute(sql)
        return result[0]['count'] if result else 0
    
    def get_tags_by_category(self, category: str) -> Dict[str, int]:
        """
        獲取指定類別的標籤統計
        
        Args:
            category: 標籤類別
            
        Returns:
            標籤名稱 -> 數量的字典
        """
        sql = """
        SELECT tag_name, COUNT(*) as count
        FROM address_tags
        WHERE category = %s
        GROUP BY tag_name
        ORDER BY count DESC
        """
        
        result = self.execute(sql, (category,))
        return {row['tag_name']: row['count'] for row in result}
    
    def get_all_tags(self) -> List[Dict[str, Any]]:
        """獲取所有標籤"""
        sql = """
        SELECT 
            address_id,
            category,
            tag_name,
            confidence_score,
            is_manual,
            created_at,
            updated_at
        FROM address_tags
        ORDER BY address_id, category, tag_name
        """
        
        return self.execute(sql)
    
    def get_category_trades(self, address_id: int, category: str) -> int:
        """
        獲取地址在指定類別的交易次數
        
        Args:
            address_id: 地址 ID
            category: 市場類別
            
        Returns:
            交易次數
        """
        trades_table = self.get_table_name('address_trades')
        markets_table = self.get_table_name('markets')
        address_id_col = self.get_column_name('address_trades', 'address_id')
        market_id_col = self.get_column_name('address_trades', 'market_id')
        category_col = self.get_column_name('markets', 'category')
        
        sql = f"""
        SELECT COUNT(*) as count
        FROM {trades_table} t
        JOIN {markets_table} m ON t.{market_id_col} = m.id
        WHERE t.{address_id_col} = %s AND m.{category_col} = %s
        """
        
        result = self.execute(sql, (address_id, category))
        return result[0]['count'] if result else 0
    
    def get_keyword_trades(self, address_id: int, keywords: List[str], parent_category: Optional[str] = None) -> int:
        """
        獲取地址在包含關鍵詞的市場的交易次數
        
        Args:
            address_id: 地址 ID
            keywords: 關鍵詞列表
            parent_category: 父類別（可選）
            
        Returns:
            交易次數
        """
        trades_table = self.get_table_name('address_trades')
        markets_table = self.get_table_name('markets')
        address_id_col = self.get_column_name('address_trades', 'address_id')
        market_id_col = self.get_column_name('address_trades', 'market_id')
        title_col = self.get_column_name('markets', 'title')
        category_col = self.get_column_name('markets', 'category')
        
        # 構建關鍵詞條件
        keyword_conditions = ' OR '.join([f"m.{title_col} LIKE %s" for _ in keywords])
        keyword_params = [f"%{kw}%" for kw in keywords]
        
        sql = f"""
        SELECT COUNT(*) as count
        FROM {trades_table} t
        JOIN {markets_table} m ON t.{market_id_col} = m.id
        WHERE t.{address_id_col} = %s
        AND ({keyword_conditions})
        """
        
        params = [address_id] + keyword_params
        
        if parent_category:
            sql += f" AND m.{category_col} = %s"
            params.append(parent_category)
        
        result = self.execute(sql, tuple(params))
        return result[0]['count'] if result else 0
    
    def get_recent_trades_count(self, address_id: int, days: int = 30) -> int:
        """
        獲取地址最近的交易次數
        
        Args:
            address_id: 地址 ID
            days: 天數
            
        Returns:
            交易次數
        """
        trades_table = self.get_table_name('address_trades')
        address_id_col = self.get_column_name('address_trades', 'address_id')
        timestamp_col = self.get_column_name('address_trades', 'timestamp')
        
        sql = f"""
        SELECT COUNT(*) as count
        FROM {trades_table}
        WHERE {address_id_col} = %s
        AND {timestamp_col} >= DATE_SUB(NOW(), INTERVAL {days} DAY)
        """
        
        result = self.execute(sql, (address_id,))
        return result[0]['count'] if result else 0
    
    def get_monthly_pnl(self, address_id: int) -> List[Dict[str, Any]]:
        """
        獲取地址的月度盈虧
        
        Args:
            address_id: 地址 ID
            
        Returns:
            月度盈虧列表
        """
        trades_table = self.get_table_name('address_trades')
        address_id_col = self.get_column_name('address_trades', 'address_id')
        timestamp_col = self.get_column_name('address_trades', 'timestamp')
        pnl_col = self.get_column_name('address_trades', 'pnl')
        
        sql = f"""
        SELECT 
            DATE_FORMAT({timestamp_col}, '%Y-%m') as month,
            SUM({pnl_col}) as monthly_pnl
        FROM {trades_table}
        WHERE {address_id_col} = %s
        GROUP BY month
        ORDER BY month
        """
        
        return self.execute(sql, (address_id,))
    
    def get_price_distribution(self, address_id: int) -> List[Dict[str, Any]]:
        """
        獲取地址的價格分布
        
        Args:
            address_id: 地址 ID
            
        Returns:
            價格分布列表
        """
        trades_table = self.get_table_name('address_trades')
        address_id_col = self.get_column_name('address_trades', 'address_id')
        price_col = self.get_column_name('address_trades', 'price')
        
        sql = f"""
        SELECT {price_col} as price
        FROM {trades_table}
        WHERE {address_id_col} = %s
        """
        
        return self.execute(sql, (address_id,))
    
    def get_late_entry_trades(self, address_id: int, days_before_close: int = 3) -> int:
        """
        獲取地址在市場結算前 N 天內的交易次數
        
        Args:
            address_id: 地址 ID
            days_before_close: 結算前天數
            
        Returns:
            交易次數
        """
        trades_table = self.get_table_name('address_trades')
        markets_table = self.get_table_name('markets')
        address_id_col = self.get_column_name('address_trades', 'address_id')
        market_id_col = self.get_column_name('address_trades', 'market_id')
        timestamp_col = self.get_column_name('address_trades', 'timestamp')
        end_date_col = self.get_column_name('markets', 'end_date')
        
        sql = f"""
        SELECT COUNT(*) as count
        FROM {trades_table} t
        JOIN {markets_table} m ON t.{market_id_col} = m.id
        WHERE t.{address_id_col} = %s
        AND m.{end_date_col} IS NOT NULL
        AND TIMESTAMPDIFF(DAY, t.{timestamp_col}, m.{end_date_col}) <= {days_before_close}
        """
        
        result = self.execute(sql, (address_id,))
        return result[0]['count'] if result else 0
    
    def get_early_entry_trades(self, address_id: int, hours_after_creation: int = 48) -> int:
        """
        獲取地址在市場創建後 N 小時內的交易次數
        
        Args:
            address_id: 地址 ID
            hours_after_creation: 創建後小時數
            
        Returns:
            交易次數
        """
        trades_table = self.get_table_name('address_trades')
        markets_table = self.get_table_name('markets')
        address_id_col = self.get_column_name('address_trades', 'address_id')
        market_id_col = self.get_column_name('address_trades', 'market_id')
        timestamp_col = self.get_column_name('address_trades', 'timestamp')
        created_at_col = self.get_column_name('markets', 'created_at')
        
        sql = f"""
        SELECT COUNT(*) as count
        FROM {trades_table} t
        JOIN {markets_table} m ON t.{market_id_col} = m.id
        WHERE t.{address_id_col} = %s
        AND m.{created_at_col} IS NOT NULL
        AND TIMESTAMPDIFF(HOUR, m.{created_at_col}, t.{timestamp_col}) <= {hours_after_creation}
        """
        
        result = self.execute(sql, (address_id,))
        return result[0]['count'] if result else 0
    
    def close(self):
        """關閉數據庫連接"""
        if self.connection:
            self.connection.close()
