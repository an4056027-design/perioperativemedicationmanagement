import streamlit as st
import pandas as pd

# 1. 頁面基礎配置
st.set_page_config(
    page_title="術前停藥建議查詢平台",
    page_icon="💊",
    layout="wide"
)

# 2. 連線至 Google Sheets CSV (無須 API Key)
# 替換為你的 Google Sheet 發布 CSV 網址
GSHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRSdCCbnf2lbqXvwX3x8Db6myDrz-6ewc2p3K_7ulhvcnur3saxxho_9VCEa6uVko9DRC6L5kKUMr8O/pub?output=csv"

@st.cache_data(ttl=60) # 每 60 秒自動更新一次資料
def fetch_data(url):
    try:
        data = pd.read_csv(url)
        # 資料清洗：轉換需要布林值的欄位
        data['need_stop'] = data['need_stop'].astype(str).str.upper() == 'TRUE'
        data['bridging_needed'] = data['bridging_needed'].astype(str).str.upper() == 'TRUE'
        return data
    except Exception as e:
        st.error(f"連線至 Google Sheets 失敗，請確認發布網址是否正確。錯誤訊息: {e}")
        return pd.DataFrame()

df = fetch_data(GSHEET_CSV_URL)

# 3. 醫學安全免責聲明 Banner
st.warning("⚠️ **臨床決策支援聲明**：本平台建議僅供醫療人員參考，實際處置請依患者個別狀況（如腎功能、凝血功能）及主治醫師專業判斷為準。")

st.title("🏥 術前停藥與恢復時程查詢平台")

if not df.empty:
    # 4. 搜尋與選單控制區
    col1, col2 = st.columns(2)
    
    with col1:
        # 混合學名與商品名做搜尋選單
        df['drug_label'] = df['generic_name'] + " (" + df['trade_name'] + ")"
        drug_options = df['drug_label'].unique()
        selected_drug_label = st.selectbox("1. 選擇或輸入藥物 (學名/商品名)", drug_options)
        
    with col2:
        surgery_options = df['surgery_risk'].unique()
        selected_surgery = st.selectbox("2. 選擇手術/術式出血風險等級", surgery_options)

    is_emergency = st.toggle("🚨 當前處置為「急診手術 (Emergency Surgery)」", value=False)

    # 5. 邏輯比對
    matched_rule = df[
        (df['drug_label'] == selected_drug_label) & 
        (df['surgery_risk'] == selected_surgery)
    ]

    if not matched_rule.empty:
        row = matched_rule.iloc[0]
        st.divider()

        # 結果 Header
        res_col1, res_col2 = st.columns([3, 1])
        with res_col1:
            st.subheader(f"💊 {row['generic_name']} ({row['trade_name']}) — {row['category']}")
        with res_col2:
            if row['need_stop']:
                st.error("🛑 建議術前停藥", icon="🚨")
            else:
                st.success("🟢 不需停藥 (繼續使用)", icon="✅")

        # 停藥時程卡片
        if row['need_stop']:
            st.markdown("### ⏳ 圍手術期時程建議")
            m1, m2, m3 = st.columns(3)
            m1.metric("術前提前停藥", f"{row['stop_days']} 天")
            m2.metric("手術當天 (Day 0)", "停止使用")
            m3.metric("術後恢復時機", f"第 {row['resume_days']} 天重新評估")

        # 橋接治療提醒
        if row['bridging_needed']:
            st.info(f"💉 **橋接治療建議 (Bridging Therapy)**：{row['bridging_notes']}")

        # 急診模式 Protocol
        if is_emergency:
            st.error(f"🚨 **急診例外處置 Protocol**：{row['emergency_protocol']}")

        # 臨床注意事項與出處
        with st.expander("📋 臨床注意事項與實證指引出處", expanded=True):
            st.write(f"**臨床評估要點**：{row['clinical_notes']}")
            st.caption(f"實證參考來源：{row['reference']}")
    else:
        st.info("尚無該「藥物 x 術式」組合的對照規則，請諮詢專科醫師或藥師。")
