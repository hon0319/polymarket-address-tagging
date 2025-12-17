# 自動標記算法 - 可移植性說明

## 🎯 核心問題

**你的問題：** 如果我實作出自動標記算法，交接給主管時，他是否能直接使用？

**答案：是的，但需要滿足以下條件。**

---

## ✅ 可移植性設計原則

### 1. 數據庫無關性
算法應該能適配不同的數據庫結構，只需要：
- 地址表（addresses）
- 交易記錄表（address_trades）
- 市場表（markets）

### 2. 配置文件驅動
所有閾值、參數都寫在配置文件中，不寫死在代碼裡：
```json
{
  "tags": {
    "高勝率": {
      "category": "交易風格",
      "win_rate_threshold": 0.55,
      "min_trades": 5
    },
    "政治專家": {
      "category": "專長類別",
      "category_ratio_threshold": 0.50,
      "min_category_trades": 5
    }
  }
}
```

### 3. 獨立運行
算法應該是一個獨立的 Python 腳本或服務，不依賴你的專案代碼：
```bash
# 主管只需要執行
$ python address_tagging_service.py --config config.json --database mysql://...
```

### 4. 清晰的輸入輸出
- **輸入：** 數據庫連接字符串 + 配置文件
- **輸出：** 標籤數據（JSON 或直接寫入數據庫）

---

## 📦 可移植的算法架構

### 文件結構
```
address-tagging-service/
├── address_tagging_service.py  # 主程序
├── config.json                 # 配置文件
├── requirements.txt            # Python 依賴
├── README.md                   # 使用說明
├── tags/                       # 標籤邏輯模組
│   ├── __init__.py
│   ├── trading_style.py        # 交易風格標籤
│   ├── expertise.py            # 專長類別標籤
│   ├── strategy.py             # 策略類型標籤
│   ├── risk.py                 # 風險偏好標籤
│   ├── special.py              # 特殊標記標籤
│   └── social.py               # 社交影響力標籤
├── utils/                      # 工具模組
│   ├── __init__.py
│   ├── database.py             # 數據庫連接
│   ├── confidence.py           # 信心分數計算
│   └── logger.py               # 日誌記錄
└── tests/                      # 測試
    ├── test_trading_style.py
    ├── test_expertise.py
    └── ...
```

---

## 🔧 使用方式（主管視角）

### 步驟 1：安裝依賴
```bash
$ pip install -r requirements.txt
```

### 步驟 2：配置數據庫連接
```bash
# 方式 1：環境變量
$ export DATABASE_URL="mysql://user:pass@host:port/database"

# 方式 2：命令行參數
$ python address_tagging_service.py --database "mysql://user:pass@host:port/database"

# 方式 3：配置文件
# 在 config.json 中設置
{
  "database": {
    "url": "mysql://user:pass@host:port/database"
  }
}
```

### 步驟 3：運行算法
```bash
# 初始化標籤（第一次運行）
$ python address_tagging_service.py --init

# 更新標籤（定期運行）
$ python address_tagging_service.py --update

# 只處理特定地址
$ python address_tagging_service.py --address 0x123...

# 只運行特定類別的標籤
$ python address_tagging_service.py --category "交易風格"

# 生成報告
$ python address_tagging_service.py --report
```

### 步驟 4：查看結果
```bash
# 查看日誌
$ tail -f address_tagging.log

# 查看統計
$ python address_tagging_service.py --stats
```

---

## 📊 數據庫適配

### 主管的數據庫結構可能不同
算法需要能適配不同的表名和欄位名：

```json
// config.json
{
  "database": {
    "tables": {
      "addresses": "users",           // 主管可能叫 users
      "address_trades": "trades",     // 主管可能叫 trades
      "markets": "markets"
    },
    "columns": {
      "addresses": {
        "id": "user_id",              // 主管可能叫 user_id
        "win_rate": "win_rate",
        "total_trades": "trade_count",
        "total_volume": "volume"
      },
      "address_trades": {
        "address_id": "user_id",
        "market_id": "market_id",
        "timestamp": "created_at",
        "amount": "size",
        "side": "outcome"
      }
    }
  }
}
```

### 算法中的查詢適配
```python
class DatabaseAdapter:
    def __init__(self, config):
        self.config = config
        self.tables = config['database']['tables']
        self.columns = config['database']['columns']
    
    def get_addresses_table(self):
        return self.tables.get('addresses', 'addresses')
    
    def get_column(self, table, column):
        return self.columns.get(table, {}).get(column, column)
    
    def build_query(self, template):
        # 替換表名和欄位名
        query = template
        for table, table_name in self.tables.items():
            query = query.replace(f'{{table.{table}}}', table_name)
        return query

# 使用示例
adapter = DatabaseAdapter(config)
query = f"""
    SELECT {adapter.get_column('addresses', 'id')} as address_id
    FROM {adapter.get_addresses_table()}
    WHERE {adapter.get_column('addresses', 'win_rate')} >= 0.55
"""
```

---

## 🔌 輸出格式

### 方式 1：直接寫入主管的數據庫
```python
# 算法自動創建 address_tags 表（如果不存在）
# 並寫入標籤數據
```

### 方式 2：輸出 JSON 文件
```bash
$ python address_tagging_service.py --output tags.json

# tags.json
[
  {
    "address_id": "0x123...",
    "tags": [
      {
        "category": "交易風格",
        "tag_name": "高勝率",
        "confidence_score": 0.85
      },
      {
        "category": "專長類別",
        "tag_name": "政治專家",
        "confidence_score": 0.92
      }
    ]
  },
  ...
]
```

### 方式 3：輸出 CSV 文件
```bash
$ python address_tagging_service.py --output tags.csv

# tags.csv
address_id,category,tag_name,confidence_score
0x123...,交易風格,高勝率,0.85
0x123...,專長類別,政治專家,0.92
...
```

### 方式 4：API 服務
```bash
# 啟動 API 服務
$ python address_tagging_service.py --serve --port 8000

# 主管可以通過 API 調用
$ curl http://localhost:8000/tag/0x123...
{
  "address_id": "0x123...",
  "tags": [...]
}
```

---

## 📝 配置文件範例

```json
{
  "database": {
    "url": "mysql://user:pass@host:port/database",
    "tables": {
      "addresses": "addresses",
      "address_trades": "address_trades",
      "markets": "markets"
    },
    "columns": {
      "addresses": {
        "id": "id",
        "win_rate": "win_rate",
        "total_trades": "total_trades",
        "total_volume": "total_volume",
        "avg_trade_size": "avg_trade_size",
        "created_at": "created_at"
      },
      "address_trades": {
        "id": "id",
        "address_id": "address_id",
        "market_id": "market_id",
        "timestamp": "timestamp",
        "amount": "amount",
        "side": "side",
        "price": "price",
        "pnl": "pnl",
        "exit_timestamp": "exit_timestamp"
      },
      "markets": {
        "id": "id",
        "category": "category",
        "title": "title",
        "created_at": "created_at",
        "end_date": "end_date"
      }
    }
  },
  "tags": {
    "交易風格": {
      "高勝率": {
        "enabled": true,
        "win_rate_threshold": 0.55,
        "min_trades": 5
      },
      "大交易量": {
        "enabled": true,
        "avg_trade_size_threshold": 5000,
        "min_large_trades": 3,
        "large_trade_threshold": 5000
      },
      "高頻交易": {
        "enabled": true,
        "trades_per_day_threshold": 5,
        "lookback_days": 30
      }
    },
    "專長類別": {
      "政治專家": {
        "enabled": true,
        "category": "Politics",
        "ratio_threshold": 0.50,
        "min_category_trades": 5
      }
    }
  },
  "confidence": {
    "method": "linear",  // linear, exponential, sigmoid
    "min_confidence": 0.0,
    "max_confidence": 1.0
  },
  "output": {
    "format": "database",  // database, json, csv, api
    "create_tables": true,
    "update_existing": true
  },
  "logging": {
    "level": "INFO",
    "file": "address_tagging.log"
  }
}
```

---

## 🚀 主管可以做的事

### 1. 調整閾值
```json
// 主管覺得 55% 勝率太低，改成 60%
{
  "tags": {
    "交易風格": {
      "高勝率": {
        "win_rate_threshold": 0.60  // 從 0.55 改成 0.60
      }
    }
  }
}
```

### 2. 啟用/禁用標籤
```json
// 主管暫時不需要「社交影響力」標籤
{
  "tags": {
    "社交影響力": {
      "KOL": {
        "enabled": false  // 禁用
      }
    }
  }
}
```

### 3. 添加新標籤
```python
# 主管可以在 tags/custom.py 中添加自定義標籤
class CustomTags:
    @staticmethod
    def whale_hunter(address_data, config):
        """獵鯨者：專門狙擊大戶的交易者"""
        # 自定義邏輯
        pass
```

### 4. 整合到自己的系統
```python
# 主管可以將算法作為模組導入
from address_tagging_service import AddressTaggingService

service = AddressTaggingService(config_path='config.json')
tags = service.tag_address('0x123...')
```

---

## 📦 交付清單

### 給主管的完整包
```
address-tagging-service.zip
├── address_tagging_service.py    # 主程序
├── config.json                   # 配置文件（含註釋）
├── requirements.txt              # Python 依賴
├── README.md                     # 詳細使用說明
├── INSTALL.md                    # 安裝指南
├── EXAMPLES.md                   # 使用範例
├── tags/                         # 標籤邏輯模組
├── utils/                        # 工具模組
├── tests/                        # 測試
└── docker/                       # Docker 部署（可選）
    ├── Dockerfile
    └── docker-compose.yml
```

### README.md 內容
```markdown
# 地址標籤自動標記服務

## 快速開始

### 1. 安裝
```bash
pip install -r requirements.txt
```

### 2. 配置
編輯 `config.json`，設置數據庫連接

### 3. 運行
```bash
python address_tagging_service.py --init
```

## 配置說明
- `database.url`: 數據庫連接字符串
- `tags.*.enabled`: 啟用/禁用標籤
- `tags.*.threshold`: 調整閾值

## 常見問題
Q: 如何調整勝率閾值？
A: 修改 config.json 中的 `tags.交易風格.高勝率.win_rate_threshold`

Q: 如何只運行部分標籤？
A: 使用 `--category` 參數或在 config.json 中設置 `enabled: false`
```

---

## ✅ 可移植性檢查清單

### 主管能直接使用的條件

- [ ] **無硬編碼**：所有閾值、參數都在配置文件中
- [ ] **數據庫適配**：支持不同的表名和欄位名
- [ ] **獨立運行**：不依賴你的專案代碼
- [ ] **清晰文檔**：README、INSTALL、EXAMPLES 齊全
- [ ] **錯誤處理**：有清晰的錯誤提示和日誌
- [ ] **測試覆蓋**：有單元測試，主管可以驗證
- [ ] **多種輸出**：支持數據庫、JSON、CSV、API
- [ ] **易於擴展**：主管可以添加自定義標籤
- [ ] **版本管理**：有版本號，方便追蹤更新

---

## 🎯 總結

### 主管能直接使用的前提

1. ✅ **算法是獨立的**：不依賴你的專案代碼
2. ✅ **配置是靈活的**：主管可以調整閾值、表名、欄位名
3. ✅ **文檔是完整的**：主管知道如何安裝、配置、運行
4. ✅ **輸出是標準的**：JSON、CSV 或直接寫入數據庫
5. ✅ **錯誤是友好的**：有清晰的錯誤提示和日誌

### 如果做到以上 5 點

**主管可以：**
- 直接運行算法，無需修改代碼
- 調整配置文件，適配自己的數據庫
- 整合到自己的系統中
- 添加自定義標籤
- 定時自動運行

**主管不需要：**
- 了解你的專案代碼
- 了解你的數據庫結構
- 重新實作算法邏輯

---

✅ **結論：** 只要按照上述架構設計，主管可以直接使用你的自動標記算法，無需了解你的代碼細節。
