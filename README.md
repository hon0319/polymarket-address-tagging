# Polymarket 地址標籤自動標記服務

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

**完整的 Polymarket 地址標籤自動標記系統，支持 50 種標籤，6 個維度的用戶畫像分析。**

---

## 📊 項目概述

本項目提供了一套完整的地址標籤自動標記算法，用於分析 Polymarket 用戶的交易行為、專長領域、策略類型、風險偏好和社交影響力。

### 核心特性

- ✅ **50 種標籤**：涵蓋交易風格、專長類別、策略類型、風險偏好、特殊標記、社交影響力 6 個維度
- ✅ **三階段實作**：漸進式整合，從基礎標籤到高級標籤
- ✅ **適配器模式**：算法邏輯與數據源解耦，易於整合到任何系統
- ✅ **配置驅動**：所有閾值可調整，支持自定義數據庫結構
- ✅ **信心分數**：每個標籤都有 0-1 的信心分數，量化標記準確度
- ✅ **多種輸出格式**：支持數據庫、JSON、CSV 等多種輸出方式

---

## 🎯 標籤體系

### 6 個維度，50 種標籤

| 維度 | 標籤數量 | 標籤列表 |
|------|---------|---------|
| **🎯 交易風格** | 8 種 | 高勝率、大交易量、高頻交易、穩定盈利、小額多單、波段交易者、長期持有者、閃電交易者 |
| **🏆 專長類別** | 10 種 | 政治專家、體育專家、加密專家、NFL專家、NBA專家、娛樂專家、經濟專家、選舉專家、足球專家、全能型 |
| **📊 策略類型** | 12 種 | 掃尾盤、逆勢操作、順勢操作、價值捕手、早期進場、套利者、事件驅動、對沖交易者、做市商、趨勢追蹤者、均值回歸者、狙擊手 |
| **⚠️ 風險偏好** | 6 種 | 低風險、高風險、均衡型、Degen、保守型、激進型 |
| **🌟 特殊標記** | 10 種 | 疑似內線、新聞追蹤、名人、機器人/腳本、多帳號操作、市場操縱嫌疑、專業機構、新手、休眠喚醒、單一市場專注 |
| **👥 社交影響力** | 4 種 | KOL、社群領袖、跟單目標、隱形巨鯨 |

完整的標籤體系和篩選邏輯請參考：[ADDRESS_TAGGING_SYSTEM.md](ADDRESS_TAGGING_SYSTEM.md)

---

## 🚀 快速開始

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 配置數據庫

編輯 `config.json`，設置你的數據庫連接：

```json
{
  "database": {
    "url": "mysql://user:password@host:port/database",
    "tables": {
      "addresses": "addresses",
      "address_trades": "address_trades",
      "markets": "markets"
    }
  }
}
```

### 3. 運行標記服務

```bash
# 初始化：為所有地址打標籤
python address_tagging_service.py --init

# 更新：為最近活躍地址更新標籤
python address_tagging_service.py --update

# 為單個地址打標籤
python address_tagging_service.py --address 123

# 生成統計報告
python address_tagging_service.py --report
```

### 4. 導出標籤

```bash
# 導出為 JSON
python address_tagging_service.py --export-json tags.json

# 導出為 CSV
python address_tagging_service.py --export-csv tags.csv
```

詳細使用說明請參考：[QUICKSTART.md](QUICKSTART.md)

---

## 📚 三階段實作

本項目採用漸進式設計，可以根據數據可用性分階段實作：

### 第一階段：基礎標籤（19 種）

**數據需求：** 只需要現有的交易數據

**包含標籤：**
- 交易風格：高勝率、大交易量、高頻交易、穩定盈利、小額多單
- 專長類別：政治/體育/加密/娛樂/經濟/選舉/NFL/NBA/足球專家、全能型
- 風險偏好：低風險、高風險
- 策略類型：掃尾盤、早期進場

**使用方式：**
```python
from address_tagging_service import AddressTaggingService

service = AddressTaggingService()
service.tag_all_addresses()  # 自動打 19 種基礎標籤
```

---

### 第二階段：持倉分析標籤（+15 種）

**數據需求：** 需要持倉時間、價格歷史等數據

**包含標籤：**
- 交易風格：波段交易者、長期持有者、閃電交易者
- 風險偏好：均衡型、保守型、激進型
- 策略類型：逆勢操作、順勢操作、價值捕手、套利者、對沖交易者、做市商、趨勢追蹤者、均值回歸者、狙擊手

**使用方式：**
```python
from address_tagging_service import AddressTaggingService
from my_adapter import MyPhase2Adapter

# 實作數據適配器（5-10 行代碼）
adapter = MyPhase2Adapter()
service = AddressTaggingService(data_adapter=adapter)
service.tag_all_addresses()  # 自動打 34 種標籤（第一+第二階段）
```

---

### 第三階段：高級分析標籤（+16 種）

**數據需求：** 需要新聞 API、社交媒體 API 等外部數據

**包含標籤：**
- 特殊標記：疑似內線、新聞追蹤、名人、機器人/腳本、多帳號操作、市場操縱嫌疑、專業機構、新手、休眠喚醒、單一市場專注
- 社交影響力：KOL、社群領袖、跟單目標、隱形巨鯨

**使用方式：**
```python
from address_tagging_service import AddressTaggingService
from my_adapter import MyFullAdapter

# 實作完整的數據適配器
adapter = MyFullAdapter(news_api_key='xxx', twitter_token='yyy')
service = AddressTaggingService(data_adapter=adapter)
service.tag_all_addresses()  # 自動打所有 50 種標籤
```

---

## 🔧 數據適配器

本項目使用**適配器模式**，讓你可以輕鬆整合到自己的系統中。

### 為什麼需要適配器？

- 不同系統的數據結構不同
- 第二和第三階段需要額外的數據源
- 算法邏輯與數據源解耦，易於維護

### 如何實作適配器？

**最小實作（只需 5 行代碼）：**

```python
from adapters.base import DataAdapter

class MyAdapter(DataAdapter):
    """你的數據適配器"""
    
    def get_price_history(self, market_id: int):
        # 從你的數據庫查詢價格歷史
        return self.db.query("SELECT * FROM prices WHERE market_id = %s", market_id)
    
    def get_position_changes(self, address_id: int):
        # 從你的數據庫查詢持倉變化
        return self.db.query("SELECT * FROM positions WHERE address_id = %s", address_id)
```

**詳細的適配器實作指南請查看：** [ADAPTER_GUIDE.md](ADAPTER_GUIDE.md)

---

## 📖 文檔

| 文檔 | 說明 |
|------|------|
| [README.md](README.md) | 項目概述和快速開始（本文件） |
| [QUICKSTART.md](QUICKSTART.md) | 5 分鐘快速上手指南 |
| [ADDRESS_TAGGING_SYSTEM.md](ADDRESS_TAGGING_SYSTEM.md) | 完整的 50 種標籤體系和篩選邏輯 |
| [ADAPTER_GUIDE.md](ADAPTER_GUIDE.md) | 數據適配器實作指南（含完整示例） |
| [AUTO_TAGGING_PORTABILITY_GUIDE.md](AUTO_TAGGING_PORTABILITY_GUIDE.md) | 可移植性設計指南 |

---

## 🏗️ 項目結構

```
polymarket-address-tagging/
├── address_tagging_service.py  # 主程序
├── config.json                 # 配置文件（包含所有 50 種標籤配置）
├── requirements.txt            # Python 依賴
│
├── adapters/                   # 數據適配器
│   ├── base.py                 # 適配器基類（接口定義）
│   └── mock.py                 # 模擬數據適配器（用於測試）
│
├── tags/                       # 標籤邏輯模組
│   ├── trading_style.py        # 交易風格（第一階段）
│   ├── expertise.py            # 專長類別（第一階段）
│   ├── risk.py                 # 風險偏好（第一階段）
│   ├── strategy.py             # 策略類型（第一階段）
│   ├── trading_style_phase2.py # 交易風格（第二階段）
│   ├── risk_phase2.py          # 風險偏好（第二階段）
│   ├── strategy_phase2.py      # 策略類型（第二階段）
│   ├── special_phase3.py       # 特殊標記（第三階段）
│   └── social_phase3.py        # 社交影響力（第三階段）
│
└── utils/                      # 工具模組
    ├── database.py             # 數據庫適配器
    ├── confidence.py           # 信心分數計算器
    └── logger.py               # 日誌記錄器
```

---

## 💡 使用場景

### 1. 初始化標籤系統

```bash
python address_tagging_service.py --init
```

**輸出：**
```
✅ 初始化完成
   已標記地址：6,500/10,000
   總標籤數：15,000
```

---

### 2. 定時更新標籤

```bash
# 每天運行，更新最近活躍地址的標籤
python address_tagging_service.py --update
```

**輸出：**
```
✅ 更新完成
   已更新地址：1,200
   總標籤數：3,500
```

---

### 3. 為單個地址打標籤

```bash
python address_tagging_service.py --address 12345
```

**輸出：**
```
地址 12345 的標籤：
  [交易風格] 高勝率 (信心: 0.85)
  [專長類別] 政治專家 (信心: 0.92)
  [策略類型] 早期進場 (信心: 0.78)
  [風險偏好] 低風險 (信心: 0.81)
```

---

### 4. 生成統計報告

```bash
python address_tagging_service.py --report
```

**輸出：**
```
📊 標籤統計報告
   總地址數：10,000
   已標記地址：6,500
   標記率：65.0%
   總標籤數：15,000
   平均每地址標籤數：2.31
```

---

### 5. 整合到前端

```typescript
// 獲取地址標籤
const tags = await trpc.address.getTags.query({ addressId: 123 });

// 顯示標籤
{tags.map(tag => (
  <Badge key={tag.id} variant={tag.category}>
    {tag.tag_name} ({(tag.confidence_score * 100).toFixed(0)}%)
  </Badge>
))}

// 按標籤篩選地址
const addresses = await trpc.address.list.query({
  tags: ['高勝率', '政治專家'],
  minConfidence: 0.7
});
```

---

## ⚙️ 配置說明

### 調整標籤閾值

編輯 `config.json`：

```json
{
  "tags": {
    "交易風格": {
      "高勝率": {
        "enabled": true,
        "win_rate_threshold": 0.55,  // 調整閾值
        "min_trades": 5
      }
    }
  }
}
```

### 禁用特定標籤

```json
{
  "tags": {
    "特殊標記": {
      "疑似內線": {
        "enabled": false  // 禁用此標籤
      }
    }
  }
}
```

### 自定義數據庫結構

```json
{
  "database": {
    "tables": {
      "addresses": "my_addresses_table",
      "address_trades": "my_trades_table"
    },
    "columns": {
      "addresses": {
        "id": "user_id",
        "win_rate": "success_rate"
      }
    }
  }
}
```

---

## 🔒 數據庫表結構

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

---

## 🧪 測試

### 使用模擬數據測試

```bash
# 測試 10 個地址
python address_tagging_service.py --init --limit 10 --use-mock
```

### 單元測試

```bash
# 運行所有測試
python -m pytest tests/

# 測試特定標籤器
python -m pytest tests/test_trading_style.py
```

---

## 📊 性能

| 操作 | 地址數量 | 處理時間 | 吞吐量 |
|------|---------|---------|--------|
| 第一階段標記 | 10,000 | ~10 分鐘 | ~1,000 地址/分鐘 |
| 第二階段標記 | 10,000 | ~20 分鐘 | ~500 地址/分鐘 |
| 第三階段標記 | 10,000 | ~30 分鐘 | ~333 地址/分鐘 |

*測試環境：8 核 CPU，16GB RAM，MySQL 數據庫*

---

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

### 開發指南

1. Fork 本項目
2. 創建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

---

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
A: 參考 [ADAPTER_GUIDE.md](ADAPTER_GUIDE.md) 和 [AUTO_TAGGING_PORTABILITY_GUIDE.md](AUTO_TAGGING_PORTABILITY_GUIDE.md)

---

## 📄 授權

MIT License

---

## 📞 聯繫方式

- **GitHub Issues**: [提交問題](https://github.com/hon0319/polymarket-address-tagging/issues)

---

## 🗺️ Roadmap

- [x] 第一階段標籤（19 種）
- [x] 第二階段標籤（15 種）
- [x] 第三階段標籤（16 種）
- [x] 適配器模式設計
- [ ] Web UI 管理界面
- [ ] 實時標記（WebSocket）
- [ ] 機器學習模型優化
- [ ] 支持更多預測市場平台

---

**相關專案：**
- [Polymarket Insights](https://github.com/hon0319/polymarket-insights) - Polymarket 市場分析平台

---

**⭐ 如果這個項目對你有幫助，請給我們一個 Star！**
