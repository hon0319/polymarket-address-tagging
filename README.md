# Polymarket 地址標籤自動標記服務

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

根據 Polymarket 地址的交易行為自動打上標籤，幫助識別和分類不同類型的交易者。

## 🎯 功能特點

- **19 種標籤**（第一階段）：涵蓋交易風格、專長類別、風險偏好、策略類型
- **配置驅動**：所有閾值和參數都可在配置文件中調整
- **數據庫適配**：支持不同的表名和欄位名，易於整合到現有系統
- **信心分數**：每個標籤都有 0-1 的信心分數，表示可信度
- **多種輸出**：支持數據庫、JSON、CSV 格式
- **易於擴展**：模組化設計，方便添加新標籤

## 📊 標籤體系

### 1. 🎯 交易風格 (Trading Style) - 8 種
高勝率、大交易量、高頻交易、穩定盈利、小額多單、波段交易者、長期持有者、閃電交易者

### 2. 🏆 專長類別 (Expertise Category) - 10 種
政治專家、體育專家、加密專家、NFL專家、NBA專家、娛樂專家、經濟專家、選舉專家、足球專家、全能型

### 3. 📊 策略類型 (Strategy Type) - 12 種
掃尾盤、逆勢操作、順勢操作、價值捕手、早期進場、套利者、事件驅動、對沖交易者、做市商、趨勢追蹤者、均值回歸者、狙擊手

### 4. ⚠️ 風險偏好 (Risk Preference) - 6 種
低風險、高風險、均衡型、Degen、保守型、激進型

### 5. 🌟 特殊標記 (Special Tags) - 10 種
疑似內線、新聞追蹤、名人、機器人/腳本、多帳號操作、市場操縱嫌疑、專業機構、新手、休眠喚醒、單一市場專注

### 6. 👥 社交影響力 (Social Influence) - 4 種
KOL、社群領袖、跟單目標、隱形巨鯨

完整的 50 種標籤體系請參考：[ADDRESS_TAGGING_SYSTEM.md](ADDRESS_TAGGING_SYSTEM.md)

## 🚀 快速開始

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 配置數據庫

編輯 `config.json`：

```json
{
  "database": {
    "url": "mysql://user:password@host:port/database"
  }
}
```

### 3. 運行服務

```bash
# 測試模式（處理 10 個地址）
python address_tagging_service.py --init --limit 10

# 正式運行（處理所有地址）
python address_tagging_service.py --init

# 查看統計報告
python address_tagging_service.py --report
```

詳細使用說明請參考：[QUICKSTART.md](QUICKSTART.md)

## 📂 項目結構

```
polymarket-address-tagging/
├── address_tagging_service.py  # 主程序
├── config.json                 # 配置文件
├── requirements.txt            # Python 依賴
├── README.md                   # 本文件
├── QUICKSTART.md              # 快速開始指南
├── ADDRESS_TAGGING_SYSTEM.md  # 完整標籤體系（50 種）
├── AUTO_TAGGING_PORTABILITY_GUIDE.md  # 可移植性設計指南
├── tags/                       # 標籤邏輯模組
│   ├── trading_style.py        # 交易風格標籤
│   ├── expertise.py            # 專長類別標籤
│   ├── risk.py                 # 風險偏好標籤
│   └── strategy.py             # 策略類型標籤
└── utils/                      # 工具模組
    ├── database.py             # 數據庫適配器
    ├── confidence.py           # 信心分數計算器
    └── logger.py               # 日誌記錄器
```

## 📖 文檔

- **[QUICKSTART.md](QUICKSTART.md)** - 5 分鐘快速開始指南
- **[ADDRESS_TAGGING_SYSTEM.md](ADDRESS_TAGGING_SYSTEM.md)** - 完整的 50 種標籤體系和篩選邏輯
- **[AUTO_TAGGING_PORTABILITY_GUIDE.md](AUTO_TAGGING_PORTABILITY_GUIDE.md)** - 可移植性設計指南，如何整合到其他系統

## 🎯 使用場景

### 1. 地址分析
```bash
python address_tagging_service.py --address 12345
```

輸出：
```
地址 12345 的標籤:
  - [交易風格] 高勝率 (信心: 0.85)
  - [專長類別] 政治專家 (信心: 0.92)
  - [風險偏好] 低風險 (信心: 0.78)
  - [策略類型] 早期進場 (信心: 0.65)
```

### 2. 批量標記
```bash
# 為所有地址打標籤
python address_tagging_service.py --init

# 更新最近活躍地址
python address_tagging_service.py --update
```

### 3. 數據導出
```bash
# 導出為 JSON
python address_tagging_service.py --export-json tags.json

# 導出為 CSV
python address_tagging_service.py --export-csv tags.csv
```

### 4. 統計報告
```bash
python address_tagging_service.py --report
```

## ⚙️ 配置說明

### 調整閾值

編輯 `config.json` 調整標籤的判斷標準：

```json
{
  "tags": {
    "交易風格": {
      "高勝率": {
        "enabled": true,
        "win_rate_threshold": 0.55,  // 勝率閾值（可調整）
        "min_trades": 5               // 最小交易次數（可調整）
      }
    }
  }
}
```

### 啟用/禁用標籤

```json
{
  "tags": {
    "交易風格": {
      "高勝率": {
        "enabled": false  // 禁用此標籤
      }
    }
  }
}
```

### 適配不同數據庫

如果你的數據庫表名或欄位名不同：

```json
{
  "database": {
    "tables": {
      "addresses": "users",           // 映射表名
      "address_trades": "trades"
    },
    "columns": {
      "addresses": {
        "id": "user_id",              // 映射欄位名
        "win_rate": "win_rate"
      }
    }
  }
}
```

## 🔧 數據庫表結構

服務會自動創建 `address_tags` 表：

```sql
CREATE TABLE address_tags (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    address_id BIGINT NOT NULL,
    category VARCHAR(50) NOT NULL,
    tag_name VARCHAR(50) NOT NULL,
    confidence_score DECIMAL(3,2) DEFAULT 1.00,
    is_manual BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_address_tag (address_id, tag_name)
);
```

## 📊 實作階段

### ✅ 第一階段（已完成）- 19 種標籤
- 只需要現有數據（addresses, address_trades, markets）
- 覆蓋率：60-70% 的地址至少有 1 個標籤
- 開發時間：1-2 天

### ⏳ 第二階段（計劃中）- 15 種標籤
- 需要持倉數據（exit_timestamp）
- 覆蓋率：70-80% 的地址至少有 1 個標籤
- 開發時間：3-5 天

### 🔮 第三階段（計劃中）- 16 種標籤
- 需要外部 API（新聞、社交媒體）
- 覆蓋率：80-90% 的地址至少有 1 個標籤
- 開發時間：1-2 週

## 🎨 整合到前端

### 查詢地址標籤

```python
from address_tagging_service import AddressTaggingService

service = AddressTaggingService(config_path='config.json')
tags = service.tag_address(12345)

# 返回格式
[
    {
        'category': '交易風格',
        'tag_name': '高勝率',
        'confidence_score': 0.85
    },
    ...
]
```

### 按標籤篩選地址

```sql
-- 查詢所有「高勝率」的地址
SELECT DISTINCT address_id
FROM address_tags
WHERE tag_name = '高勝率'
AND confidence_score >= 0.7;

-- 查詢同時有「政治專家」和「高勝率」標籤的地址
SELECT address_id
FROM address_tags
WHERE tag_name IN ('政治專家', '高勝率')
GROUP BY address_id
HAVING COUNT(DISTINCT tag_name) = 2;
```

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

### 添加新標籤

1. 在 `tags/` 目錄下創建新的標籤器模組
2. 在 `config.json` 中添加配置
3. 在 `address_tagging_service.py` 中註冊新的標籤器
4. 添加測試和文檔

## 📝 常見問題

### Q: 如何定時自動運行？
A: 使用 cron（Linux）或 Task Scheduler（Windows）：
```bash
# 每天凌晨 2 點更新標籤
0 2 * * * cd /path/to/service && python address_tagging_service.py --update
```

### Q: 信心分數是如何計算的？
A: 信心分數反映標籤的可信度：
- 實際值剛好達到閾值 → 信心分數較低（0.0-0.5）
- 實際值遠超閾值 → 信心分數較高（0.5-1.0）
- 可選擇計算方法：linear、exponential、sigmoid

### Q: 如何整合到現有系統？
A: 參考 [AUTO_TAGGING_PORTABILITY_GUIDE.md](AUTO_TAGGING_PORTABILITY_GUIDE.md)

## 📄 授權

MIT License

## 📧 聯繫

如有問題，請在 GitHub 上提交 Issue。

---

**相關專案：**
- [Polymarket Insights](https://github.com/hon0319/polymarket-insights) - Polymarket 市場分析平台
