# 快速開始指南

這份指南幫助你在 5 分鐘內開始使用地址標籤服務。

## 📦 步驟 1：安裝依賴

```bash
pip install -r requirements.txt
```

## ⚙️ 步驟 2：配置數據庫

編輯 `config.json`，修改數據庫連接字符串：

```json
{
  "database": {
    "url": "mysql://user:password@host:port/database"
  }
}
```

**示例：**
```json
{
  "database": {
    "url": "mysql://root:mypassword@localhost:3306/polymarket"
  }
}
```

## 🚀 步驟 3：運行服務

### 測試模式（推薦首次運行）

先處理 10 個地址測試：

```bash
python address_tagging_service.py --init --limit 10
```

### 正式運行

為所有地址打標籤：

```bash
python address_tagging_service.py --init
```

## 📊 步驟 4：查看結果

生成統計報告：

```bash
python address_tagging_service.py --report
```

## 🎯 常用命令

```bash
# 為單個地址打標籤
python address_tagging_service.py --address 12345

# 更新最近活躍地址的標籤
python address_tagging_service.py --update

# 導出標籤為 JSON
python address_tagging_service.py --export-json tags.json

# 導出標籤為 CSV
python address_tagging_service.py --export-csv tags.csv
```

## ⚠️ 常見問題

### 問題 1：數據庫連接失敗

**錯誤信息：**
```
Error: Can't connect to MySQL server
```

**解決方案：**
1. 檢查數據庫連接字符串是否正確
2. 確認數據庫服務是否運行
3. 確認防火牆是否允許連接

### 問題 2：表名或欄位名不匹配

**錯誤信息：**
```
Error: Table 'addresses' doesn't exist
```

**解決方案：**
在 `config.json` 中映射你的表名：

```json
{
  "database": {
    "tables": {
      "addresses": "your_table_name",
      "address_trades": "your_trades_table",
      "markets": "your_markets_table"
    }
  }
}
```

### 問題 3：沒有標籤生成

**可能原因：**
- 地址的交易數據不足
- 閾值設置過高

**解決方案：**
降低閾值，例如：

```json
{
  "tags": {
    "交易風格": {
      "高勝率": {
        "win_rate_threshold": 0.50,  // 從 0.55 降低到 0.50
        "min_trades": 3               // 從 5 降低到 3
      }
    }
  }
}
```

## 📝 下一步

- 閱讀 [README.md](README.md) 了解完整功能
- 閱讀 [ADDRESS_TAGGING_SYSTEM.md](../ADDRESS_TAGGING_SYSTEM.md) 了解標籤體系
- 閱讀 [AUTO_TAGGING_PORTABILITY_GUIDE.md](../AUTO_TAGGING_PORTABILITY_GUIDE.md) 了解可移植性設計

## 🤝 需要幫助？

如有問題，請查看：
1. 日誌文件：`address_tagging.log`
2. 完整文檔：`README.md`
3. 配置說明：`config.json` 中的註釋
