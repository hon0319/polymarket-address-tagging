# Polymarket 地址標籤體系 - 篩選邏輯

## 📊 標籤體系概覽

地址標籤系統分為 **6 個維度，共 50 個標籤**：

### 1. 🎯 交易風格 (Trading Style) - 8 種
- 高勝率
- 大交易量
- 高頻交易
- 穩定盈利
- 小額多單
- 波段交易者
- 長期持有者
- 閃電交易者

### 2. 🏆 專長類別 (Expertise Category) - 10 種
- 政治專家
- 體育專家
- 加密專家
- NFL 專家
- NBA 專家
- 娛樂專家
- 經濟專家
- 選舉專家
- 足球專家
- 全能型

### 3. 📊 策略類型 (Strategy Type) - 12 種
- 掃尾盤
- 逆勢操作
- 順勢操作
- 價值捕手
- 早期進場
- 套利者
- 事件驅動
- 對沖交易者
- 做市商
- 趨勢追蹤者
- 均值回歸者
- 狙擊手

### 4. ⚠️ 風險偏好 (Risk Preference) - 6 種
- 低風險
- 高風險
- 均衡型
- Degen
- 保守型
- 激進型

### 5. 🌟 特殊標記 (Special Tags) - 10 種
- 疑似內線
- 新聞追蹤
- 名人
- 機器人/腳本
- 多帳號操作
- 市場操縱嫌疑
- 專業機構
- 新手
- 休眠喚醒
- 單一市場專注

### 6. 👥 社交影響力 (Social Influence) - 4 種
- KOL
- 社群領袖
- 跟單目標
- 隱形巨鯨

---

## 🔍 篩選邏輯

### 1. 交易風格 (Trading Style)

#### 高勝率
```sql
SELECT address_id 
FROM addresses 
WHERE win_rate >= 0.55
  AND total_trades >= 5
```

#### 大交易量
```sql
SELECT address_id 
FROM addresses 
WHERE avg_trade_size >= 5000
  OR EXISTS (
    SELECT 1 FROM address_trades 
    WHERE address_id = addresses.id 
      AND amount >= 5000
    HAVING COUNT(*) >= 3
  )
```

#### 高頻交易
```sql
SELECT address_id 
FROM address_trades 
WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY address_id 
HAVING COUNT(*) / 30 >= 5
```

#### 穩定盈利
```sql
SELECT address_id 
FROM (
  SELECT 
    address_id,
    DATE_FORMAT(timestamp, '%Y-%m') as month,
    SUM(pnl) as monthly_pnl
  FROM address_trades 
  GROUP BY address_id, month
) monthly_stats
GROUP BY address_id
HAVING SUM(CASE WHEN monthly_pnl > 0 THEN 1 ELSE 0 END) >= 2
  AND COUNT(DISTINCT month) >= 3
```

#### 小額多單
```sql
SELECT address_id 
FROM addresses 
WHERE avg_trade_size < 1000
  AND total_trades >= 20
```

#### 波段交易者
```sql
SELECT 
  a.id as address_id,
  AVG(TIMESTAMPDIFF(DAY, at.timestamp, 
    COALESCE(at.exit_timestamp, m.end_date, NOW())
  )) as avg_holding_days
FROM addresses a
JOIN address_trades at ON a.id = at.address_id
LEFT JOIN markets m ON at.market_id = m.id
GROUP BY a.id
HAVING avg_holding_days BETWEEN 7 AND 30
  AND COUNT(*) >= 5
```

#### 長期持有者
```sql
SELECT 
  a.id as address_id,
  AVG(TIMESTAMPDIFF(DAY, at.timestamp, 
    COALESCE(at.exit_timestamp, m.end_date, NOW())
  )) as avg_holding_days
FROM addresses a
JOIN address_trades at ON a.id = at.address_id
LEFT JOIN markets m ON at.market_id = m.id
GROUP BY a.id
HAVING avg_holding_days > 30
  AND COUNT(CASE WHEN at.exit_timestamp IS NULL THEN 1 END) * 1.0 / COUNT(*) >= 0.50
  AND COUNT(*) >= 5
```

#### 閃電交易者
```sql
SELECT 
  a.id as address_id,
  AVG(TIMESTAMPDIFF(HOUR, at.timestamp, at.exit_timestamp)) as avg_holding_hours
FROM addresses a
JOIN address_trades at ON a.id = at.address_id
WHERE at.exit_timestamp IS NOT NULL
GROUP BY a.id
HAVING avg_holding_hours < 24
  AND COUNT(*) >= 10
```

---

### 2. 專長類別 (Expertise Category)

#### 政治專家
```sql
SELECT 
  a.id as address_id,
  COUNT(CASE WHEN m.category = 'Politics' THEN 1 END) * 1.0 / COUNT(*) as politics_ratio
FROM addresses a
JOIN address_trades at ON a.id = at.address_id
JOIN markets m ON at.market_id = m.id
GROUP BY a.id
HAVING politics_ratio >= 0.50
  AND COUNT(CASE WHEN m.category = 'Politics' THEN 1 END) >= 5
```

#### 體育專家
```sql
SELECT 
  a.id as address_id,
  COUNT(CASE WHEN m.category = 'Sports' THEN 1 END) * 1.0 / COUNT(*) as sports_ratio
FROM addresses a
JOIN address_trades at ON a.id = at.address_id
JOIN markets m ON at.market_id = m.id
GROUP BY a.id
HAVING sports_ratio >= 0.50
  AND COUNT(CASE WHEN m.category = 'Sports' THEN 1 END) >= 5
```

#### 加密專家
```sql
SELECT 
  a.id as address_id,
  COUNT(CASE WHEN m.category = 'Crypto' THEN 1 END) * 1.0 / COUNT(*) as crypto_ratio
FROM addresses a
JOIN address_trades at ON a.id = at.address_id
JOIN markets m ON at.market_id = m.id
GROUP BY a.id
HAVING crypto_ratio >= 0.50
  AND COUNT(CASE WHEN m.category = 'Crypto' THEN 1 END) >= 5
```

#### 娛樂專家
```sql
SELECT 
  a.id as address_id,
  COUNT(CASE WHEN m.category = 'Entertainment' THEN 1 END) * 1.0 / COUNT(*) as entertainment_ratio
FROM addresses a
JOIN address_trades at ON a.id = at.address_id
JOIN markets m ON at.market_id = m.id
GROUP BY a.id
HAVING entertainment_ratio >= 0.50
  AND COUNT(CASE WHEN m.category = 'Entertainment' THEN 1 END) >= 5
```

#### 經濟專家
```sql
SELECT 
  a.id as address_id,
  COUNT(CASE WHEN m.category = 'Economics' THEN 1 END) * 1.0 / COUNT(*) as economics_ratio
FROM addresses a
JOIN address_trades at ON a.id = at.address_id
JOIN markets m ON at.market_id = m.id
GROUP BY a.id
HAVING economics_ratio >= 0.50
  AND COUNT(CASE WHEN m.category = 'Economics' THEN 1 END) >= 5
```

#### 選舉專家
```sql
SELECT 
  a.id as address_id,
  COUNT(CASE WHEN m.title LIKE '%election%' OR m.title LIKE '%選舉%' THEN 1 END) * 1.0 / COUNT(*) as election_ratio
FROM addresses a
JOIN address_trades at ON a.id = at.address_id
JOIN markets m ON at.market_id = m.id
WHERE m.category = 'Politics'
GROUP BY a.id
HAVING election_ratio >= 0.50
  AND COUNT(CASE WHEN m.title LIKE '%election%' OR m.title LIKE '%選舉%' THEN 1 END) >= 5
```

#### NFL 專家
```sql
SELECT 
  a.id as address_id,
  COUNT(CASE WHEN m.title LIKE '%NFL%' THEN 1 END) * 1.0 / COUNT(*) as nfl_ratio
FROM addresses a
JOIN address_trades at ON a.id = at.address_id
JOIN markets m ON at.market_id = m.id
WHERE m.category = 'Sports'
GROUP BY a.id
HAVING nfl_ratio >= 0.50
  AND COUNT(CASE WHEN m.title LIKE '%NFL%' THEN 1 END) >= 5
```

#### NBA 專家
```sql
SELECT 
  a.id as address_id,
  COUNT(CASE WHEN m.title LIKE '%NBA%' THEN 1 END) * 1.0 / COUNT(*) as nba_ratio
FROM addresses a
JOIN address_trades at ON a.id = at.address_id
JOIN markets m ON at.market_id = m.id
WHERE m.category = 'Sports'
GROUP BY a.id
HAVING nba_ratio >= 0.50
  AND COUNT(CASE WHEN m.title LIKE '%NBA%' THEN 1 END) >= 5
```

#### 足球專家
```sql
SELECT 
  a.id as address_id,
  COUNT(CASE WHEN m.title LIKE '%football%' OR m.title LIKE '%soccer%' OR m.title LIKE '%足球%' THEN 1 END) * 1.0 / COUNT(*) as football_ratio
FROM addresses a
JOIN address_trades at ON a.id = at.address_id
JOIN markets m ON at.market_id = m.id
WHERE m.category = 'Sports'
GROUP BY a.id
HAVING football_ratio >= 0.50
  AND COUNT(CASE WHEN m.title LIKE '%football%' OR m.title LIKE '%soccer%' OR m.title LIKE '%足球%' THEN 1 END) >= 5
```

#### 全能型
```sql
SELECT 
  a.id as address_id,
  MAX(category_ratio) as max_category_ratio,
  COUNT(DISTINCT m.category) as category_count
FROM (
  SELECT 
    a.id as address_id,
    m.category,
    COUNT(*) * 1.0 / (SELECT COUNT(*) FROM address_trades WHERE address_id = a.id) as category_ratio
  FROM addresses a
  JOIN address_trades at ON a.id = at.address_id
  JOIN markets m ON at.market_id = m.id
  GROUP BY a.id, m.category
) category_stats
JOIN addresses a ON category_stats.address_id = a.id
JOIN address_trades at ON a.id = at.address_id
JOIN markets m ON at.market_id = m.id
GROUP BY a.id
HAVING max_category_ratio < 0.40
  AND category_count >= 3
  AND (SELECT COUNT(*) FROM address_trades WHERE address_id = a.id) >= 15
```

---

### 3. 策略類型 (Strategy Type)

#### 掃尾盤
```sql
SELECT 
  a.id as address_id,
  COUNT(CASE 
    WHEN TIMESTAMPDIFF(DAY, at.timestamp, m.end_date) <= 3
    THEN 1 
  END) * 1.0 / COUNT(*) as late_entry_ratio
FROM addresses a
JOIN address_trades at ON a.id = at.address_id
JOIN markets m ON at.market_id = m.id
WHERE m.end_date IS NOT NULL
GROUP BY a.id
HAVING late_entry_ratio >= 0.50
  AND COUNT(*) >= 5
```

#### 逆勢操作
```sql
-- 需要價格歷史數據
SELECT 
  a.id as address_id,
  COUNT(CASE 
    WHEN (at.side = 'YES' AND at.price < 0.40) 
      OR (at.side = 'NO' AND at.price > 0.60)
    THEN 1 
  END) * 1.0 / COUNT(*) as contrarian_ratio
FROM addresses a
JOIN address_trades at ON a.id = at.address_id
GROUP BY a.id
HAVING contrarian_ratio >= 0.60
  AND COUNT(*) >= 10
```

#### 順勢操作
```sql
-- 需要價格歷史數據
SELECT 
  a.id as address_id,
  COUNT(CASE 
    WHEN (at.side = 'YES' AND at.price > 0.60) 
      OR (at.side = 'NO' AND at.price < 0.40)
    THEN 1 
  END) * 1.0 / COUNT(*) as momentum_ratio
FROM addresses a
JOIN address_trades at ON a.id = at.address_id
GROUP BY a.id
HAVING momentum_ratio >= 0.60
  AND COUNT(*) >= 10
```

#### 價值捕手
```sql
-- 需要價格歷史數據
SELECT 
  a.id as address_id,
  AVG(ABS(at.price - 0.50)) as avg_price_deviation
FROM addresses a
JOIN address_trades at ON a.id = at.address_id
GROUP BY a.id
HAVING avg_price_deviation >= 0.20
  AND COUNT(*) >= 10
```

#### 早期進場
```sql
SELECT 
  a.id as address_id,
  COUNT(CASE 
    WHEN TIMESTAMPDIFF(HOUR, m.created_at, at.timestamp) <= 48
    THEN 1 
  END) * 1.0 / COUNT(*) as early_entry_ratio
FROM addresses a
JOIN address_trades at ON a.id = at.address_id
JOIN markets m ON at.market_id = m.id
WHERE m.created_at IS NOT NULL
GROUP BY a.id
HAVING early_entry_ratio >= 0.50
  AND COUNT(*) >= 5
```

#### 套利者
```sql
SELECT 
  a.id as address_id,
  COUNT(DISTINCT at.market_id) as markets_count,
  COUNT(*) as total_trades
FROM addresses a
JOIN address_trades at ON a.id = at.address_id
GROUP BY a.id
HAVING markets_count >= 10
  AND total_trades >= 20
  AND total_trades * 1.0 / markets_count >= 1.5
```

#### 事件驅動
```sql
-- 需要新聞 API 數據
-- 檢測交易時間與重大新聞發布的相關性
```

#### 對沖交易者
```sql
SELECT 
  a.id as address_id,
  COUNT(DISTINCT at1.market_id) as hedged_markets
FROM addresses a
JOIN address_trades at1 ON a.id = at1.address_id AND at1.side = 'YES'
JOIN address_trades at2 ON a.id = at2.address_id AND at2.side = 'NO'
  AND at1.market_id = at2.market_id
  AND ABS(TIMESTAMPDIFF(DAY, at1.timestamp, at2.timestamp)) <= 7
GROUP BY a.id
HAVING hedged_markets >= 3
```

#### 做市商
```sql
SELECT 
  a.id as address_id,
  COUNT(*) as total_trades,
  COUNT(DISTINCT at.market_id) as markets_count,
  AVG(TIMESTAMPDIFF(MINUTE, at.timestamp, at.exit_timestamp)) as avg_holding_minutes
FROM addresses a
JOIN address_trades at ON a.id = at.address_id
WHERE at.exit_timestamp IS NOT NULL
GROUP BY a.id
HAVING total_trades >= 50
  AND markets_count >= 10
  AND avg_holding_minutes < 120
```

#### 趨勢追蹤者
```sql
-- 需要價格歷史數據
-- 檢測是否在價格上升/下降趨勢中進場
```

#### 均值回歸者
```sql
-- 需要價格歷史數據
-- 檢測是否在價格偏離歷史均值時進場
```

#### 狙擊手
```sql
SELECT 
  a.id as address_id,
  a.total_trades,
  a.win_rate,
  AVG(at.amount) as avg_trade_size
FROM addresses a
JOIN address_trades at ON a.id = at.address_id
GROUP BY a.id
HAVING a.total_trades <= 20
  AND a.win_rate >= 0.70
  AND avg_trade_size >= 3000
```

---

### 4. 風險偏好 (Risk Preference)

#### 低風險
```sql
SELECT 
  a.id as address_id,
  COUNT(CASE 
    WHEN at.price >= 0.75 OR at.price <= 0.25
    THEN 1 
  END) * 1.0 / COUNT(*) as low_risk_ratio
FROM addresses a
JOIN address_trades at ON a.id = at.address_id
GROUP BY a.id
HAVING low_risk_ratio >= 0.60
  AND COUNT(*) >= 5
```

#### 高風險
```sql
SELECT 
  a.id as address_id,
  COUNT(CASE 
    WHEN at.price BETWEEN 0.35 AND 0.65
    THEN 1 
  END) * 1.0 / COUNT(*) as high_risk_ratio
FROM addresses a
JOIN address_trades at ON a.id = at.address_id
GROUP BY a.id
HAVING high_risk_ratio >= 0.60
  AND COUNT(*) >= 5
```

#### 均衡型
```sql
SELECT 
  a.id as address_id,
  STDDEV(at.price) as price_stddev
FROM addresses a
JOIN address_trades at ON a.id = at.address_id
GROUP BY a.id
HAVING price_stddev BETWEEN 0.15 AND 0.25
  AND COUNT(*) >= 10
```

#### Degen
```sql
SELECT 
  a.id as address_id,
  AVG(at.amount) as avg_trade_size,
  COUNT(CASE WHEN at.price BETWEEN 0.4 AND 0.6 THEN 1 END) * 1.0 / COUNT(*) as extreme_risk_ratio
FROM addresses a
JOIN address_trades at ON a.id = at.address_id
GROUP BY a.id
HAVING extreme_risk_ratio >= 0.70
  AND avg_trade_size >= 2000
  AND COUNT(*) >= 10
```

#### 保守型
```sql
SELECT 
  a.id as address_id,
  AVG(TIMESTAMPDIFF(DAY, at.timestamp, m.end_date)) as avg_days_before_close
FROM addresses a
JOIN address_trades at ON a.id = at.address_id
JOIN markets m ON at.market_id = m.id
WHERE m.end_date IS NOT NULL
GROUP BY a.id
HAVING avg_days_before_close <= 14
  AND COUNT(*) >= 5
```

#### 激進型
```sql
SELECT 
  a.id as address_id,
  AVG(TIMESTAMPDIFF(DAY, at.timestamp, m.end_date)) as avg_days_before_close
FROM addresses a
JOIN address_trades at ON a.id = at.address_id
JOIN markets m ON at.market_id = m.id
WHERE m.end_date IS NOT NULL
GROUP BY a.id
HAVING avg_days_before_close >= 60
  AND COUNT(*) >= 5
```

---

### 5. 特殊標記 (Special Tags)

#### 疑似內線
```sql
SELECT 
  a.id as address_id,
  a.suspicion_score,
  a.win_rate,
  AVG(TIMESTAMPDIFF(HOUR, m.created_at, at.timestamp)) as avg_hours_after_creation
FROM addresses a
JOIN address_trades at ON a.id = at.address_id
JOIN markets m ON at.market_id = m.id
WHERE m.created_at IS NOT NULL
GROUP BY a.id
HAVING a.suspicion_score >= 0.70
  AND a.win_rate >= 0.65
  AND avg_hours_after_creation <= 24
  AND COUNT(*) >= 5
```

#### 新聞追蹤
```sql
-- 需要新聞 API 數據
-- 檢測交易時間與新聞發布的時間相關性
```

#### 名人
```sql
-- 手動維護的名人地址列表
SELECT address_id 
FROM known_celebrities
WHERE verified = TRUE
```

#### 機器人/腳本
```sql
SELECT 
  a.id as address_id,
  COUNT(CASE 
    WHEN MINUTE(at.timestamp) IN (0, 15, 30, 45)
    THEN 1 
  END) * 1.0 / COUNT(*) as regular_timing_ratio
FROM addresses a
JOIN address_trades at ON a.id = at.address_id
GROUP BY a.id
HAVING regular_timing_ratio >= 0.60
  AND COUNT(*) >= 15
```

#### 多帳號操作
```sql
SELECT 
  a1.id as address_id,
  COUNT(DISTINCT a2.id) as correlated_addresses
FROM addresses a1
JOIN address_trades at1 ON a1.id = at1.address_id
JOIN address_trades at2 ON at1.market_id = at2.market_id
  AND at1.side = at2.side
  AND ABS(TIMESTAMPDIFF(MINUTE, at1.timestamp, at2.timestamp)) <= 10
  AND at1.address_id != at2.address_id
JOIN addresses a2 ON at2.address_id = a2.id
GROUP BY a1.id
HAVING correlated_addresses >= 2
  AND COUNT(*) >= 10
```

#### 市場操縱嫌疑
```sql
SELECT 
  a.id as address_id,
  COUNT(CASE 
    WHEN at.amount >= 5000
      AND EXISTS (
        SELECT 1 FROM address_trades at2
        WHERE at2.address_id = a.id
          AND at2.market_id = at.market_id
          AND at2.side != at.side
          AND at2.timestamp > at.timestamp
          AND TIMESTAMPDIFF(HOUR, at.timestamp, at2.timestamp) <= 48
      )
    THEN 1 
  END) as pump_dump_count
FROM addresses a
JOIN address_trades at ON a.id = at.address_id
GROUP BY a.id
HAVING pump_dump_count >= 2
```

#### 專業機構
```sql
SELECT 
  a.id as address_id,
  a.total_volume,
  a.win_rate,
  a.total_trades
FROM addresses a
WHERE a.total_volume >= 500000
  AND a.win_rate >= 0.65
  AND a.total_trades >= 50
```

#### 新手
```sql
SELECT 
  a.id as address_id,
  a.created_at,
  a.total_trades
FROM addresses a
WHERE TIMESTAMPDIFF(DAY, a.created_at, NOW()) < 60
  AND a.total_trades < 15
```

#### 休眠喚醒
```sql
SELECT 
  a.id as address_id,
  MAX(at.timestamp) as last_trade_time,
  COUNT(CASE WHEN at.timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 END) as recent_trades
FROM addresses a
JOIN address_trades at ON a.id = at.address_id
GROUP BY a.id
HAVING TIMESTAMPDIFF(DAY, 
  (SELECT MAX(timestamp) FROM address_trades WHERE address_id = a.id AND timestamp < DATE_SUB(NOW(), INTERVAL 7 DAY)),
  (SELECT MIN(timestamp) FROM address_trades WHERE address_id = a.id AND timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY))
) >= 60
  AND recent_trades >= 5
```

#### 單一市場專注
```sql
SELECT 
  a.id as address_id,
  MAX(market_trade_count) * 1.0 / SUM(market_trade_count) as max_market_ratio
FROM (
  SELECT 
    a.id as address_id,
    at.market_id,
    COUNT(*) as market_trade_count
  FROM addresses a
  JOIN address_trades at ON a.id = at.address_id
  GROUP BY a.id, at.market_id
) market_stats
GROUP BY address_id
HAVING max_market_ratio >= 0.70
  AND SUM(market_trade_count) >= 10
```

---

### 6. 社交影響力 (Social Influence)

#### KOL
```sql
-- 手動維護或通過 API 整合
SELECT address_id 
FROM known_kols
WHERE verified = TRUE
  AND platform IN ('Twitter', 'Discord')
```

#### 社群領袖
```sql
SELECT 
  a.id as address_id,
  a.total_volume,
  a.win_rate,
  a.total_trades
FROM addresses a
WHERE a.total_volume >= 300000
  AND a.win_rate >= 0.60
  AND a.total_trades >= 100
```

#### 跟單目標
```sql
SELECT 
  a1.id as address_id,
  COUNT(DISTINCT a2.id) as follower_count
FROM addresses a1
JOIN address_trades at1 ON a1.id = at1.address_id
JOIN address_trades at2 ON at1.market_id = at2.market_id
  AND at1.side = at2.side
  AND at2.timestamp > at1.timestamp
  AND TIMESTAMPDIFF(MINUTE, at1.timestamp, at2.timestamp) <= 60
  AND at1.address_id != at2.address_id
JOIN addresses a2 ON at2.address_id = a2.id
GROUP BY a1.id
HAVING follower_count >= 5
  AND COUNT(*) >= 10
```

#### 隱形巨鯨
```sql
SELECT 
  a.id as address_id,
  a.total_volume
FROM addresses a
LEFT JOIN known_kols k ON a.id = k.address_id
WHERE a.total_volume >= 500000
  AND k.address_id IS NULL
  AND NOT EXISTS (
    SELECT 1 FROM known_celebrities WHERE address_id = a.id
  )
```

---

## 📊 實作階段建議

### 第一階段（立即可實作）- 19 種標籤
使用現有數據，無需外部 API：

**交易風格（5 種）：**
- 高勝率、大交易量、高頻交易、穩定盈利、小額多單

**專長類別（10 種）：**
- 政治專家、體育專家、加密專家、NFL 專家、NBA 專家、娛樂專家、經濟專家、選舉專家、足球專家、全能型

**風險偏好（2 種）：**
- 低風險、高風險

**策略類型（2 種）：**
- 掃尾盤、早期進場

### 第二階段（需要持倉數據）- 15 種標籤
需要 `exit_timestamp` 或市場結算數據：

**交易風格（3 種）：**
- 波段交易者、長期持有者、閃電交易者

**風險偏好（2 種）：**
- 保守型、激進型

**策略類型（3 種）：**
- 對沖交易者、做市商、狙擊手

**其他（7 種）：**
- 均衡型、逆勢操作、順勢操作、價值捕手、套利者、專業機構、單一市場專注

### 第三階段（需要外部數據）- 16 種標籤
需要價格歷史、新聞 API 或社交媒體 API：

**策略類型（3 種）：**
- 事件驅動、趨勢追蹤者、均值回歸者

**特殊標記（9 種）：**
- 疑似內線、新聞追蹤、名人、機器人/腳本、多帳號操作、市場操縱嫌疑、新手、休眠喚醒

**社交影響力（4 種）：**
- KOL、社群領袖、跟單目標、隱形巨鯨

---

## 📋 數據庫 Schema 建議

### address_tags 表
```sql
CREATE TABLE address_tags (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  address_id BIGINT NOT NULL,
  category VARCHAR(50) NOT NULL,  -- 交易風格、專長類別、策略類型等
  tag_name VARCHAR(50) NOT NULL,  -- 具體標籤名稱
  confidence_score DECIMAL(3,2) DEFAULT 1.00,  -- 信心分數 0-1
  is_manual BOOLEAN DEFAULT FALSE,  -- 是否手動標記
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_address_tag (address_id, tag_name),
  INDEX idx_address (address_id),
  INDEX idx_tag (tag_name),
  INDEX idx_category (category)
);
```

### tag_definitions 表（可選）
```sql
CREATE TABLE tag_definitions (
  id INT PRIMARY KEY AUTO_INCREMENT,
  category VARCHAR(50) NOT NULL,
  tag_name VARCHAR(50) NOT NULL,
  description TEXT,
  sql_logic TEXT,  -- 篩選邏輯的 SQL
  phase INT DEFAULT 1,  -- 實作階段 1/2/3
  is_active BOOLEAN DEFAULT TRUE,
  UNIQUE KEY uk_tag (category, tag_name)
);
```

---

✅ **文檔完成** - 包含所有 50 個標籤的完整篩選邏輯
