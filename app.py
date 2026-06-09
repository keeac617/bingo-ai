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
st.set_page_config(page_title="HLF 綜合彩券 AI 分析總署", layout="wide")

# --- 設定返回最上層的隱形錨點 ---
st.markdown("<div id='top-anchor'></div>", unsafe_allow_html=True)

# 處理手動更新的參數
if "refresh" in st.query_params:
    st.cache_data.clear()
    try:
        del st.query_params["refresh"]
    except:
        pass

if "current_game" not in st.session_state:
    st.session_state.current_game = "Home"
if "ai_predicted" not in st.session_state:
    st.session_state.ai_predicted = []
if "ai_star_num" not in st.session_state:
    st.session_state.ai_star_num = 0
if "last_game" not in st.session_state:
    st.session_state.last_game = "Home"

if st.session_state.current_game != st.session_state.last_game:
    st.session_state.ai_predicted = []
    st.session_state.last_game = st.session_state.current_game

# --- 定義六大彩券參數 ---
GAME_CONFIG = {
    "賓果賓果": {"pool": 80, "draws": 20, "super": True, "desc": "01～80號，每期開20碼"},
    "大樂透": {"pool": 49, "draws": 6, "super": True, "desc": "01～49號，每期開6碼+1特別號"},
    "威力彩": {"pool": 38, "draws": 6, "super": True, "desc": "第一區01～38號，第二區01～08號"},
    "今彩539": {"pool": 39, "draws": 5, "super": False, "desc": "01～39號，每期開5碼"},
    "三星彩": {"pool": 9, "draws": 3, "super": False, "desc": "三位數字，各0～9"},
    "四星彩": {"pool": 9, "draws": 4, "super": False, "desc": "四位數字，各0～9"}
}

# --- 質感深色主題與全站 CSS ---
st.markdown("""
<style>
    .stApp { background-color: #0a0e17 !important; }
    body, p, span, div, li, h2, h3, h4, h5, h6, label { color: #e2e8f0 !important; }
    h1 { font-size: min(6vw, 2.2rem) !important; white-space: nowrap !important; color: #e2e8f0 !important; margin-bottom: 5px !important; }

    .game-card { background: linear-gradient(145deg, #1f2937, #111827); border: 1px solid #374151; border-radius: 12px; padding: 20px; text-align: center; cursor: pointer; transition: all 0.3s ease; box-shadow: 0 4px 6px rgba(0,0,0,0.3); margin-bottom: 15px; }
    .game-card:hover { transform: translateY(-5px); border-color: #3b82f6; box-shadow: 0 8px 15px rgba(59, 130, 246, 0.4); }
    .game-title { font-size: 24px; font-weight: bold; color: #60a5fa; margin-bottom: 10px; }
    .game-desc { font-size: 14px; color: #9ca3af; }

    .nav-container { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px; }
    div.stButton > button { background: linear-gradient(180deg, #1e3a8a 0%, #1e40af 100%) !important; color: #ffffff !important; font-weight: bold !important; border: 1px solid #3b82f6 !important; box-shadow: 0 2px 5px rgba(0,0,0,0.5); transition: all 0.3s ease; width: 100%; }
    div.stButton > button:hover { background: linear-gradient(180deg, #2563eb 0%, #1d4ed8 100%) !important; border: 1px solid #60a5fa !important; transform: translateY(-2px); }

    div[data-baseweb="tab-list"] { flex-wrap: wrap !important; gap: 8px !important; justify-content: flex-start; }
    div[data-baseweb="tab"] { padding: 8px 12px !important; margin-bottom: 5px !important; background-color: #1f2937 !important; border: 1px solid #374151 !important; border-radius: 6px; }

    div[data-baseweb="select"] > div { background-color: #1f2937 !important; border-color: #374151 !important; color: #ffffff !important; }
    div[data-baseweb="select"] span { color: #ffffff !important; font-weight: bold; }
    div[role="listbox"] { background-color: #1f2937 !important; border: 1px solid #374151 !important; }
    ul[role="listbox"], li[role="option"] { background-color: #1f2937 !important; color: #ffffff !important; }
    li[role="option"]:hover { background-color: #374151 !important; }

    div[data-testid="metric-container"] { background-color: #111827 !important; border: 1px solid #1f2937 !important; border-top: 3px solid #3b82f6 !important; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    div[data-testid="metric-container"] div { color: #60a5fa !important; }

    div[data-testid="stExpander"] details { background-color: #111827 !important; border: 1px solid #374151 !important; border-radius: 8px; }
    div[data-testid="stExpander"] summary { background-color: #1f2937 !important; color: #60a5fa !important; border-radius: 8px; padding: 10px; }
    div[data-testid="stExpander"] summary:hover { background-color: #374151 !important; }
    div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] { background-color: #111827 !important; padding: 15px; }

    .history-card { background-color: #1f2937; border: 1px solid #374151; border-radius: 8px; padding: 12px; margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.3); }
    .history-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #374151; padding-bottom: 8px; margin-bottom: 10px; font-size: 14px; }
    .history-period { font-weight: bold; color: #60a5fa; font-size: 16px; display: flex; align-items: center; }
    .history-date { font-size: 12px; color: #9ca3af; font-weight: normal; margin-left: 10px; background-color: #111827; padding: 2px 6px; border-radius: 4px;}
    .history-balls { display: flex; flex-wrap: wrap; gap: 6px; }
    
    .ball-container { display: flex; flex-wrap: wrap; justify-content: flex-start; gap: 8px; padding: 10px 0; }
    .lottery-ball { display: inline-block; width: 40px; height: 40px; line-height: 40px; border-radius: 50%; color: #ffffff !important; font-size: 16px; font-weight: bold; text-align: center; background: radial-gradient(circle at 30% 30%, #ef4444, #991b1b); box-shadow: 0 0 8px rgba(239, 68, 68, 0.4); }
    .lottery-ball-cold { background: radial-gradient(circle at 30% 30%, #14b8a6, #0f766e) !important; box-shadow: 0 0 8px rgba(20, 184, 166, 0.4) !important; }
    .lottery-ball-latest { background: radial-gradient(circle at 30% 30%, #3b82f6, #1d4ed8) !important; box-shadow: 0 0 8px rgba(59, 130, 246, 0.4) !important; }
    .lottery-ball-super { background: radial-gradient(circle at 30% 30%, #fbbf24, #b45309) !important; box-shadow: 0 0 12px rgba(251, 191, 36, 0.8) !important; color: #111827 !important; }
    .h-ball { width: 32px; height: 32px; line-height: 32px; border-radius: 50%; text-align: center; font-size: 14px; font-weight: bold; color: white; background: radial-gradient(circle at 30% 30%, #ef4444, #991b1b); box-shadow: 0 2px 4px rgba(0,0,0,0.4); }
    .h-ball-super { background: radial-gradient(circle at 30% 30%, #fbbf24, #b45309); color: #111827; box-shadow: 0 0 6px rgba(251, 191, 36, 0.8); }

    .stat-item { display: flex; flex-direction: column; align-items: center; margin: 2px; }
    .stat-label { font-size: 11px; color: #9ca3af; margin-top: 4px; font-weight: bold; }
    .double-ball-wrapper { display: flex; gap: 2px; }

    .table-responsive { width: 100%; overflow-x: auto; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    .jyb-table { width: 100%; border-collapse: collapse; background-color: #111827; color: #e2e8f0; font-size: 14px; text-align: center; }
    .jyb-table th { background-color: #1f2937; color: #60a5fa; padding: 10px; border: 1px solid #374151; font-weight: bold; }
    .jyb-table td { padding: 8px; border: 1px solid #374151; }
    @media (max-width: 768px) { .jyb-table { font-size: 12px; } .jyb-table th, .jyb-table td { padding: 5px; } }

    .back-to-top {
        position: fixed; bottom: 80px; right: 30px; z-index: 99999;
        background: linear-gradient(180deg, #3b82f6 0%, #1d4ed8 100%);
        color: white !important; width: 50px; height: 50px; line-height: 45px;
        text-align: center; border-radius: 50%; font-size: 24px; text-decoration: none;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5); border: 2px solid #60a5fa; transition: transform 0.3s;
    }
    .back-to-top:hover { transform: scale(1.1); }

    /* 手機版排版終極優化：強制所有欄位橫向自動折行，不使用相容性差的語法 */
    @media (max-width: 768px) {
        div[data-testid="stHorizontalBlock"] {
            flex-direction: row !important;
            flex-wrap: wrap !important;
            gap: 5px !important;
        }
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            width: auto !important;
            min-width: 28% !important; 
            flex: 1 1 auto !important;
            padding: 0 !important;
        }
        /* 讓手機版導覽按鈕稍微縮小，排列更緊湊 */
        div.stButton > button {
            padding: 4px 8px !important;
            font-size: 13px !important;
            min-height: 38px !important;
        }
    }
</style>
""", unsafe_allow_html=True)

def render_stat_balls(stat_data, suffix="次", is_cold=False, is_double=False):
    html = "<div class='ball-container'>"
    ball_class = "lottery-ball lottery-ball-cold" if is_cold else "lottery-ball"
    is_stars = st.session_state.get('current_game') in ["三星彩", "四星彩"]
    for item, val in stat_data:
        if is_double: 
            b1 = f"{item[0]}" if is_stars else f"{item[0]:02d}"
            b2 = f"{item[1]}" if is_stars else f"{item[1]:02d}"
            b_html = f"<div class='double-ball-wrapper'><div class='{ball_class}'>{b1}</div><div class='{ball_class}'>{b2}</div></div>"
        else: 
            b_val = f"{item}" if is_stars else f"{item:02d}"
            b_html = f"<div class='{ball_class}'>{b_val}</div>"
        html += f"<div class='stat-item'>{b_html}<div class='stat-label'>{val} {suffix}</div></div>"
    html += "</div>"
    return html

# --- 各彩種專屬玩法介紹元件 ---
def show_game_rules(game_name):
    st.header(f"💡 {game_name} 玩法與獎金規則")
    if game_name == "賓果賓果":
        st.markdown("""
        **【多樣化玩法介紹】**
        * **基本星件玩法**：選號範圍為 01～80，您可以任意選擇玩 1～10 個號碼的玩法（稱為「1星」至「10星」）。每次開獎時，電腦系統將隨機開出 20 個獎號，只要您的選號符合該期任一種中獎情形，即為中獎。
        * **超級獎號**：每期開出的第 20 個獎號即當期的「超級獎號」。您可以針對當期的超級獎號進行預測，猜對即贏得高額加倍獎金。
        * **猜大小**：您可就當期開出的 20 個獎號中，預測較小的號碼（01～40號）或較大的號碼（41～80號）開出的個數。認為小號碼開出 13 顆 (含) 以上，可投注「猜小」；認為大號碼開出 13 顆 (含) 以上，則投注「猜大」，猜中單注獎金 150 元。
        * **猜單雙**：您可預測當期 20 個獎號中，單數 (01、03...79) 與雙數 (02、04...80) 開出的個數。認為單數開出 13 顆 (含) 以上，可投注「猜單」；認為雙數開出 13 顆 (含) 以上，則投注「猜雙」，猜中單注獎金 150 元。
        
        <div class='table-responsive'>
            <table class='jyb-table'>
                <thead>
                    <tr><th style='width: 12%; text-align: center;'>玩法</th><th style='width: 44%;'>對中號碼數與對應獎金</th><th style='width: 44%;'>容錯與保底獎金</th></tr>
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
                    <tr><td colspan='3' style='text-align: center; color: #9ca3af; font-size: 12px; padding: 12px;'>(註：以上為基本倍數獎金單注25元，若該期總中獎金額超過官方上限，將依台彩規定按比例分配)</td></tr>
                </tbody>
            </table>
        </div>
        """, unsafe_allow_html=True)
    elif game_name == "大樂透":
        st.markdown("""
        **【玩法介紹】** 選號範圍為 01～49，任選 6 個號碼進行投注。每期開出 6 個號碼加 1 個「特別號」。
        <div class='table-responsive'>
            <table class='jyb-table'>
                <thead><tr><th>獎項</th><th>中獎條件</th><th>獎金分配 (單注50元)</th></tr></thead>
                <tbody>
                    <tr><td><b>頭獎</b></td><td>對中當期 6 個號碼</td><td>總獎金扣除固定獎項後之 82%</td></tr>
                    <tr><td><b>貳獎</b></td><td>任 5 個號碼 ＋ 特別號</td><td>總獎金扣除固定獎項後之 6.5%</td></tr>
                    <tr><td><b>參獎</b></td><td>對中任 5 個號碼</td><td>總獎金扣除固定獎項後之 7%</td></tr>
                    <tr><td><b>肆獎</b></td><td>任 4 個號碼 ＋ 特別號</td><td>總獎金扣除固定獎項後之 4.5%</td></tr>
                    <tr><td><b>伍獎</b></td><td>對中任 4 個號碼</td><td>固定 2,000 元</td></tr>
                    <tr><td><b>陸獎</b></td><td>任 3 個號碼 ＋ 特別號</td><td>固定 1,000 元</td></tr>
                    <tr><td><b>柒獎</b></td><td>任 2 個號碼 ＋ 特別號</td><td>固定 400 元</td></tr>
                    <tr><td><b>普獎</b></td><td>對中任 3 個號碼</td><td>固定 400 元</td></tr>
                </tbody>
            </table>
        </div>
        """, unsafe_allow_html=True)
    elif game_name == "威力彩":
        st.markdown("""
        **【玩法介紹】** 包含兩個選號區。第一區 01～38 選 6 個，第二區 01～08 選 1 個。
        <div class='table-responsive'>
            <table class='jyb-table'>
                <thead><tr><th>獎項</th><th>中獎條件</th><th>獎金分配 (單注100元)</th></tr></thead>
                <tbody>
                    <tr><td><b>頭獎</b></td><td>第1區 6個 ＋ 第2區 1個</td><td>總獎金扣除固定獎項後之 89%</td></tr>
                    <tr><td><b>貳獎</b></td><td>對中第1區 6個號碼</td><td>總獎金扣除固定獎項後之 11%</td></tr>
                    <tr><td><b>參獎</b></td><td>第1區 5個 ＋ 第2區 1個</td><td>固定 150,000 元</td></tr>
                    <tr><td><b>肆獎</b></td><td>對中第1區 5個號碼</td><td>固定 20,000 元</td></tr>
                    <tr><td><b>伍獎</b></td><td>第1區 4個 ＋ 第2區 1個</td><td>固定 4,000 元</td></tr>
                    <tr><td><b>陸獎</b></td><td>對中第1區 4個號碼</td><td>固定 800 元</td></tr>
                    <tr><td><b>柒獎</b></td><td>第1區 3個 ＋ 第2區 1個</td><td>固定 400 元</td></tr>
                    <tr><td><b>捌獎</b></td><td>第1區 2個 ＋ 第2區 1個</td><td>固定 200 元</td></tr>
                    <tr><td><b>玖獎</b></td><td>對中第1區 3個號碼</td><td>固定 100 元</td></tr>
                    <tr><td><b>普獎</b></td><td>第1區 1個 ＋ 第2區 1個</td><td>固定 100 元</td></tr>
                </tbody>
            </table>
        </div>
        """, unsafe_allow_html=True)
    elif game_name == "今彩539":
        st.markdown("""
        **【玩法介紹】** 選號範圍為 01～39，任選 5 個號碼進行投注。每期隨機開出 5 個號碼，無特別號玩法。
        <div class='table-responsive'>
            <table class='jyb-table'>
                <thead><tr><th>獎項</th><th>中獎條件</th><th>單注獎金 (單注50元)</th></tr></thead>
                <tbody>
                    <tr><td><b>頭獎</b></td><td>對中當期 5 個號碼</td><td>8,000,000 元 (最高總額2400萬)</td></tr>
                    <tr><td><b>貳獎</b></td><td>對中任 4 個號碼</td><td>20,000 元</td></tr>
                    <tr><td><b>參獎</b></td><td>對中任 3 個號碼</td><td>300 元</td></tr>
                    <tr><td><b>肆獎</b></td><td>對中任 2 個號碼</td><td>50 元</td></tr>
                </tbody>
            </table>
        </div>
        """, unsafe_allow_html=True)
    elif game_name == "四星彩":
        st.markdown("""
        **【玩法介紹】** 0000～9999 中任選一組四位數字。中獎依據數字與位置是否與開出獎號相符。
        <div class='table-responsive'>
            <table class='jyb-table'>
                <thead><tr><th>獎項</th><th>中獎條件</th><th>單注獎金 (單注25元)</th></tr></thead>
                <tbody>
                    <tr><td><b>壹獎</b></td><td>4個數字與順序完全相同</td><td>50,000 元</td></tr>
                    <tr><td><b>貳獎</b></td><td>前3碼或後3碼數字與順序相同</td><td>5,000 元</td></tr>
                    <tr><td><b>參獎</b></td><td>前2碼或後2碼數字與順序相同</td><td>500 元</td></tr>
                </tbody>
            </table>
        </div>
        """, unsafe_allow_html=True)
    elif game_name == "三星彩":
        st.markdown("""
        **【玩法介紹】** 000～999 中任選一組三位數字。中獎依據數字與位置是否與開出獎號相符。
        <div class='table-responsive'>
            <table class='jyb-table'>
                <thead><tr><th>獎項</th><th>中獎條件</th><th>單注獎金 (單注25元)</th></tr></thead>
                <tbody>
                    <tr><td><b>壹獎</b></td><td>3個數字與順序完全相同</td><td>5,000 元</td></tr>
                    <tr><td><b>貳獎</b></td><td>前2碼或後2碼數字與順序相同</td><td>500 元</td></tr>
                    <tr><td><b>參獎</b></td><td>對中前1碼或後1碼</td><td>50 元</td></tr>
                </tbody>
            </table>
        </div>
        """, unsafe_allow_html=True)

# --- 泛用彩券真實爬蟲引擎 (年度全量網頁高速解析版) ---
@st.cache_data(ttl=60)
def fetch_universal_data(game_name):
    cfg = GAME_CONFIG[game_name]
    data = []
    tw_tz = timezone(timedelta(hours=8))
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml'
    }

    if game_name == "賓果賓果":
        url = "https://www.pilio.idv.tw/bingo/list.asp"
        now = datetime.now(tw_tz)
        minute = now.minute - (now.minute % 5)
        bingo_base_time = now.replace(minute=minute, second=0, microsecond=0)
        
        for page in range(1, 6):
            if len(data) >= 100: break
            try:
                page_url = f"{url}?indexpage={page}"
                response = requests.get(page_url, headers=headers, timeout=5)
                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.text, 'html.parser')
                
                seen_periods = set([d["期數"] for d in data])
                for row in soup.find_all('tr'):
                    try:
                        row_text = row.get_text(separator=' ', strip=True)
                        period_match = re.search(r'(11[2-9]\d{5,8})', row_text)
                        if not period_match:
                            period_match = re.search(r'(\d{7,10})', row_text)
                        if not period_match: continue
                        period_text = period_match.group(1)
                        
                        if period_text in seen_periods: continue
                        
                        calculated_time = bingo_base_time - timedelta(minutes=5 * len(data))
                        date_str = calculated_time.strftime("%m/%d %H:%M")
                        
                        clean_text = row_text.replace(period_text, ' ')
                        clean_text = re.sub(r'\d{4}/\d{1,2}/\d{1,2}|\d{1,2}:\d{2}', ' ', clean_text)
                        
                        raw_nums = [int(x) for x in re.findall(r'(?<!\d)\d{1,2}(?!\d)', clean_text)]
                        valid_nums = [n for n in raw_nums if 1 <= n <= 80]
                        
                        seen = set()
                        draw_ordered = [x for x in valid_nums if not (x in seen or seen.add(x))]
                        draw = sorted(draw_ordered[:20])
                        if len(draw) < 20: continue
                        
                        super_num = draw[-1]
                        seen_periods.add(period_text)
                        data.append({"期數": period_text, "開獎時間": date_str, "超級獎號": super_num, "原始陣列": draw})
                        if len(data) >= 100: break
                    except:
                        continue
            except:
                break
    else:
        # 使用 2026 全年度綜合彙整單頁網址，免去分頁爬取，速度極快且絕無斷層
        auzo_urls = {
            "大樂透": "https://lotto.auzo.tw/biglotto/list_2026_all.html",
            "威力彩": "https://lotto.auzo.tw/power/list_2026_all.html",
            "今彩539": "https://lotto.auzo.tw/daily539/list_2026_all.html",
            "四星彩": "https://lotto.auzo.tw/lotto_historylist_four-star.html",
            "三星彩": "https://lotto.auzo.tw/lotto_historylist_three-star.html"
        }
        url = auzo_urls.get(game_name)
        seen_periods = set()
        
        # 針對歷史網頁線性往下讀取，直到抓滿指定的 50 期紀錄
        for page in range(1, 5):
            if len(data) >= 50: break
            page_url = f"{url}?page={page}" if ("historylist" in url and page > 1) else url
            
            try:
                response = requests.get(page_url, headers=headers, timeout=6)
                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for tag in soup.find_all(['tr', 'div', 'li', 'article']):
                    try:
                        text = tag.get_text(separator=' ', strip=True)
                        if len(text) > 300: continue
                        
                        periods_found = re.findall(r'\b(11[0-9]\d{3,7})\b', text)
                        if len(periods_found) != 1: continue
                        period_text = periods_found[0]
                        
                        if period_text in seen_periods: continue
                        
                        date_match = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2})', text)
                        date_str = date_match.group(1) if date_match else ""
                        
                        clean_text = text.replace(period_text, ' ')
                        if date_str: clean_text = clean_text.replace(date_str, ' ')
                        
                        if game_name in ["三星彩", "四星彩"]:
                            digits = re.findall(r'\d', clean_text)
                            if len(digits) < cfg["draws"]: continue
                            draw = [int(d) for d in digits[:cfg["draws"]]]
                            super_num = None
                        else:
                            raw_nums = [int(x) for x in re.findall(r'(?<!\d)\d{1,2}(?!\d)', clean_text)]
                            valid_nums = [n for n in raw_nums if 1 <= n <= cfg["pool"]]
                            
                            seen = set()
                            draw_ordered = [x for x in valid_nums if not (x in seen or seen.add(x))]
                            draw = sorted(draw_ordered[:cfg["draws"]])
                            if len(draw) < cfg["draws"]: continue
                            
                            super_num = None
                            if cfg["super"]:
                                if game_name == "威力彩":
                                    potential_super = valid_nums[-1] if len(valid_nums) > cfg["draws"] else None
                                    if potential_super and 1 <= potential_super <= 8:
                                        super_num = potential_super
                                else:
                                    super_num = valid_nums[-1] if len(valid_nums) > cfg["draws"] else draw[-1]
                                    
                        seen_periods.add(period_text)
                        data.append({"期數": period_text, "開獎時間": date_str, "超級獎號": super_num, "原始陣列": draw})
                        if len(data) >= 50: break
                    except:
                        continue
            except:
                break

    if len(data) > 0:
        data = sorted(data, key=lambda x: int(x['期數']), reverse=True)
    if len(data) == 0:
        raise Exception("網頁讀取回應超時，或未在目標彙整網頁中解析出符合規則的數據。")
        
    return pd.DataFrame(data)

def show_home_page():
    st.markdown("<h1 style='text-align: center; color: #60a5fa !important; padding-top: 40px;'>🏦 HLF 綜合彩券 AI 分析總署</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #9ca3af !important; margin-bottom: 40px;'>請選擇您要進行預測與分析的彩券項目</p>", unsafe_allow_html=True)
    
    games = list(GAME_CONFIG.items())
    
    # 強制使用「列優先」分配法，確保手機版垂直排列的順序完全一致
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button(f"✨ {games[0][0]}\n\n{games[0][1]['desc']}", key="btn_h0", use_container_width=True): st.session_state.current_game = games[0][0]; st.rerun()
    with c2:
        if st.button(f"✨ {games[1][0]}\n\n{games[1][1]['desc']}", key="btn_h1", use_container_width=True): st.session_state.current_game = games[1][0]; st.rerun()
    with c3:
        if st.button(f"✨ {games[2][0]}\n\n{games[2][1]['desc']}", key="btn_h2", use_container_width=True): st.session_state.current_game = games[2][0]; st.rerun()
        
    c4, c5, c6 = st.columns(3)
    with c4:
        if st.button(f"✨ {games[3][0]}\n\n{games[3][1]['desc']}", key="btn_h3", use_container_width=True): st.session_state.current_game = games[3][0]; st.rerun()
    with c5:
        if st.button(f"✨ {games[4][0]}\n\n{games[4][1]['desc']}", key="btn_h4", use_container_width=True): st.session_state.current_game = games[4][0]; st.rerun()
    with c6:
        if st.button(f"✨ {games[5][0]}\n\n{games[5][1]['desc']}", key="btn_h5", use_container_width=True): st.session_state.current_game = games[5][0]; st.rerun()

def show_game_page(game_name):
    cfg = GAME_CONFIG[game_name]
    
    # 將導覽列移至側邊欄 (Sidebar)
    with st.sidebar:
        st.markdown("### 🎲 切換彩券項目")
        if st.button("🏠 回大廳", key="nav_home", use_container_width=True): st.session_state.current_game = "Home"; st.rerun()
        if st.button("賓果賓果", key="nav_bingo", use_container_width=True): st.session_state.current_game = "賓果賓果"; st.rerun()
        if st.button("大樂透", key="nav_lotto", use_container_width=True): st.session_state.current_game = "大樂透"; st.rerun()
        if st.button("威力彩", key="nav_power", use_container_width=True): st.session_state.current_game = "威力彩"; st.rerun()
        if st.button("今彩539", key="nav_539", use_container_width=True): st.session_state.current_game = "今彩539"; st.rerun()
        if st.button("三星彩", key="nav_3d", use_container_width=True): st.session_state.current_game = "三星彩"; st.rerun()
        if st.button("四星彩", key="nav_4d", use_container_width=True): st.session_state.current_game = "四星彩"; st.rerun()
    
    title_col, clock_col = st.columns([2, 1])
    with title_col:
        st.markdown(f"<h1>🏆 HLF {game_name} AI 分析終端</h1>", unsafe_allow_html=True)
    
    with clock_col:
        # 根據是否為賓果決定是否顯示倒數計時器與動態真實時間運算
        if game_name == "賓果賓果":
            countdown_div = '<div id="countdown" style="font-size: 11px; color: #ef4444; font-weight: bold; margin-top: 1px; white-space: nowrap;"></div>'
            js_timer_logic = """
                var currentMin = now.getMinutes();
                var currentSec = now.getSeconds();
                
                // 動態計算距離下一個 5 分鐘整點（00, 05, 10...）的剩餘秒數
                var nextMin = Math.ceil((currentMin + 0.1) / 5) * 5;
                if (nextMin === currentMin) nextMin += 5;
                var totalSecondsLeft = ((nextMin - currentMin) * 60) - currentSec;
                
                document.getElementById('countdown').innerText = "距離自動更新： " + totalSecondsLeft + " 秒";
                
                // 倒數到 0 時，利用時間戳記強制瀏覽器破除快取並刷新網頁
                if (totalSecondsLeft <= 0) {
                    window.parent.location.search = '?refresh=' + new Date().getTime();
                }
            """
        else:
            countdown_div = ''
            js_timer_logic = ""

        # 利用精確的網頁樣式控制，確保手動更新按鈕與時間在電腦畫面上緊密靠右並排
        top_bar_html = f"""
        <div style="display: flex; justify-content: flex-end; align-items: center; gap: 12px; width: 100%; margin-top: 5px;">
            <button onclick="window.parent.location.search = '?refresh=' + new Date().getTime();" style="background: linear-gradient(180deg, #1e3a8a 0%, #1e40af 100%); color: white; padding: 5px 12px; border-radius: 5px; border: 1px solid #3b82f6; cursor: pointer; font-size: 13px; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.4); white-space: nowrap; height: 32px;">
                🔄 手動更新
            </button>
            <div style="text-align: right; font-family: monospace; line-height: 1.3;">
                <div id="clock" style="font-size: 15px; font-weight: bold; color: #60a5fa; white-space: nowrap;"></div>
                {countdown_div}
            </div>
        </div>
        <script>
            function updateAll() {{
                var now = new Date();
                document.getElementById('clock').innerText = now.toLocaleDateString('zh-TW') + " " + now.toLocaleTimeString('zh-TW', {{ hour12: false }});
                {js_timer_logic}
            }}
            setInterval(updateAll, 1000); updateAll();
        </script>
        """
        components.html(top_bar_html, height=45)

    try:
        df_history = fetch_universal_data(game_name)
    except Exception as e:
        st.error(f"🛑 系統嚴重錯誤：無法取得即時大數據！")
        st.error(f"詳細診斷訊息：{e}")
        st.warning("⚠️ 請稍後再試，或點擊上方「手動更新」重新連線民間網站。")
        st.stop()

    latest_draw = df_history.iloc[0]['原始陣列']
    latest_super = df_history.iloc[0]['超級獎號']
    latest_period = df_history.iloc[0]['期數']
    latest_date = df_history.iloc[0].get('開獎時間', '')

    recent_30_arrays = df_history.head(30)['原始陣列'].tolist()
    counts_30 = {i: 0 for i in range(0 if "星彩" in game_name else 1, cfg["pool"] + 1)}
    for arr in recent_30_arrays:
        for num in arr: counts_30[num] += 1
    
    sorted_30 = sorted(counts_30.items(), key=lambda x: x[1], reverse=True)
    hot_top = sorted_30[:15]
    cold_top = sorted(counts_30.items(), key=lambda x: x[1])[:15] 

    gaps_30 = {i: 30 for i in range(0 if "星彩" in game_name else 1, cfg["pool"] + 1)}
    for idx, arr in enumerate(recent_30_arrays):
        for num in arr:
            if gaps_30[num] == 30: gaps_30[num] = idx
    overdue_top = sorted(gaps_30.items(), key=lambda x: x[1], reverse=True)[:15]

    # ======== 區塊一：最新開獎 ========
    st.header("📌 最新一期開獎結果")
    st.markdown(f"**第 {latest_period} 期** <span style='font-size:14px; color:#9ca3af;'>({latest_date})</span>", unsafe_allow_html=True)
    html_latest_balls = ""
    is_stars = game_name in ["三星彩", "四星彩"]
    for n in latest_draw:
        ball_text = f"{n}" if is_stars else f"{n:02d}"
        if n == latest_super and game_name == "賓果賓果":
            html_latest_balls += f"<div class='lottery-ball lottery-ball-super'>{ball_text}</div>"
        else:
            html_latest_balls += f"<div class='lottery-ball lottery-ball-latest'>{ball_text}</div>"
            
    if game_name == "大樂透" and latest_super is not None:
        html_latest_balls += f"<div style='display:inline-block; margin-left:10px; color:#fbbf24; font-weight:bold; line-height:40px;'>特別號：</div><div class='lottery-ball lottery-ball-super'>{latest_super:02d}</div>"
    elif game_name == "威力彩" and latest_super is not None:
        html_latest_balls += f"<div style='display:inline-block; margin-left:10px; color:#fbbf24; font-weight:bold; line-height:40px;'>第二區：</div><div class='lottery-ball lottery-ball-super'>{latest_super:02d}</div>"
        
    st.markdown(f"<div class='ball-container'>{html_latest_balls}</div>", unsafe_allow_html=True)
    st.markdown("---")

    # ======== 區塊二：AI 預測 ========
    st.header("🎯 策略型智慧號碼預測")
    
    if game_name == "賓果賓果":
        star_selection = st.selectbox("請選擇預測數量 (星數/碼數)：", [f"{i} 星" for i in range(1, 11)], index=2)
        star_num = int(star_selection.replace(" 星", ""))
    else:
        star_num = cfg["draws"]
        st.markdown(f"<div style='color: #60a5fa; font-size: 16px; font-weight: bold; margin-bottom: 15px;'>🎲 本彩種固定預測數量： {star_num} 碼</div>", unsafe_allow_html=True)

    col_b1, col_b2, col_b3, col_b4, col_b5 = st.columns(5)
    pred_type = None

    if col_b1.button("⚖️ 均衡選號", use_container_width=True, key="p1"): pred_type = "balanced"
    if col_b2.button("🔥 熱門號碼", use_container_width=True, key="p2"): pred_type = "hot"
    if col_b3.button("❄️ 冷門號碼", use_container_width=True, key="p3"): pred_type = "cold"
    if col_b4.button("🎲 隨機選號", use_container_width=True, key="p4"): pred_type = "random"
    if col_b5.button("⏳ 久未開出", use_container_width=True, key="p5"): pred_type = "overdue"

    if pred_type:
        with st.spinner("AI 核心演算法正在解析盤勢..."):
            time.sleep(0.5) 
            hot_pool = [item[0] for item in hot_top]
            cold_pool = [item[0] for item in cold_top]
            overdue_pool = [item[0] for item in overdue_top]
            
            is_digit = "星彩" in game_name
            
            if pred_type == "hot": predicted = random.choices(hot_pool, k=star_num) if is_digit else random.sample(hot_pool, min(star_num, len(hot_pool)))
            elif pred_type == "cold": predicted = random.choices(cold_pool, k=star_num) if is_digit else random.sample(cold_pool, min(star_num, len(cold_pool)))
            elif pred_type == "overdue": predicted = random.choices(overdue_pool, k=star_num) if is_digit else random.sample(overdue_pool, min(star_num, len(overdue_pool)))
            elif pred_type == "balanced":
                half = star_num // 2
                rem = star_num - half
                p_hot = random.choices(hot_pool, k=half) if is_digit else random.sample(hot_pool, min(half, len(hot_pool)))
                p_cold_pool = [x for x in cold_pool if x not in p_hot] if not is_digit else cold_pool
                p_cold = random.choices(p_cold_pool, k=rem) if is_digit else random.sample(p_cold_pool, min(rem, len(p_cold_pool)))
                predicted = p_hot + p_cold
            elif pred_type == "random":
                weights = [counts_30.get(x, 0) + 1 for x in range(0 if is_digit else 1, cfg["pool"] + 1)]
                if is_digit: predicted = random.choices(range(10), weights=weights, k=star_num)
                else:
                    drawn_set = set()
                    while len(drawn_set) < star_num:
                        res = random.choices(range(1, cfg["pool"] + 1), weights=weights, k=star_num - len(drawn_set))
                        drawn_set.update(res)
                    predicted = list(drawn_set)
                
            if not is_digit: predicted.sort()
            st.session_state.ai_predicted = predicted
            st.session_state.ai_star_num = star_num

    if st.session_state.ai_predicted:
        st.success(f"✅ 運算完成！為您推薦的 **{st.session_state.ai_star_num} 碼** 如下：")
        is_stars = game_name in ["三星彩", "四星彩"]
        html_pred_balls = "".join([f"<div class='lottery-ball'>{n if is_stars else f'{n:02d}'}</div>" for n in st.session_state.ai_predicted])
        st.markdown(f"<div class='ball-container'>{html_pred_balls}</div>", unsafe_allow_html=True)
    st.markdown("---")

    # ======== 區塊三：30 期統計 ========
    st.header("📊 最新 30 期開獎趨勢統計")
    
    consec_counts = Counter()
    for i in range(len(recent_30_arrays) - 1): 
        intersect = set(recent_30_arrays[i]).intersection(set(recent_30_arrays[i+1]))
        for n in intersect: consec_counts[n] += 1
    top_consec = consec_counts.most_common(10)

    top_double_consec = []
    if cfg["pool"] > 10:
        double_consec_counts = Counter()
        for i in range(len(recent_30_arrays) - 1):
            intersect = set(recent_30_arrays[i]).intersection(set(recent_30_arrays[i+1]))
            if len(intersect) >= 2:
                for pair in itertools.combinations(sorted(intersect), 2): double_consec_counts[pair] += 1
        top_double_consec = double_consec_counts.most_common(10)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔥 熱門", "❄️ 冷門", "🔁 連莊", "👯 雙連", "⏳ 遺漏"])
    with tab1: st.markdown(render_stat_balls(hot_top, "次"), unsafe_allow_html=True)
    with tab2: st.markdown(render_stat_balls(cold_top, "次", is_cold=True), unsafe_allow_html=True)
    with tab3: 
        if top_consec: st.markdown(render_stat_balls(top_consec, "次連莊"), unsafe_allow_html=True)
        else: st.info("近 30 期尚無連莊號碼。")
    with tab4:
        if top_double_consec: st.markdown(render_stat_balls(top_double_consec, "次連莊", is_double=True), unsafe_allow_html=True)
        else: st.info("本彩種近 30 期尚無雙連莊，或不適用雙連莊計算。")
    with tab5: st.markdown(render_stat_balls(overdue_top, "期", is_cold=True), unsafe_allow_html=True)
    st.markdown("---")

    # ======== 區塊四：歷史紀錄卡片 ========
    limit_period = 100 if game_name == "賓果賓果" else 50
    with st.expander(f"📋 展開查看 {game_name} 完整歷史明細 (近 {limit_period} 期)", expanded=False):
        history_cards_html = ""
        for idx, row in df_history.iterrows():
            nums = row['原始陣列']
            s_num = row['超級獎號']
            date_info = row.get('開獎時間', '')
            
            balls_html = ""
            is_stars = game_name in ["三星彩", "四星彩"]
            for n in nums:
                ball_text = f"{n}" if is_stars else f"{n:02d}"
                if n == s_num and game_name == "賓果賓果": 
                    balls_html += f"<div class='h-ball h-ball-super'>{ball_text}</div>"
                else: 
                    balls_html += f"<div class='h-ball'>{ball_text}</div>"
                    
            if game_name == "大樂透" and s_num is not None:
                balls_html += f"<div style='margin-left:8px; line-height:32px; color:#fbbf24; font-size:13px;'>特別號:</div><div class='h-ball h-ball-super'>{s_num:02d}</div>"
            elif game_name == "威力彩" and s_num is not None:
                balls_html += f"<div style='margin-left:8px; line-height:32px; color:#fbbf24; font-size:13px;'>二區:</div><div class='h-ball h-ball-super'>{s_num:02d}</div>"

            history_cards_html += f"""
            <div class='history-card'>
                <div class='history-header'>
                    <div class='history-period'>第 {row['期數']} 期 <span class='history-date'>{date_info}</span></div>
                </div>
                <div class='history-balls'>{balls_html}</div>
            </div>
            """
        st.markdown(history_cards_html, unsafe_allow_html=True)
    st.markdown("---")

    # ======== 區塊五：專屬玩法與規則 ========
    show_game_rules(game_name)

# --- 系統底層 ---
def show_footer():
    st.markdown("""
    <div style="background-color: #450a0a; border: 1px solid #991b1b; padding: 15px; border-radius: 8px; margin-top: 30px;">
        <p style="color: #fca5a5; font-size: 13px; font-weight: bold; margin-bottom: 5px;">⚠️ 網站免責聲明：</p>
        <p style="color: #fecaca; font-size: 12px; line-height: 1.6; margin: 0;">本站提供之預測號碼與大數據，均由 AI 演算法與真實歷史開獎計算得出。資訊僅供學術交流與娛樂參考，絕對不保證中獎機率。請保持理性投注。本站為獨立專案，與「台灣彩券」無任何官方關聯。</p>
    </div>
    """, unsafe_allow_html=True)
    
    tw_tz = timezone(timedelta(hours=8))
    try:
        file_mtime = os.path.getmtime(__file__)
        update_time = datetime.fromtimestamp(file_mtime, tw_tz).strftime("%Y-%m-%d %H:%M:%S")
    except:
        update_time = datetime.now(tw_tz).strftime("%Y-%m-%d %H:%M:%S")
    st.markdown(f"<div style='text-align: center; color: #6b7280; margin-top: 20px; font-size: 12px;'>系統最後更新時間：{update_time}</div>", unsafe_allow_html=True)
    
    st.markdown("<a href='#top-anchor' class='back-to-top' title='返回頂部'>⬆️</a>", unsafe_allow_html=True)

# --- 主程式路由控制器 ---
if st.session_state.current_game == "Home":
    show_home_page()
    show_footer()
else:
    show_game_page(st.session_state.current_game)
    show_footer()