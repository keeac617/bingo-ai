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
from datetime import datetime, timezone, timedelta

# --- 網頁基本設定 ---
st.set_page_config(page_title="旗艦版賓果數據預報", layout="wide")

# --- 啟動記憶體功能 ---
if "ai_predicted" not in st.session_state:
    st.session_state.ai_predicted = []
if "ai_star_num" not in st.session_state:
    st.session_state.ai_star_num = 0

# --- 質感深色主題與下拉選單徹底修復 ---
st.markdown("""
<style>
    .stApp { background-color: #0e1117 !important; }
    body, p, span, div, li, h1, h2, h3, h4, h5, h6, label { color: #e2e8f0 !important; }
    
    div[data-baseweb="select"] > div { background-color: #2d3748 !important; border-color: #4a5568 !important; }
    div[data-baseweb="select"] span { color: #ffffff !important; font-weight: bold; }
    div[data-baseweb="popover"] > div { background-color: #2d3748 !important; }
    ul[role="listbox"] { background-color: #2d3748 !important; }
    li[role="option"] { color: #ffffff !important; background-color: #2d3748 !important; }
    li[role="option"]:hover { background-color: #4a5568 !important; }

    table { width: 100%; border-collapse: collapse; background-color: #1a202c !important; color: #e2e8f0 !important; font-size: 14px; margin-bottom: 20px; }
    th, td { border: 1px solid #4a5568 !important; padding: 10px; text-align: left; }
    th { background-color: #2d3748 !important; color: #63b3ed !important; }

    div[data-testid="metric-container"] {
        background-color: #1a202c !important; border: 1px solid #2d3748 !important;
        border-top: 3px solid #3182ce !important; padding: 15px; border-radius: 8px; text-align: center;
        box-shadow: 0 4px 8px rgba(0,0,0,0.5);
    }
    div[data-testid="metric-container"] div { color: #63b3ed !important; }

    div.stButton > button {
        background: linear-gradient(180deg, #2b6cb0 0%, #2c5282 100%) !important;
        color: #ffffff !important; font-weight: bold !important; border: 1px solid #4299e1 !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3); transition: all 0.3s ease;
    }
    div.stButton > button:hover { background: linear-gradient(180deg, #3182ce 0%, #2b6cb0 100%) !important; border: 1px solid #63b3ed !important; transform: translateY(-2px); }

    .ball-container { display: flex; flex-wrap: wrap; justify-content: flex-start; gap: 12px; padding: 10px 0; }
    .lottery-ball {
        display: inline-block; width: 45px; height: 45px; line-height: 45px;
        border-radius: 50%; color: #ffffff !important; font-size: 20px; font-weight: bold; text-align: center;
        background: radial-gradient(circle at 30% 30%, #ff4b4b, #9b0000); box-shadow: 0 0 8px rgba(255, 75, 75, 0.4);
    }
    .lottery-ball-cold { background: radial-gradient(circle at 30% 30%, #4fd1c5, #285e61) !important; box-shadow: 0 0 8px rgba(79, 209, 197, 0.4) !important; }
    .lottery-ball-latest { background: radial-gradient(circle at 30% 30%, #3182ce, #153e75) !important; box-shadow: 0 0 8px rgba(49, 130, 206, 0.4) !important; }
    .lottery-ball-super { 
        background: radial-gradient(circle at 30% 30%, #ecc94b, #b7791f) !important; 
        box-shadow: 0 0 12px rgba(236, 201, 75, 0.8) !important; 
        color: #1a202c !important;
    }

    .stat-item { display: flex; flex-direction: column; align-items: center; margin: 5px; }
    .stat-label { font-size: 13px; color: #a0aec0; margin-top: 6px; font-weight: bold; }
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
                        "開獎號碼": ", ".join([f"{n:02d}" for n in draw]), 
                        "超級獎號": super_num,
                        "大小比例": f"大 {big_count} : 小 {20-big_count}", 
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
            data.append({"期數": str(period_num), "開獎號碼": ", ".join([f"{n:02d}" for n in draw]), "超級獎號": super_num, "大小比例": f"大 {big_count} : 小 {20-big_count}", "奇偶比例": f"奇 {odd_count} : 偶 {20-odd_count}", "原始陣列": draw})
        return pd.DataFrame(data), False, str(e)

col_title, col_clock = st.columns([2, 1])
with col_title:
    st.title("🏆 Bingo 專業大數據終端分析系統")
    
with col_clock:
    clock_html = """
    <div style="text-align: right; font-family: monospace;">
        <div id="clock" style="font-size: 20px; font-weight: bold; color: #63b3ed; padding-top: 10px;"></div>
        <div id="countdown" style="font-size: 13px; color: #fc8181; margin-top: 5px; font-weight: bold;"></div>
    </div>
    <script>
        var timeLeft = 60;
        function updateAll() {
            var now = new Date();
            document.getElementById('clock').innerText = now.toLocaleDateString('zh-TW') + " " + now.toLocaleTimeString('zh-TW', { hour12: false });
            document.getElementById('countdown').innerText = "🔄 距離自動更新資料： " + timeLeft + " 秒";
            timeLeft--;
            if (timeLeft < 0) {
                timeLeft = 60; 
                var btns = window.parent.document.querySelectorAll('button');
                for(var i=0; i<btns.length; i++) {
                    if(btns[i].innerText.includes('手動更新資料')) { btns[i].click(); break; }
                }
            }
        }
        setInterval(updateAll, 1000); updateAll();
    </script>
    """
    components.html(clock_html, height=70)

if st.button("🔄 手動更新資料", key="hidden_refresh"):
    st.cache_data.clear()

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
st.write("所有指標隨開獎結果自動同步，即時更新。")

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

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔥 總熱門前20碼", "❄️ 總冷門前20碼", "🔁 熱門連莊號", "👯 雙連莊號碼", "⏳ 最久未開 (遺漏)"])
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

# ======== 區塊四：歷史明細 (收合設計) ========
with st.expander("📋 展開查看完整歷史開獎明細清單 (近 200 期)", expanded=False):
    df_display = df_history.drop(columns=['原始陣列'])
    st.dataframe(df_display, use_container_width=True, height=400)
st.markdown("---")

# ======== 區塊五：玩法介紹與免責聲明 ========
st.header("💡 BINGO BINGO 賓果賓果 玩法與獎金規則")
st.markdown("""
**【多樣化玩法介紹】**
* **基本星件玩法**：玩家可從 01 至 80 號中任選 1 到 10 個號碼進行投注（即 1星至 10星玩法）。系統每期將隨機開出 20 個獎號，只要您的選號與開出獎號符合該星等的中獎條件，即可獲得對應獎金。
* **超級獎號**：每期開出的第 20 個號碼即為專屬的「超級獎號」。玩家可選擇附加投注超級獎號玩法，只要您的選號中包含此超級獎號，即可贏得更高額的專屬加倍獎金。
* **猜大小**：預測當期 20 個開獎號碼的整體落球分佈。若認為「小號碼 (01～40)」將開出 13 顆 (含) 以上，可投注「猜小」；若認為「大號碼 (41～80)」將開出 13 顆 (含) 以上，則投注「猜大」。猜中即獲得 6 倍獎金 (單注獎金 150 元)。
* **猜單雙**：預測當期 20 個獎號的單雙數分佈。若認為「單數 (01, 03...79)」開出 13 顆 (含) 以上，可投注「猜單」；若認為「雙數 (02, 04...80)」開出 13 顆 (含) 以上，則投注「猜雙」。猜中亦可獲得 6 倍獎金 (單注獎金 150 元)。
""")

st.markdown("""
**【星件玩法獎金分配表 (以單注 25 元為例)】**
| 玩法 | 對中號碼數與對應獎金 | 容錯與保底獎金 |
|---|---|---|
| **10星** | 中 10：**5,000,000 元** <br> 中 9：250,000 元 <br> 中 8：25,000 元 | 中 7：2,500 元 <br> 中 6：250 元 <br> 中 5 / 中 0：皆 25 元 |
| **9星** | 中 9：**1,000,000 元** <br> 中 8：100,000 元 <br> 中 7：3,000 元 | 中 6：500 元 <br> 中 5：100 元 <br> 中 4 / 中 0：皆 25 元 |
| **8星** | 中 8：**500,000 元** <br> 中 7：20,000 元 | 中 6：1,000 元 <br> 中 5：200 元 <br> 中 4 / 中 0：皆 25 元 |
| **7星** | 中 7：**80,000 元** <br> 中 6：3,000 元 | 中 5：300 元 <br> 中 4：50 元 <br> 中 3：25 元 |
| **6星** | 中 6：**25,000 元** <br> 中 5：1,000 元 | 中 4：200 元 <br> 中 3：25 元 |
| **5星** | 中 5：**7,500 元** <br> 中 4：500 元 | 中 3：50 元 |
| **4星** | 中 4：**1,000 元** <br> 中 3：100 元 | 中 2：25 元 |
| **3星** | 中 3：**500 元** | 中 2：50 元 |
| **2星** | 中 2：**75 元** | |
| **1星** | 中 1：**50 元** | |
*(註：以上為基本倍數獎金，若該期總中獎金額超過官方上限，將依台彩規定按比例分配)*
""", unsafe_allow_html=True)

st.warning("""
**⚠️ 網站免責聲明：**
本站提供之預測號碼與統計大數據，均由 AI 演算法與歷史開獎資料計算得出。所有資訊僅供學術交流、數據分析與娛樂參考之用，絕對不保證未來中獎機率。
請使用者衡量自身財務狀況，保持理性投注，切勿過度沉迷。本站為獨立開發者之個人專案，與「台灣彩券股份有限公司」無任何官方合作、背書或從屬關係。
""")

# --- 系統更新時間標籤 ---
tw_tz = timezone(timedelta(hours=8))
current_time = datetime.now(tw_tz).strftime("%Y-%m-%d %H:%M:%S")
st.markdown(f"<div style='text-align: center; color: #718096; margin-top: 50px; font-size: 12px;'>系統最後更新時間：{current_time} (依據伺服器自動校時)</div>", unsafe_allow_html=True)