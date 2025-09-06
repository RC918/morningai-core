# GitHub 分支保護設置指南

## 🎯 目標
為 `main` 分支設置保護規則，確保代碼質量和部署安全性。

## 🔒 分支保護規則配置

### 1. 基本保護設置

#### 訪問路徑：
```
GitHub Repository → Settings → Branches → Add rule
```

#### 規則配置：
```yaml
Branch name pattern: main

Protect matching branches:
  ✅ Restrict pushes that create files larger than 100 MB
  ✅ Restrict force pushes
  ✅ Restrict deletions

Require a pull request before merging:
  ✅ Require a pull request before merging
  ✅ Require approvals: 1
  ✅ Dismiss stale PR approvals when new commits are pushed
  ✅ Require review from code owners (if CODEOWNERS file exists)

Require status checks to pass before merging:
  ✅ Require status checks to pass before merging
  ✅ Require branches to be up to date before merging
  
  Required status checks:
    - backend (from CI workflow)
    - frontend (from CI workflow, if applicable)
```

### 2. 高級保護設置

#### 管理員設置：
```yaml
Do not allow bypassing the above settings:
  ✅ Include administrators
  
Allow force pushes:
  ❌ Everyone (disabled)
  
Allow deletions:
  ❌ Everyone (disabled)
```

#### 自動化設置：
```yaml
Automatically delete head branches:
  ✅ Automatically delete head branches after PRs are merged
```

## 📋 CI/CD 狀態檢查

### 當前工作流程：
```yaml
Workflow: .github/workflows/ci.yml
Jobs:
  - backend: Python 3.11, pytest, constraints.txt
  - frontend: Node.js (conditional execution)

Triggers:
  - push: main, staging branches
  - pull_request: all branches
```

### 必需的狀態檢查：
1. **backend** - 後端測試必須通過
2. **frontend** - 前端測試（如果有 lock files）

### 可選的狀態檢查：
1. **security-scan** - 安全掃描（可後續添加）
2. **performance-test** - 性能測試（可後續添加）
3. **db-smoke** - 資料庫煙霧測試（如果實施）

## 🔧 實施步驟

### Step 1: 設置基本分支保護
```bash
# 通過 GitHub Web UI 設置
1. 進入 Repository Settings
2. 點擊 Branches
3. 點擊 "Add rule"
4. 輸入 "main" 作為分支名稱模式
5. 啟用上述保護選項
```

### Step 2: 配置狀態檢查
```bash
# 確保 CI 工作流程正常運行
1. 檢查最新的 CI 運行狀態
2. 確認 backend job 成功
3. 在分支保護中添加 "backend" 作為必需檢查
```

### Step 3: 測試保護規則
```bash
# 創建測試 PR 驗證規則
1. 創建新分支: git checkout -b test-branch-protection
2. 做小修改並推送
3. 創建 PR 到 main
4. 驗證 CI 檢查是否阻止合併
5. 等待 CI 通過後合併
```

## 📊 分支保護驗證

### 驗證清單：
- [ ] 無法直接推送到 main 分支
- [ ] PR 需要至少 1 個審核
- [ ] CI 檢查必須通過才能合併
- [ ] 分支必須是最新的才能合併
- [ ] 管理員也受到保護規則約束

### 測試腳本：
```bash
#!/bin/bash
# 測試分支保護規則

echo "Testing branch protection rules..."

# 1. 嘗試直接推送到 main（應該失敗）
git checkout main
echo "test" >> test-protection.txt
git add test-protection.txt
git commit -m "test: direct push to main"
git push origin main
# 預期: 被拒絕

# 2. 通過 PR 流程（應該成功）
git checkout -b test-pr-flow
git push origin test-pr-flow
# 然後在 GitHub UI 創建 PR

echo "Branch protection test completed"
```

## 🚨 緊急情況處理

### 緊急修復流程：
```yaml
Scenario: 生產環境緊急修復
Process:
  1. 創建 hotfix 分支
  2. 實施最小化修復
  3. 快速 CI 驗證
  4. 緊急 PR 審核（可考慮臨時繞過某些規則）
  5. 立即部署
  6. 後續完整測試和文檔更新
```

### 臨時繞過規則：
```yaml
Emergency Override:
  - 僅限管理員
  - 需要明確的業務理由
  - 必須在事後補充完整的測試和審核
  - 記錄在事件報告中
```

## 📈 分支保護指標

### 監控指標：
```yaml
Metrics:
  - PR 合併成功率
  - CI 檢查通過率
  - 平均 PR 審核時間
  - 直接推送嘗試次數（應為 0）
  - 緊急繞過次數
```

### 報告頻率：
```yaml
Daily: CI 檢查狀態
Weekly: PR 流程效率報告
Monthly: 分支保護效果評估
```

## 🔄 持續改進

### 定期檢查：
1. **每月檢查**: 分支保護規則是否適當
2. **季度評估**: CI/CD 流程效率
3. **年度審核**: 整體代碼質量改進

### 規則調整：
```yaml
可能的調整:
  - 增加更多狀態檢查
  - 調整審核人數要求
  - 添加自動化安全掃描
  - 實施代碼覆蓋率要求
```

## 📋 實施檢查清單

### 立即執行（今日）：
- [ ] 設置 main 分支基本保護
- [ ] 配置 CI 狀態檢查要求
- [ ] 測試 PR 流程
- [ ] 驗證保護規則生效

### 後續改進（本週）：
- [ ] 添加 CODEOWNERS 文件
- [ ] 實施自動化安全掃描
- [ ] 設置分支保護監控
- [ ] 創建緊急修復流程文檔

### 長期優化（本月）：
- [ ] 實施代碼覆蓋率檢查
- [ ] 添加性能測試門檻
- [ ] 優化 CI/CD 流程效率
- [ ] 建立分支保護最佳實踐

---
**創建時間**: 2025-09-06 09:40 UTC  
**實施優先級**: P0 - 立即執行  
**負責人**: DevOps Team

