import streamlit as st
import csv
import random
import pandas as pd

# --- 1. 基本ロジック（ここが抜けていた可能性があります） ---

def load_players_from_file(uploaded_file):
    players = []
    content = uploaded_file.read().decode("utf-8").splitlines()
    reader = csv.DictReader(content)
    for row in reader:
        players.append({
            "name": row["名前"],
            "gender": "M" if row["性別"] in ["男"] else "F",
            "grade": int(row["学年"]),
            "skill": int(row["経験者度"]),
            "matches": 0, "mix_count": 0, "same_count": 0,
            "partners": set(), "opponents": set()
        })
    return players

def split_red_white(players):
    groups = {}
    for p in players:
        skill_band = 1 if p["skill"] <= 2 else 2
        key = (p["gender"], skill_band)
        groups.setdefault(key, []).append(p)
    red, white = [], []
    for key, group in groups.items():
        group = sorted(group, key=lambda p: (-p["grade"], p["skill"]))
        random.shuffle(group)

        mid = len(group) // 2
        red.extend(group[:mid]); white.extend(group[mid:])
    return red, white

def make_pairs_by_count(team, mix_count, md_count, fd_count, fixed_pairs=None, ng_pairs=None):
    # 個別ペア配慮（指定されたペアを優先的に固定）
    used_names = set()
    pairs = []
    if ng_pairs is None:
        ng_pairs = []
    
    # 固定ペアの処理
    if fixed_pairs:
        for p1_name, p2_name in fixed_pairs:
            p1 = next((p for p in team if p["name"] == p1_name), None)
            p2 = next((p for p in team if p["name"] == p2_name), None)
            if p1 and p2 and p1["name"] not in used_names and p2["name"] not in used_names:
                pairs.append((p1, p2))
                used_names.update([p1["name"], p2["name"]])
                for p in [p1, p2]: p["matches"] += 1
    
    males = [p for p in team if p["gender"] == "M" and p["name"] not in used_names]
    females = [p for p in team if p["gender"] == "F" and p["name"] not in used_names]

    #【女子ダブルス優先】
    females.sort(key=lambda p: (p["same_count"], random.random()))
    current_fd = sum(1 for a, b in pairs if a["gender"] == "F" and b["gender"] == "F")
    
    while current_fd < fd_count and len(females) >= 2:
        p1 = females.pop(0)
        p2 = females.pop(0)
        pairs.append((p1, p2))
        used_names.update([p1["name"], p2["name"]])
        for p in [p1, p2]: 
            p["same_count"] += 1
            p["matches"] += 1
        current_fd += 1

    #【ミックスダブルス】
    males.sort(key=lambda p: (p["mix_count"], random.random()))
    current_mix = 0
    for m in males[:]:
        if current_mix >= mix_count or not females: break
        # パートナー未経験・実力差を考慮してソート
        candidates = sorted(females, key=lambda f: (f["mix_count"], f["name"] in m["partners"], abs(f["skill"] - m["skill"])))
        # NGペアは除外
        candidates = [f for f in candidates if (m["name"], f["name"]) not in ng_pairs and (f["name"], m["name"]) not in ng_pairs]
        if not candidates:
            continue
        f = candidates[0]
        pairs.append((m, f))
        males.remove(m)
        females.remove(f)
        used_names.update([m["name"], f["name"]])
        for p in [m, f]: 
            p["mix_count"] += 1
            p["matches"] += 1
        current_mix += 1

    #【男子ダブルス】（余った男子で作成）
    males.sort(key=lambda p: (p["same_count"], random.random()))
    while len(males) >= 2:
        p1 = males.pop(0)
        p2 = males.pop(0)
        pairs.append((p1, p2))
        used_names.update([p1["name"], p2["name"]])
        for p in [p1, p2]: 
            p["same_count"] += 1
            p["matches"] += 1

    return pairs

def match_pairs(red_pairs, white_pairs, courts):
    matches = []
    for i in range(courts):
        if i < len(red_pairs) and i < len(white_pairs):
            matches.append((red_pairs[i], white_pairs[i]))
        else:
            matches.append((None, None))
    return matches
# --- 2. Streamlit UI部分 ---

def main():
    st.set_page_config(page_title="LaissezFaire T.C", layout="wide")
    st.title("🎾 紅白戦オーダー管理システム")

    st.sidebar.header("1. 準備")
    uploaded_file = st.sidebar.file_uploader("CSVファイルをアップロード", type="csv")
    rounds_num = st.sidebar.number_input("ラウンド数", min_value=1, value=6)
    courts_num = st.sidebar.number_input("コート数", min_value=1, value=6)
    
    st.sidebar.header("2. 個別ペア配慮")
    fixed_pair_input = st.sidebar.text_input("固定したいペア（例: 田中,佐藤）", "")

    ng_pair_input = st.sidebar.text_input("共演NGペア（例: 田中,佐藤）", "")
    ng_pairs = [ng_pair_input.split(",")] if ng_pair_input and "," in ng_pair_input else []

    if uploaded_file:
        if st.sidebar.button("オーダーを生成・更新"):
            #初期化
            players = load_players_from_file(uploaded_file)
            red, white = split_red_white(players)

            # 固定ペアの解析
            fixed_pairs = [fixed_pair_input.split(",")] if fixed_pair_input and "," in fixed_pair_input else []
            
            full_order = []
            for r in range(rounds_num):
                # 女子ダブルス枠を最低1つ以上確保するロジック
                fd_needed = 1 if r % 2 == 0 else 0 
                mix_needed = courts_num - fd_needed
                
                rp = make_pairs_by_count(red, mix_needed, 0, fd_needed, fixed_pairs, ng_pairs)
                wp = make_pairs_by_count(white, mix_needed, 0, fd_needed, fixed_pairs, ng_pairs)

                matches = match_pairs(rp, wp, courts_num)
                full_order.append(matches)
            
            st.session_state.red = red
            st.session_state.white = white
            st.session_state.full_order = full_order
            st.success("オーダー生成完了！")

        if 'full_order' in st.session_state:
            tab1, tab2, tab3 = st.tabs(["📋 全体オーダー表", "🔍 個人検索", "🚩 チーム分け"])
            
            with tab1:
                st.header("📋 試合オーダー表")

                # ラウンドごとにループ
                for r, matches in enumerate(st.session_state.full_order):
                    # 各ラウンドを折りたたみメニューにする（スッキリ見せるため）
                    with st.expander(f"📍 Round {r+1}", expanded=(r==0)):
                        # 1行に3枚のカードを並べる
                        cols = st.columns(3)
                        for i, m in enumerate(matches):
                            col_idx = i % 3
                            with cols[col_idx]:
                                # HTMLを使って「枠」と「VS」をデザイン
                                st.markdown(f"""
                                <div style="
                                    border: 2px solid #4E79A7; 
                                    border-radius: 12px; 
                                    padding: 15px; 
                                    margin-bottom: 20px; 
                                    background-color: #FFFFFF; 
                                    box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
                                    text-align: center;
                                ">
                                    <div style="background-color: #4E79A7; color: white; border-radius: 5px; margin-bottom: 10px; font-weight: bold;">
                                        Court {i+1}
                                    </div>
                                    <div style="font-size: 1.1em; font-weight: bold; color: #333;">
                                        {m[0][0]['name']}<br>{m[0][1]['name']}
                                    </div>
                                    <div style="margin: 8px 0; color: #E15759; font-size: 1.2em; font-weight: 900;">
                                        VS
                                    </div>
                                    <div style="font-size: 1.1em; font-weight: bold; color: #333;">
                                        {m[1][0]['name']}<br>{m[1][1]['name']}
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
            
            with tab2:
                st.header("個人検索")
                search_text = st.text_input("名前の一部を入力")
                if search_text:
                    all_players = st.session_state.red + st.session_state.white
                    matched = [p for p in all_players if search_text in p['name']]
                    if matched:
                        target_name = st.selectbox("対象者を選択:", [p['name'] for p in matched]) if len(matched) > 1 else matched[0]['name']
                        st.subheader(f"【{target_name} さんの予定】")

                        team_color = "紅" if any(p['name'] == target_name for p in st.session_state.red) else "白"
                        st.write(f"### {target_name} さんは **{team_color}組** です")

                        found_any = False
                        for r, m_in_r in enumerate(st.session_state.full_order):
                            for c, m in enumerate(m_in_r):
                                if any(p['name'] == target_name for p in m[0] + m[1]):
                                    found_any = True
                                    is_red = any(p['name'] == target_name for p in m[0])
                                    my_t, opp_t = (m[0], m[1]) if is_red else (m[1], m[0])
                                    partner = next(p['name'] for p in my_t if p['name'] != target_name)
                                    st.write(f"**R{r+1} C{c+1}**: {partner} とペア / 相手: {opp_t[0]['name']}, {opp_t[1]['name']}")
                        if not found_any:
                            st.info("このラウンドでの試合はありません。")
                    else:
                        st.warning("該当するプレイヤーが見つかりません。")
            with tab3:
                st.header("🚩 紅白チーム分け一覧")
                col_r, col_w = st.columns(2)
                with col_r:
                    st.subheader("🔴 紅組")
                    st.write("\n ".join([f" ・{p['name']}" for p in st.session_state.red]))
                with col_w:
                    st.subheader("⚪ 白組")
                    st.write("\n ".join([f" ・{p['name']}" for p in st.session_state.white]))
    else:
        st.info("サイドバーからCSVファイルをアップロードしてください。")

if __name__ == "__main__":
    main()