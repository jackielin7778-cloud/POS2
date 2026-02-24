# POS 連鎖店系統 v2.0

連鎖門市 Point of Sale 系統，支援電子發票開立（MIG 4.1 F0401）。

## 功能

- 🏪 門市管理（總部 + 分店）
- 📦 商品管理
- 💳 銷售 POS
- 🧾 電子發票（MIG 4.1 F0401）
- 👤 會員管理（跨店積分）
- 🏷️ 促銷系統
- 📊 庫存管理（調拨）
- 👥 權限管理

## 安裝

```bash
# 克隆專案
git clone https://github.com/your-repo/pos-system-v2.git
cd pos-system-v2

# 建立虛擬環境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt
```

## 本地執行

### Flask Web 版
```bash
python app.py
```

### Streamlit 版
```bash
streamlit run app_streamlit.py
```

## 部署到 Streamlit Cloud

1. 將程式碼推送到 GitHub
2. 前往 [Streamlit Cloud](https://streamlit.io/cloud)
3. 連結 GitHub 帳號
4. 選擇 repository 和 branch
5. 設定 `app_streamlit.py` 為主程式
6. 點擊 Deploy

## 資料庫

使用 SQLite，自動建立於 `pos_chain.db`

## 電子發票

符合財政部 MIG 4.1 F0401 規格
- 三表結構：Main / Details / Amount
- 支援載具、捐贈、保稅區

## License

MIT
