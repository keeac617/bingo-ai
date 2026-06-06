import streamlit as st
import pandas as pd
import random
import requests
from bs4 import BeautifulSoup
from collections import Counter
import time
import re
import streamlit.components.v1 as components
import itertools
import os
from datetime import datetime, timezone, timedelta

# --- 網頁基本設定 ---
st.set_page_config(page_title="HLF賓果AI分析系統", layout="wide")

# --- 攔截手動更新的網址參數 ---
# 當使用者點擊 iframe 裡的手動更新時，會帶有 refresh=1 的參數
if st.query_params.get("refresh") == "1":
    st.cache_data.clear()
    del st.query_params["refresh"]

if "ai_predicted" not in st.session_state:
    st.session_state.ai_predicted = []
if "ai_star_num" not in st.session_state:
    st.session_state.ai_star_num = 0

# --- 質感深色主題、手機自適應與卡片 CSS ---
st.markdown("""
<style>
    .stApp { background-color: #0a0e17 !important; }
    body, p, span, div, li, h2, h3, h4, h5, h6, label { color: #e2e8f0 !important; }
    
    /* 1. 標題自適應：精準動態縮放，保證單行且夠大 */
    h1 {
        font-size: min(7vw, 2.5rem) !important;
        white-space: nowrap !important;
        color: #e2e8f0 !important;
        letter-spacing: -0.5px;
        padding-bottom: 0px !important;
        margin-bottom: 5px !important;
    }

    /* 2. 統計頁籤間隔拉大，防誤觸 */
    div[data-baseweb="tab-list"] {
        flex-wrap: wrap !important;
        gap: 12px !important;
        justify-content: flex-start;
    }
    div[data-baseweb="tab"] {
        padding: 10px 15px !important;
        margin-bottom: 8px !important;
        background-color: #1f2937 !important;
        border: 1px solid #374151 !important;
        border-radius: 6px;
    }

    /* 下拉選單修復 */
    div[data-baseweb="select"] > div { background-color: #2d3748 !important; border-color: #4a5568 !important; }
    div[data-baseweb="select"] span { color: #ffffff !important; font-weight: bold; }
    div[data-baseweb="popover"] > div, ul[role="listbox"], li[role="option"] { background-color: #2d3748 !important; color: #ffffff !important; }
    li[role="option"]:hover { background-color: #4a5568 !important; }

    /* 儀表板卡片 */
    div[data-testid="metric-container"] {
        background-color: #111827 !important; border: 1px solid #1f2937 !important;
        border-top: 3px solid #3b82f6 !important; padding: 15px; border-radius: 8px; text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    div[data-testid="metric-container"] div { color: #60a5fa !important; }

    /* AI 按鈕樣式 */
    div.stButton > button {
        background: linear-gradient(180deg, #1e3a8a 0%, #1e40af 100%) !important;
        color: #ffffff !important; font-weight: bold !important; border: 1px solid #3b82f6 !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.5); transition: all 0.3s ease;
    }
    div.stButton > button:hover { background: linear-gradient(180deg, #2563eb 0%, #1d4ed8 100%) !important; border: 1px solid #60a5fa !important; transform: translateY(-2px); }

    /* 玩法與獎金表格 */
    .table-responsive { width: 100%; overflow-x: auto; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    .jyb-table { width: 100%; border-collapse: collapse; background-color: #111827; color: #e2e8f0; font-size: 14px; text-align: center; }
    .jyb-table th { background-color: #1f2937; color: #60a5fa; padding: 10px; border: 1px solid #374151; font-weight: bold; }
    .jyb-table td { padding: 8px; border: 1px solid #374151; }
    @media (max-width: 768px) { .jyb-table { font-size: 12px; } .jyb-table th, .jyb-table td { padding: 5px; } }

    /* 歷史紀錄專屬卡片 (完美解決左右滑動問題) */
    .history-card {
        background-color: #111827; border: 1px solid #374151; border-radius: 8px;
        padding: 12px; margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    .history-header {
        display: flex; justify-content: space-between; align-items: center;
        border-bottom: 1px solid #1f2937; padding-bottom: 8px; margin-bottom: 10px; font-size: 14px;
    }
    .history-period { font-weight: bold; color: #60a5fa; font-size: 16px; }
    .history-stats { color: #9ca3af; font-size: 13px; }
    .history-balls { display: flex; flex-wrap: wrap; gap: 6px; }
    
    /* 歷史紀錄專屬小球 */
    .h-ball {
        width: 32px; height: 32px; line-height: 32px; border-radius: 50%;
        text-align: center; font-size: 14px; font-weight: bold; color: white;
        background: radial-gradient(circle at 30% 30%, #ef4444, #991b1b);
        box-shadow: 0 2px 4px rgba(0,0,0,0.4);
    }
    .h-ball-super { 
        background: radial-gradient(circle at 30% 30%, #fbbf24, #b45309); 
        color: #111827; box-shadow: 0 0 6px rgba(251, 191, 36, 0.8); 
    }

    /* 預測與統計大球 */
    .ball-container { display: flex; flex-wrap: wrap; justify-content: flex-start; gap: 10px; padding: 10px 0; }
    .lottery-ball {
        display: inline-block; width: 42px; height: 42px; line-height: 42px;
        border-radius: 50%; color: #ffffff !important; font-size: 18px; font-weight: bold; text-align: center;
        background: radial-gradient(circle at 30% 30%, #ef4444, #991b1b); box-shadow: 0 0 8px rgba(239, 68, 68, 0.4);
    }
    .lottery-ball-cold { background: radial-gradient(circle at 30% 30%, #14b8a6, #0f766e) !important; box-shadow: 0 0 8px rgba(20, 184, 166, 0.4) !important; }
    .lottery-ball-latest { background: radial-gradient(circle at 30% 30%, #3b82f6, #1d4ed8) !important; box-shadow: 0 0 8px rgba(59, 130, 246, 0.4) !important; }
    .lottery-ball-super { background: radial-gradient(circle at 30% 30%, #fbbf24, #b45309) !important; box-shadow: 0 0 12px rgba(251, 191, 36, 0.8) !important; color: #111827 !important; }

    .stat-item { display: flex; flex-direction: column; align-items: center; margin: 3px; }
    .stat-label { font-size: 12px; color: #9ca3af; margin-top: 4px; font-weight: bold; }
    .double-ball-wrapper { display: flex; gap: 2px; }
</style>
""", unsafe_allow_html=True)

def render_stat_balls(stat_data, suffix="次", is_cold=False, is_double=False):
    html = "<div class='ball-container'>"
    ball_class = "lottery-ball lottery-ball-cold" if is_cold else "lottery-ball"
    for item, val in stat_data:
        if is_double: b_html = f"<div class='double-ball-wrapper'><div class='{ball_class}'>{item[0]:02d}</div><div class='{ball_class}'>{item[1]:02d}</div></div>"
        else: b_html = f"<div class='{ball_class}'>{item:02d}</div>"
        html += f"<div class='stat-item'>{b_html}<div class='stat-label'>{val} {suffix}</div></div>"
    html += "</div>"
    return html

@st.cache_data(ttl=60)
def fetch_real_bingo_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    data = []
    try:
        url = "https://www.pilio.idv.tw/bingo/list.asp" 
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8' 
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.find_all('tr')
        for row in rows:
            text_content = row.get_text(separator=' ')
            if "115" in text_content or "114" in text_content:
                raw_nums = [int(s) for s in text_content.split() if s.isdigit() and 1 <= int(s) <= 80]
                seen = set()
                draw_ordered = [x for x in raw_nums if not (x in seen or seen.add(x))]
                draw = sorted(draw_ordered[:20])
                
                if len(draw) >= 20:
                    super_num = raw_nums[-1] if len(raw_nums) >= 21 else draw[-1]
                    period_match = re.search(r'(11[45]\d{6,})', text_content)
                    period_text = period_match.group(1) if period_match else "未知期數"
                    big_count = sum(1 for n in draw if n >= 41)
                    odd_count = sum(1 for n in draw if n % 2 != 0)
                    data.append({
                        "期數": period_text, 
                        "超級獎號": super_num,
                        "大小比例": f"<span style='color:#ef4444'>大 {big_count}</span> : <span style='color:#60a5fa'>小 {20-big_count}</span>", 
                        "奇偶比例": f"奇 {odd_count} : 偶 {20-odd_count}", 
                        "原始陣列": draw 
                    })
        if len(data) > 0: return pd.DataFrame(data), True
        else: raise Exception("資料庫結構異常")
    except Exception as e:
        for i in range(200):
            period_num = 115000000 + 200 - i
            draw = sorted(random.sample(range(1, 81), 20))
            super_num = random.choice(draw)
            big_count = sum(1 for n in draw if n >= 41)
            odd_count = sum(1 for n in draw if n % 2 != 0)
            data.append({"期數": str(period_num), "超級獎號": super_num, "大小比例": f"大 {big_count} : 小 {20-big_count}", "奇偶比例": f"奇 {odd_count} : 偶 {20-odd_count}", "原始陣列": draw})
        return pd.DataFrame(data), False, str(e)

# --- 頂部區塊：標題 ---
st.markdown("<h1>🏆 HLF 賓果 AI 分析系統</h1>", unsafe_allow_html=True)

# --- 整合控制列 (時鐘 + 倒數 + 更新按鈕) ---
# 將原本分開的按鈕和時間整合進同一個響應式區塊，保證在一行/平行顯示
top_bar_html = """
<div style="display: flex; justify-content: space-between; align-items: center; background-color: #1f2937; padding: 10px 15px; border-radius: 8px; border: 1px solid #374151; margin-bottom: 20px;">
    <div style="font-family: monospace;">
        <div id="clock" style="font-size: 15px; font-weight: bold; color: #60a5fa;"></div>
        <div id="countdown" style="font-size: 12px; color: #ef4444; margin-top: 4px; font-weight: bold;"></div>
    </div>
    <div>
        <a href="/?refresh=1" target="_parent" style="display: inline-block; background: linear-gradient(180deg, #1e3a8a 0%, #1e40af 100%); color: white; padding: 8px 12px; border-radius: 5px; text-decoration: none; font-size: 13px; font-weight: bold; border: 1px solid #3b82f6; box-shadow: 0 2px 5px rgba(0,0,0,0.3);">🔄 手動更新</a>
    </div>
</div>
<script>
    var timeLeft = 60;
    function updateAll() {
        var now = new Date();
        document.getElementById('clock').innerText = now.toLocaleDateString('zh-TW') + " " + now.toLocaleTimeString('zh-TW', { hour12: false });
        document.getElementById('countdown').innerText = "倒數更新： " + timeLeft + " 秒";
        timeLeft--;
        if (timeLeft < 0) {
            window.parent.location.href = '/?refresh=1';
        }
    }
    setInterval(updateAll, 1000); updateAll();
</script>
"""
components.html(top_bar_html, height=85)

result = fetch_real_bingo_data()
df_history = result[0]
latest_draw = df_history.iloc[0]['原始陣列']
latest_super = df_history.iloc[0]['超級獎號']
latest_period = df_history.iloc[0]['期數']

recent_30_arrays = df_history.head(30)['原始陣列'].tolist()

counts_30 = {i: 0 for i in range(1, 81)}
for arr in recent_30_arrays:
    for num in arr: counts_30[num] += 1
sorted_30 = sorted(counts_30.items(), key=lambda x: x[1], reverse=True)
hot_20 = sorted_30[:20]
cold_20 = sorted(counts_30.items(), key=lambda x: x[1])[:20] 

gaps_30 = {i: 30 for i in range(1, 81)}
for idx, arr in enumerate(recent_30_arrays):
    for num in arr:
        if gaps_30[num] == 30: gaps_30[num] = idx
overdue_20 = sorted(gaps_30.items(), key=lambda x: x[1], reverse=True)[:20]

# ======== 區塊一：最新一期獎號 ========
st.header("📌 最新一期開獎結果")
st.markdown(f"**第 {latest_period} 期** (金色球為本期超級獎號)")

html_latest_balls = ""
for n in latest_draw:
    if n == latest_super:
        html_latest_balls += f"<div class='lottery-ball lottery-ball-super'>{n:02d}</div>"
    else:
        html_latest_balls += f"<div class='lottery-ball lottery-ball-latest'>{n:02d}</div>"

st.markdown(f"<div class='ball-container'>{html_latest_balls}</div>", unsafe_allow_html=True)
st.markdown("---")

# ======== 區塊二：五大策略 AI 智慧預測 ========
st.header("🎯 策略型智慧號碼預測")
star_selection = st.selectbox("請選擇預測星數：", [f"{i}星" for i in range(1, 11)], index=2)
star_num = int(star_selection.replace("星", ""))

col_b1, col_b2, col_b3, col_b4, col_b5 = st.columns(5)
pred_type = None

if col_b1.button("⚖️ 均衡選號", use_container_width=True): pred_type = "balanced"
if col_b2.button("🔥 熱門號碼", use_container_width=True): pred_type = "hot"
if col_b3.button("❄️ 冷門號碼", use_container_width=True): pred_type = "cold"
if col_b4.button("🎲 隨機選號", use_container_width=True): pred_type = "random"
if col_b5.button("⏳ 久未開號碼", use_container_width=True): pred_type = "overdue"

if pred_type:
    with st.spinner("AI 核心演算法正在解析盤勢..."):
        time.sleep(0.5) 
        predicted = []
        hot_pool = [item[0] for item in hot_20]
        cold_pool = [item[0] for item in cold_20]
        overdue_pool = [item[0] for item in overdue_20]
        
        if pred_type == "hot": predicted = random.sample(hot_pool, min(star_num, len(hot_pool)))
        elif pred_type == "cold": predicted = random.sample(cold_pool, min(star_num, len(cold_pool)))
        elif pred_type == "overdue": predicted = random.sample(overdue_pool, min(star_num, len(overdue_pool)))
        elif pred_type == "balanced":
            half = star_num // 2
            rem = star_num - half
            p_hot = random.sample(hot_pool, min(half, len(hot_pool)))
            p_cold_pool = [x for x in cold_pool if x not in p_hot]
            p_cold = random.sample(p_cold_pool, min(rem, len(p_cold_pool)))
            predicted = p_hot + p_cold
        elif pred_type == "random":
            weights = [counts_30.get(x, 0) + 1 for x in range(1, 81)]
            drawn_set = set()
            while len(drawn_set) < star_num:
                res = random.choices(range(1, 81), weights=weights, k=star_num - len(drawn_set))
                drawn_set.update(res)
            predicted = list(drawn_set)
            
        predicted.sort()
        st.session_state.ai_predicted = predicted
        st.session_state.ai_star_num = star_num

if st.session_state.ai_predicted:
    st.success(f"✅ 運算完成！為您推薦的 **{st.session_state.ai_star_num} 星** 號碼如下：")
    html_pred_balls = "".join([f"<div class='lottery-ball'>{n:02d}</div>" for n in st.session_state.ai_predicted])
    st.markdown(f"<div class='ball-container'>{html_pred_balls}</div>", unsafe_allow_html=True)
st.markdown("---")

# ======== 區塊三：最新 30 期大數據統計 ========
st.header("📊 最新 30 期開獎趨勢統計")

consec_counts = Counter()
for i in range(len(recent_30_arrays) - 1): 
    current_draw = set(recent_30_arrays[i])
    prev_draw = set(recent_30_arrays[i+1])
    intersect = current_draw.intersection(prev_draw)
    for n in intersect: consec_counts[n] += 1
top_consec = consec_counts.most_common(15)

double_consec_counts = Counter()
for i in range(len(recent_30_arrays) - 1):
    intersect = set(recent_30_arrays[i]).intersection(set(recent_30_arrays[i+1]))
    if len(intersect) >= 2:
        for pair in itertools.combinations(sorted(intersect), 2): double_consec_counts[pair] += 1
top_double_consec = double_consec_counts.most_common(10)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔥 熱門", "❄️ 冷門", "🔁 連莊", "👯 雙連", "⏳ 遺漏"])
with tab1: st.markdown(render_stat_balls(hot_20, "次"), unsafe_allow_html=True)
with tab2: st.markdown(render_stat_balls(cold_20, "次", is_cold=True), unsafe_allow_html=True)
with tab3: 
    if top_consec: st.markdown(render_stat_balls(top_consec, "次連莊"), unsafe_allow_html=True)
    else: st.info("近 30 期尚無連莊號碼。")
with tab4:
    if top_double_consec: st.markdown(render_stat_balls(top_double_consec, "次連莊", is_double=True), unsafe_allow_html=True)
    else: st.info("近 30 期尚無雙連莊組合。")
with tab5: st.markdown(render_stat_balls(overdue_20, "期", is_cold=True), unsafe_allow_html=True)
st.markdown("---")

# ======== 區塊四：歷史明細 (卡片化完美自適應) ========
with st.expander("📋 展開查看完整歷史開獎明細清單 (近 200 期)", expanded=False):
    # 使用卡片式排版取代死板的表格，杜絕手機左右滑動
    history_cards_html = ""
    for idx, row in df_history.iterrows():
        nums = row['原始陣列']
        s_num = row['超級獎號']
        
        balls_html = ""
        for n in nums:
            if n == s_num:
                balls_html += f"<div class='h-ball h-ball-super'>{n:02d}</div>"
            else:
                balls_html += f"<div class='h-ball'>{n:02d}</div>"
        
        history_cards_html += f"""
        <div class='history-card'>
            <div class='history-header'>
                <span class='history-period'>第 {row['期數']} 期</span>
                <span class='history-stats'>{row['大小比例']} | {row['奇偶比例']}</span>
            </div>
            <div class='history-balls'>{balls_html}</div>
        </div>
        """
    st.markdown(history_cards_html, unsafe_allow_html=True)
st.markdown("---")

# ======== 區塊五：玩法介紹與免責聲明 ========
st.header("💡 BINGO BINGO 賓果賓果 玩法與獎金規則")
st.markdown("""
**【多樣化玩法介紹】**
* **基本星件玩法**：選號範圍為 01～80，您可以任意選擇玩 1～10 個號碼的玩法（稱為「1星」至「10星」）。每次開獎時，電腦系統將隨機開出 20 個獎號，只要您的選號符合該期任一種中獎情形，即為中獎。
* **超級獎號**：每期開出的第 20 個獎號即當期的「超級獎號」。您可以針對當期的超級獎號進行預測，猜對即贏得高額加倍獎金。
* **猜大小**：您可就當期開出的 20 個獎號中，預測較小的號碼（01～40號）或較大的號碼（41～80號）開出的個數。認為小號碼開出 13 顆 (含) 以上，可投注「猜小」；認為大號碼開出 13 顆 (含) 以上，則投注「猜大」，猜中即為中獎。
* **猜單雙**：您可預測當期 20 個獎號中，單數 (01、03...79) 與雙數 (02、04...80) 開出的個數。認為單數開出 13 顆 (含) 以上，可投注「猜單」；認為雙數開出 13 顆 (含) 以上，則投注「猜雙」，猜中即為中獎。
""")

st.markdown("""
<div class='table-responsive'>
    <table class='jyb-table'>
        <thead>
            <tr>
                <th style='width: 12%; text-align: center;'>玩法</th>
                <th style='width: 44%;'>對中號碼數與對應獎金</th>
                <th style='width: 44%;'>容錯與保底獎金</th>
            </tr>
        </thead>
        <tbody>
            <tr><td style='text-align: center;'><b>10星</b></td><td>中 10：<b style='color:#ef4444'>5,000,000 元</b><br>中 9：250,000 元<br>中 8：25,000 元</td><td>中 7：2,500 元<br>中 6：250 元<br>中 5 / 中 0：皆 25 元</td></tr>
            <tr><td style='text-align: center;'><b>9星</b></td><td>中 9：<b style='color:#ef4444'>1,000,000 元</b><br>中 8：100,000 元<br>中 7：3,000 元</td><td>中 6：500 元<br>中 5：100 元<br>中 4 / 中 0：皆 25 元</td></tr>
            <tr><td style='text-align: center;'><b>8星</b></td><td>中 8：<b style='color:#ef4444'>500,000 元</b><br>中 7：20,000 元</td><td>中 6：1,000 元<br>中 5：200 元<br>中 4 / 中 0：皆 25 元</td></tr>
            <tr><td style='text-align: center;'><b>7星</b></td><td>中 7：<b style='color:#ef4444'>80,000 元</b><br>中 6：3,000 元</td><td>中 5：300 元<br>中 4：50 元<br>中 3：25 元</td></tr>
            <tr><td style='text-align: center;'><b>6星</b></td><td>中 6：<b style='color:#ef4444'>25,000 元</b><br>中 5：1,000 元</td><td>中 4：200 元<br>中 3：25 元</td></tr>
            <tr><td style='text-align: center;'><b>5星</b></td><td>中 5：<b style='color:#ef4444'>7,500 元</b><br>中 4：500 元</td><td>中 3：50 元</td></tr>
            <tr><td style='text-align: center;'><b>4星</b></td><td>中 4：<b style='color:#ef4444'>1,000 元</b><br>中 3：100 元</td><td>中 2：25 元</td></tr>
            <tr><td style='text-align: center;'><b>3星</b></td><td>中 3：<b style='color:#ef4444'>500 元</b></td><td>中 2：50 元</td></tr>
            <tr><td style='text-align: center;'><b>2星</b></td><td>中 2：<b style='color:#ef4444'>75 元</b></td><td></td></tr>
            <tr><td style='text-align: center;'><b>1星</b></td><td>中 1：<b style='color:#ef4444'>50 元</b></td><td></td></tr>
            <tr><td colspan='3' style='text-align: center; color: #9ca3af; font-size: 12px; padding: 12px;'>(註：以上為基本倍數獎金，若該期總中獎金額超過官方上限，將依台彩規定按比例分配)</td></tr>
        </tbody>
    </table>
</div>
""", unsafe_allow_html=True)

# 免責聲明：使用自訂 HTML 將字體縮小，不再跟玩法文字一樣大
st.markdown("""
<div style="background-color: #450a0a; border: 1px solid #991b1b; padding: 15px; border-radius: 8px; margin-top: 10px;">
    <p style="color: #fca5a5; font-size: 13px; font-weight: bold; margin-bottom: 5px;">⚠️ 網站免責聲明：</p>
    <p style="color: #fecaca; font-size: 12px; line-height: 1.6; margin: 0;">本站提供之預測號碼與統計大數據，均由 AI 演算法與歷史開獎資料計算得出。所有資訊僅供學術交流、數據分析與娛樂參考之用，絕對不保證未來中獎機率。請使用者衡量自身財務狀況，保持理性投注，切勿過度沉迷。本站為獨立開發者之個人專案，與「台灣彩券股份有限公司」無任何官方合作、背書或從屬關係。</p>
</div>
""", unsafe_allow_html=True)

# --- 系統更新時間標籤 (抓取程式碼實體檔案最後修改時間) ---
tw_tz = timezone(timedelta(hours=8))
try:
    # 抓取這份 app.py 檔案最後一次存檔的時間
    file_mtime = os.path.getmtime(__file__)
    update_time = datetime.fromtimestamp(file_mtime, tw_tz).strftime("%Y-%m-%d %H:%M:%S")
except:
    # 萬一在某些雲端伺服器抓不到檔案時間的備用方案
    update_time = datetime.now(tw_tz).strftime("%Y-%m-%d %H:%M:%S")

st.markdown(f"<div style='text-align: center; color: #6b7280; margin-top: 50px; font-size: 12px;'>程式碼最後更新時間：{update_time}</div>", unsafe_allow_html=True)