import random
import csv

# -----------------------------
# Step 1: プレイヤーのデータの読み込み
# -----------------------------
def load_players(csv_path):
    players = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            players.append({
                "name": row["名前"],
                "grade": int(row["学年"]),
                "gender": "M" if row["性別"] in ["男"] else "F",
                "skill": int(row["経験者度"]),
                "matches": 0,        # 出場試合数
                "partners": set(),   # 組んだことのある相手
                "opponents": set(),  # 対戦したことのある相手
                "mix_count": 0,      # ミックスの回数
                "same_count": 0,     # 同性ダブルスの回数
            })
    return players

# ----------------------------
# Step 2: ペア構成を決める
# -----------------------------
def count_gender(players):
    num_male = sum(1 for p in players if p["gender"] == "M")
    num_female = sum(1 for p in players if p["gender"] == "F")
    return num_male, num_female

# ----------------------------
# Step 2: 紅白に分ける
# -----------------------------
def split_red_white(players):
    # 学年 × 性別 × skill のグループに分ける
    groups = {}
    for p in players:
        key = (p["gender"], p["grade"], p["skill"])
        groups.setdefault(key, []).append(p)

    red = []
    white = []

    # 各グループを半分ずつ紅白に分ける
    for key, group in groups.items():
        random.shuffle(group)
        mid = len(group) // 2
        red.extend(group[:mid])
        white.extend(group[mid:])

    # 最後に軽くシャッフル
    random.shuffle(red)
    random.shuffle(white)

    return red, white

# -----------------------------
# Step 3: ペアを作る関数
# -----------------------------

def shuffle_by_skill(players):
    groups = {}
    for p in players:
        groups.setdefault(p["skill"], []).append(p)

    result = []
    for skill, group in groups.items():
        random.shuffle(group)
        result.extend(group)

    return result

def sort_female_for_fd(females):
    # same_count → matches → skill帯シャッフル の順で優先
    # まず skill帯シャッフル
    females = shuffle_by_skill(females)

    # 次に same_count と matches で優先度ソート
    females.sort(key=lambda p: (p["same_count"], p["matches"]))

    return females

def decide_pair_counts(team, courts):
    males = sum(1 for p in team if p["gender"] == "M")
    females = sum(1 for p in team if p["gender"] == "F")

    # FD を最低1本作るために女子2人は残す
    max_mix = min(males, females)

    # ミックスは作れるだけ作る
    mix = min(max_mix, courts)

    # ミックスで使った人数を引く
    males -= mix
    females -= mix

    remaining = courts - mix

    # 男ダブ（男子2人で1ペア）
    md = min(males // 2, remaining)
    remaining -= md

    # 女ダブ（女子2人で1ペア）
    fd = min(females // 2, remaining)
    remaining -= fd

    return {
        "mix": mix,
        "md": md,
        "fd": fd
    }

def make_pairs_by_count(team, mix_count, md_count, fd_count):
    males = shuffle_by_skill([p for p in team if p["gender"] == "M"])
    females = shuffle_by_skill([p for p in team if p["gender"] == "F"])

    pairs = []
    used_m = set()
    used_f = set()

    # ミックス
    males.sort(key=lambda p: (p["mix_count"], random.random()))
    for m in males:
        if len(pairs) >= mix_count:
            break
        if m["name"] in used_m:
            continue

        candidates = sorted([f for f in females if f["name"] not in used_f], 
                            key=lambda f: (f["mix_count"], f["name"] in m["partners"], abs(f["skill"] - m["skill"])))
        
        # 候補がいる場合のみペアを確定させる
        if candidates:
            f = candidates[0]  # 一番条件に合う人を f とする

            # ミックスのペアが決まった直後
            pairs.append((m, f))
            used_m.add(m["name"])
            used_f.add(f["name"])

            # --- ここを追加 ---
            m["partners"].add(f["name"])
            f["partners"].add(m["name"])
            # ------------------
            m["mix_count"] += 1
            f["mix_count"] += 1
            m["matches"] += 1
            f["matches"] += 1

    # まだ使っていない男子をリスト化
    md_pool = [p for p in males if p["name"] not in used_m]
    # 安全にペアを作る（i+1 が範囲内かチェック）
    for i in range(0, md_count * 2, 2):
        if i + 1 < len(md_pool):
            p1, p2 = md_pool[i], md_pool[i+1]
            pairs.append((p1, p2))
            p1["same_count"] += 1; p2["same_count"] += 1
            p1["matches"] += 1; p2["matches"] += 1
            p1["partners"].add(p2["name"]); p2["partners"].add(p1["name"])

    # ★ここで確実に定義する（エラー回避ポイント）
    fd_pool = [p for p in females if p["name"] not in used_f]
    fd_pool.sort(key=lambda p: (p["same_count"], p["matches"]))
    
    for i in range(0, fd_count * 2, 2):
        if i + 1 < len(fd_pool):
            p1, p2 = fd_pool[i], fd_pool[i+1]
            pairs.append((p1, p2))
            p1["same_count"] += 1; p2["same_count"] += 1
            p1["matches"] += 1; p2["matches"] += 1
            p1["partners"].add(p2["name"]); p2["partners"].add(p1["name"])


    return pairs


def classify_pair(pair):
    a, b = pair
    if a["gender"] == "M" and b["gender"] == "M":
        return "MD"  # 男ダブ
    if a["gender"] == "F" and b["gender"] == "F":
        return "FD"  # 女ダブ
    return "MX"      # ミックス

def group_pairs_by_type(pairs):
    groups = {"MD": [], "FD": [], "MX": []}
    for p in pairs:
        t = classify_pair(p)
        groups[t].append(p)
    return groups

def match_pairs(red_pairs, white_pairs):
    def get_gp(ps):
        return {
            "MD": [p for p in ps if p[0]["gender"] == "M" and p[1]["gender"] == "M"],
            "FD": [p for p in ps if p[0]["gender"] == "F" and p[1]["gender"] == "F"],
            "MX": [p for p in ps if p[0]["gender"] != p[1]["gender"]]
        }
    
    # ここで r_g と w_g を定義します
    r_g = get_gp(red_pairs)
    w_g = get_gp(white_pairs)
    
    matches = []
    for t in ["MD", "FD", "MX"]:
        for i in range(min(len(r_g[t]), len(w_g[t]))):
            matches.append((r_g[t][i], w_g[t][i]))
            
            # 対戦相手履歴の更新（追加した部分）
            r_pair, w_pair = r_g[t][i], w_g[t][i]
            for rp in r_pair:
                for wp in w_pair:
                    rp["opponents"].add(wp["name"])
                    wp["opponents"].add(rp["name"])
    return matches

def all_females_fd_done(players):
    females = [p for p in players if p["gender"] == "F"]
    return all(p["same_count"] >= 1 for p in females)

def decide_fd_priority_counts(team, courts):
    males_count = sum(1 for p in team if p["gender"] == "M")
    females_count = sum(1 for p in team if p["gender"] == "F")

    # 1. 女子で作れる最大ペア数
    max_fd_possible = females_count // 2
    
    # 2. 運営上の上限（コートの半分）
    op_limit = courts // 2
    
    # 3. FDの確定数：女子の最大数と運営上限の、どちらか小さい方
    fd = min(max_fd_possible, op_limit)
    
    # 4. 残りのコートを男子ダブルスで埋める
    remaining_courts = courts - fd
    md = min(males_count // 2, remaining_courts)
    
    # 5. それでもコートが余る、あるいは男子が足りない場合はミックス
    # (合計人数が足りていれば、ここで残りのコートが埋まる)
    mix = courts - (fd + md)

    return {
        "mix": max(0, mix), 
        "md": md, 
        "fd": fd
    }


# -----------------------------
# Step 4: 実行
# -----------------------------
def main():
    # ラウンド数とコート数を手入力
    rounds = int(input("ラウンド数を入力してください: "))
    courts = int(input("コート数を入力してください: "))

    players = load_players("eapajio.GW.csv")
    # 紅白分け（経験者度 × 性別）
    red, white = split_red_white(players)

    # 空のオーダー表（ラウンド × コート）
    order = create_empty_order(rounds=rounds, courts=courts)

    fd_mode = True

    # roundsラウンド自動生成
    for r in range(rounds):

        random.shuffle(red)
        random.shuffle(white)

        # 女子が全員 FD を終えたら通常モードに切り替え
        if fd_mode:
            if all_females_fd_done(red + white):
                fd_mode = False

        if fd_mode:
            # 女子ダブルス優先モード
            red_counts = decide_fd_priority_counts(red, courts)
            white_counts = decide_fd_priority_counts(white, courts)
        else:
            # 通常モード（ミックス＋MD＋FD）
            red_counts = decide_pair_counts(red, courts)
            white_counts = decide_pair_counts(white, courts)


        # ペア生成
        red_pairs = make_pairs_by_count(
            red,
            red_counts["mix"],
            red_counts["md"],
            red_counts["fd"]
        )

        white_pairs = make_pairs_by_count(
            white,
            white_counts["mix"],
            white_counts["md"],
            white_counts["fd"]
        )

        matches = match_pairs(red_pairs, white_pairs)

        for c, m in enumerate(matches):
            if c < courts:
                order[r][c] = m
    # 1. 試合オーダー表の表示（Markdown形式）
    print("\n## 試合オーダー表")
    header = "| Round | " + " | ".join([f"Court {i+1}" for i in range(courts)]) + " |"
    print(header)
    print("|" + "---|" * (courts + 1))
    
    for r in range(rounds):
        row = f"| {r+1} | "
        for c in range(courts):
            if order[r][c]:
                (r1, r2), (w1, w2) = order[r][c]
                row += f"{r1['name']}-{r2['name']} vs {w1['name']}-{w2['name']} | "
            else:
                row += " - | "
        print(row)

    # 2. 個人検索機能（アプリ化を見据えたUI設計）
    while True:
        print("\n" + "="*30)
        input_text = input("検索（名前の一部・名字など）Enterで終了: ").strip()
        if not input_text:
            break
            
        # STEP 1: 全プレイヤーの中から「部分一致」する人を抽出
        all_players = red + white
        matched_players = [p for p in all_players if input_text in p['name']]

        if not matched_players:
            print(f"× 「{input_text}」に一致する人は見つかりませんでした。")
            continue

        # STEP 2: 対象を1人に絞り込む（複数ヒット時の処理）
        target_player_name = ""
        if len(matched_players) > 1:
            print(f"\n「{input_text}」で {len(matched_players)} 名がヒットしました。番号を選んでください:")
            for i, p in enumerate(matched_players):
                # 判別しやすくするために性別や学年を添えてもOK
                print(f"{i + 1}: {p['name']} ({'男' if p['gender']=='M' else '女'}/{p['grade']}年)")
            
            sel = input("番号を選択 (キャンセルはそのままEnter): ")
            if not sel or not sel.isdigit() or not (1 <= int(sel) <= len(matched_players)):
                continue
            target_player_name = matched_players[int(sel) - 1]['name']
        else:
            # 1人しかいない場合はそのまま確定
            target_player_name = matched_players[0]['name']

        # STEP 3: 確定した個人のスケジュールを出力
        print(f"\n--- 【{target_player_name} さんのスケジュール】 ---")
        found_match = False
        for r in range(rounds):
            for c in range(courts):
                if order[r][c]:
                    red_pair, white_pair = order[r][c]
                    all_p_in_match = red_pair + white_pair
                    
                    if any(p['name'] == target_player_name for p in all_p_in_match):
                        found_match = True
                        # ペアと対戦相手の仕分け
                        is_red = any(p['name'] == target_player_name for p in red_pair)
                        my_team = red_pair if is_red else white_pair
                        opp_team = white_pair if is_red else red_pair
                        
                        partner = next(p['name'] for p in my_team if p['name'] != target_player_name)
                        opps = [p['name'] for p in opp_team]
                        print(f"R{r+1} Court{c+1}: [ペア] {partner} vs [相手] {opps[0]}, {opps[1]}")
        
        if not found_match:
            print("本日の試合予定はありません。")


    # 表示
    print_order_table(order=order, rounds=rounds, courts=courts)

    stats = {p["name"]: {"MD/FD": p["same_count"], "MIX": p["mix_count"]} for p in players}
    import json
    print(json.dumps(stats, indent=2, ensure_ascii=False))

# -----------------------------
# Step 4: 実行
# -----------------------------
def print_order_table(order, rounds, courts):
    """
    order は以下の形式のリストを想定：
    order[round][court] = (red_pair, white_pair)
    まだ中身がない場合は None を入れておく
    """
    for r in range(rounds):
        print(f"\n=== Round {r+1} ===")
        for c in range(courts):
            if order[r][c] is not None:
                red, white = order[r][c]
                red_names = f"{red[0]['name']} - {red[1]['name']}"
                white_names = f"{white[0]['name']} - {white[1]['name']}"
                print(f"Court {c+1}: {red_names} vs {white_names}")
            else:
                print(f"Court {c+1}: ")

def create_empty_order(rounds, courts):
    return [[None for _ in range(courts)] for _ in range(rounds)]

# 実行
if __name__ == "__main__":
    main()