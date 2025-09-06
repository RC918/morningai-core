# 🔧 Render Build Command 修改指南

**目標**: 解決 externally-managed-environment 部署錯誤  
**方法**: 添加 `--break-system-packages` 參數到 Build Command

---

## 📱 詳細操作步驟

### 步驟1: 訪問Render Dashboard
1. 打開瀏覽器
2. 訪問 https://dashboard.render.com
3. 使用您的帳戶登入
4. 在服務列表中找到 `morningai-core` 服務
5. 點擊服務名稱進入

### 步驟2: 進入設定頁面
1. 在服務頁面頂部，找到並點擊 **"Settings"** 標籤
2. 頁面會顯示服務的各種設定選項
3. 向下滾動找到 **"Build & Deploy"** 部分

### 步驟3: 修改Build Command
**當前的Build Command**:
```bash
python3.11 --version && python3.11 -m pip install -r requirements.txt
```

**修改為**:
```bash
python3.11 --version && python3.11 -m pip install --break-system-packages -r requirements.txt
```

**具體操作**:
1. 找到 **"Build Command"** 欄位
2. 點擊欄位進入編輯模式
3. 在 `pip install` 和 `-r requirements.txt` 之間添加 `--break-system-packages`
4. 確認修改正確
5. 點擊 **"Save Changes"** 按鈕

### 步驟4: 觸發重新部署
1. 點擊頁面頂部的 **"Deploys"** 標籤
2. 點擊右上角的 **"Manual Deploy"** 按鈕
3. 在下拉選單中選擇 **"Clear build cache & deploy"**
4. 確認開始部署

---

## 🔍 驗證步驟

### 部署過程監控
1. 部署開始後，可以在 "Deploys" 頁面看到進度
2. 點擊正在進行的部署可以查看即時日誌
3. 注意觀察是否出現 Python 版本信息和依賴安裝過程

### 成功指標
- ✅ 部署狀態顯示 "Live" (綠色)
- ✅ 日誌中顯示 "Python 3.11.x"
- ✅ 依賴安裝無錯誤信息
- ✅ 服務啟動成功

### 失敗指標
- ❌ 部署狀態顯示 "Failed" (紅色)
- ❌ 日誌中出現 "externally-managed-environment" 錯誤
- ❌ 依賴安裝失敗

---

## 🚨 如果仍然失敗

### 備用方案1: 使用系統默認Python
將Build Command修改為:
```bash
pip install -r requirements.txt
```

### 備用方案2: 使用最小化依賴
1. 將 `requirements.txt` 替換為 `requirements_minimal.txt`
2. Build Command:
```bash
python3.11 --version && python3.11 -m pip install --break-system-packages -r requirements_minimal.txt
```

---

## 📞 需要協助時

如果遇到任何問題，請提供：
1. 修改後的Build Command截圖
2. 部署失敗的錯誤日誌
3. 當前的部署狀態截圖

我將根據具體情況提供進一步的解決方案。

---

**預期完成時間**: 5-10分鐘  
**下一步**: 部署成功後進行E段驗收測試

