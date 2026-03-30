“””
英文 RPG 後端
FastAPI + SQLite（不需要額外安裝資料庫，最簡單）
“””

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sqlite3
import json
import os
import anthropic
from datetime import datetime

# ══════════════════════════════════════

# 啟動 App

# ══════════════════════════════════════

app = FastAPI(title=“英文 RPG API”)

# 允許前端（手機瀏覽器）連線

app.add_middleware(
CORSMiddleware,
allow_origins=[”*”],
allow_methods=[”*”],
allow_headers=[”*”],
)

# Claude API（從環境變數讀取，不要寫死在程式裡）

CLAUDE_API_KEY = os.environ.get(“CLAUDE_API_KEY”, “”)

# ══════════════════════════════════════

# 資料庫初始化（自動建立）

# ══════════════════════════════════════

def init_db():
conn = sqlite3.connect(“rpg.db”)
c = conn.cursor()

```
# 用戶角色資料表
c.execute("""
    CREATE TABLE IF NOT EXISTS players (
        id TEXT PRIMARY KEY,
        name TEXT DEFAULT '英文勇者',
        level INTEGER DEFAULT 1,
        xp INTEGER DEFAULT 0,
        hp INTEGER DEFAULT 100,
        max_hp INTEGER DEFAULT 100,
        gold INTEGER DEFAULT 0,
        created_at TEXT
    )
""")

# 單字學習紀錄
c.execute("""
    CREATE TABLE IF NOT EXISTS vocab_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id TEXT,
        word TEXT,
        category TEXT,
        difficulty TEXT,
        correct_count INTEGER DEFAULT 0,
        wrong_count INTEGER DEFAULT 0,
        next_review TEXT,
        ease_factor REAL DEFAULT 2.5,
        interval_days INTEGER DEFAULT 1,
        last_reviewed TEXT
    )
""")

# 文法練習紀錄
c.execute("""
    CREATE TABLE IF NOT EXISTS grammar_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id TEXT,
        zone TEXT,
        question_type TEXT,
        correct INTEGER,
        answered_at TEXT
    )
""")

# 成就紀錄
c.execute("""
    CREATE TABLE IF NOT EXISTS achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id TEXT,
        achievement_key TEXT,
        earned_at TEXT
    )
""")

conn.commit()
conn.close()
```

init_db()

# ══════════════════════════════════════

# 資料模型（前端傳來的資料格式）

# ══════════════════════════════════════

class PlayerCreate(BaseModel):
player_id: str          # 用手機的唯一ID
name: Optional[str] = “英文勇者”

class AnswerSubmit(BaseModel):
player_id: str
zone: str               # 例如 “grammar-j”
question_type: str      # 例如 “時態”
correct: bool
xp_gained: int

class VocabReview(BaseModel):
player_id: str
word: str
category: str
difficulty: str
rating: str             # “again” / “hard” / “easy”

class AiQuestionRequest(BaseModel):
player_id: str
zone: str               # 哪個地圖（決定難度和主題）
weak_types: list[str]   # 最弱的題型（AI 會針對這個出題）

class AiTutorChat(BaseModel):
player_id: str
message: str
history: list[dict]     # 對話歷史

# ══════════════════════════════════════

# 工具函數

# ══════════════════════════════════════

def get_db():
return sqlite3.connect(“rpg.db”)

def get_player(player_id: str):
conn = get_db()
c = conn.cursor()
c.execute(“SELECT * FROM players WHERE id = ?”, (player_id,))
row = c.fetchone()
conn.close()
if not row:
return None
return {
“id”: row[0], “name”: row[1], “level”: row[2],
“xp”: row[3], “hp”: row[4], “max_hp”: row[5],
“gold”: row[6], “created_at”: row[7]
}

def calc_level(xp: int) -> int:
# 每升一級需要 500 × 當前等級 XP
level = 1
needed = 500
while xp >= needed:
xp -= needed
level += 1
needed = 500 * level
return level

# ══════════════════════════════════════

# API 路由

# ══════════════════════════════════════

# ── 健康檢查 ──

@app.get(”/”)
def root():
return {“status”: “英文 RPG 後端運行中 ⚔️”}

# ── 建立 / 取得玩家 ──

@app.post(”/player/create”)
def create_player(data: PlayerCreate):
conn = get_db()
c = conn.cursor()
# 如果已存在就直接回傳
existing = get_player(data.player_id)
if existing:
return {“success”: True, “player”: existing, “is_new”: False}
c.execute(
“INSERT INTO players (id, name, created_at) VALUES (?, ?, ?)”,
(data.player_id, data.name, datetime.now().isoformat())
)
conn.commit()
conn.close()
return {“success”: True, “player”: get_player(data.player_id), “is_new”: True}

@app.get(”/player/{player_id}”)
def get_player_api(player_id: str):
player = get_player(player_id)
if not player:
raise HTTPException(status_code=404, detail=“找不到玩家”)
return player

# ── 提交答題結果 ──

@app.post(”/answer/submit”)
def submit_answer(data: AnswerSubmit):
conn = get_db()
c = conn.cursor()

```
# 寫入答題紀錄
c.execute("""
    INSERT INTO grammar_records (player_id, zone, question_type, correct, answered_at)
    VALUES (?, ?, ?, ?, ?)
""", (data.player_id, data.zone, data.question_type,
      1 if data.correct else 0, datetime.now().isoformat()))

# 更新玩家 XP / 金幣
if data.correct:
    c.execute("""
        UPDATE players
        SET xp = xp + ?, gold = gold + 10
        WHERE id = ?
    """, (data.xp_gained, data.player_id))
else:
    # 答錯扣 HP
    c.execute("""
        UPDATE players
        SET hp = MAX(0, hp - 10)
        WHERE id = ?
    """, (data.player_id,))

# 重新計算等級
c.execute("SELECT xp FROM players WHERE id = ?", (data.player_id,))
row = c.fetchone()
if row:
    new_level = calc_level(row[0])
    c.execute("UPDATE players SET level = ? WHERE id = ?", (new_level, data.player_id))

conn.commit()
conn.close()

player = get_player(data.player_id)

# 檢查成就
achievements_earned = check_achievements(data.player_id)

return {
    "success": True,
    "player": player,
    "new_achievements": achievements_earned
}
```

# ── 分析弱點 ──

@app.get(”/analysis/{player_id}”)
def get_analysis(player_id: str):
conn = get_db()
c = conn.cursor()

```
# 各題型正確率
c.execute("""
    SELECT question_type,
           SUM(correct) as correct_count,
           COUNT(*) as total
    FROM grammar_records
    WHERE player_id = ?
    GROUP BY question_type
    ORDER BY (CAST(SUM(correct) AS REAL) / COUNT(*)) ASC
""", (player_id,))
rows = c.fetchall()
conn.close()

analysis = []
for row in rows:
    qtype, correct, total = row
    rate = round(correct / total * 100) if total > 0 else 0
    analysis.append({
        "type": qtype,
        "correct": correct,
        "total": total,
        "rate": rate,
        "status": "弱" if rate < 50 else "中" if rate < 75 else "強"
    })

weak_types = [a["type"] for a in analysis if a["rate"] < 60]

return {
    "analysis": analysis,
    "weak_types": weak_types,
    "suggestion": f"最需加強：{', '.join(weak_types[:3]) if weak_types else '繼續保持！'}"
}
```

# ── 單字間隔重複（SM-2 演算法）──

@app.post(”/vocab/review”)
def review_vocab(data: VocabReview):
conn = get_db()
c = conn.cursor()

```
# 查詢這個單字的紀錄
c.execute("""
    SELECT id, ease_factor, interval_days, correct_count, wrong_count
    FROM vocab_records
    WHERE player_id = ? AND word = ?
""", (data.player_id, data.word))
row = c.fetchone()

now = datetime.now().isoformat()

# SM-2 演算法計算下次複習時間
if data.rating == "again":
    quality = 1; interval = 1; ease_delta = -0.2
elif data.rating == "hard":
    quality = 3; interval = 3; ease_delta = -0.1
else:  # easy
    quality = 5; interval = 7; ease_delta = 0.1

if row:
    rec_id, ease, old_interval, correct_c, wrong_c = row
    new_ease = max(1.3, ease + ease_delta)
    if data.rating != "again":
        new_interval = max(1, int(old_interval * new_ease))
    else:
        new_interval = 1

    correct_c += 1 if data.rating == "easy" else 0
    wrong_c += 1 if data.rating == "again" else 0

    from datetime import datetime, timedelta
    next_review = (datetime.now() + timedelta(days=new_interval)).isoformat()

    c.execute("""
        UPDATE vocab_records
        SET ease_factor=?, interval_days=?, correct_count=?, wrong_count=?,
            next_review=?, last_reviewed=?
        WHERE id=?
    """, (new_ease, new_interval, correct_c, wrong_c, next_review, now, rec_id))
else:
    # 第一次學這個字
    from datetime import datetime, timedelta
    next_review = (datetime.now() + timedelta(days=interval)).isoformat()
    c.execute("""
        INSERT INTO vocab_records
        (player_id, word, category, difficulty, correct_count, wrong_count,
         next_review, ease_factor, interval_days, last_reviewed)
        VALUES (?, ?, ?, ?, ?, ?, ?, 2.5, ?, ?)
    """, (data.player_id, data.word, data.category, data.difficulty,
          1 if data.rating == "easy" else 0,
          1 if data.rating == "again" else 0,
          next_review, interval, now))

conn.commit()
conn.close()

return {"success": True, "next_review_days": interval}
```

# ── 今日待複習單字 ──

@app.get(”/vocab/due/{player_id}”)
def get_due_vocab(player_id: str):
conn = get_db()
c = conn.cursor()
now = datetime.now().isoformat()
c.execute(”””
SELECT word, category, difficulty, correct_count, wrong_count
FROM vocab_records
WHERE player_id = ? AND next_review <= ?
ORDER BY next_review ASC
LIMIT 20
“””, (player_id, now))
rows = c.fetchall()
conn.close()
return {
“due_count”: len(rows),
“words”: [{“word”: r[0], “category”: r[1], “difficulty”: r[2],
“correct”: r[3], “wrong”: r[4]} for r in rows]
}

# ── AI 動態出題（Claude API）──

@app.post(”/ai/generate-question”)
def generate_question(data: AiQuestionRequest):
if not CLAUDE_API_KEY:
raise HTTPException(status_code=500, detail=“未設定 CLAUDE_API_KEY”)

```
zone_info = {
    "grammar-j": "國中英文文法（時態、冠詞、代名詞、連接詞、比較級）",
    "grammar-h": "高中英文文法（假設語氣、分詞構句、倒裝句、關係子句）",
    "vocab-basic": "國高中核心英文單字（3000字範圍）",
    "vocab-medical": "醫學英文術語（學士後中醫考試相關）",
    "vocab-gre": "GRE 高階學術英文單字",
}

zone_desc = zone_info.get(data.zone, "國中英文")
weak_str = "、".join(data.weak_types) if data.weak_types else "一般"

prompt = f"""你是英文考題出題老師。請出一道{zone_desc}的選擇題。
```

玩家最弱的題型：{weak_str}，請針對這個出題。

必須以此 JSON 格式回答，不要有其他文字：
{{
“type”: “題型名稱（如：時態、假設語氣）”,
“question”: “題目（含空格用 ___ 表示）”,
“options”: [“選項A”, “選項B”, “選項C”, “選項D”],
“answer_index”: 正確選項的index（0-3的數字）,
“explanation”: “用繁體中文解釋為什麼選這個答案（50字以內）”
}}”””

```
client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=400,
    messages=[{"role": "user", "content": prompt}]
)

raw = response.content[0].text
# 清理並解析 JSON
raw = raw.strip().replace("```json", "").replace("```", "").strip()
question_data = json.loads(raw)

return {"success": True, "question": question_data}
```

# ── AI 家教對話（Claude API）──

@app.post(”/ai/tutor”)
def ai_tutor(data: AiTutorChat):
if not CLAUDE_API_KEY:
raise HTTPException(status_code=500, detail=“未設定 CLAUDE_API_KEY”)

```
# 取得玩家分析作為 context
conn = get_db()
c = conn.cursor()
c.execute("""
    SELECT question_type, ROUND(CAST(SUM(correct) AS REAL)/COUNT(*)*100) as rate
    FROM grammar_records WHERE player_id = ?
    GROUP BY question_type ORDER BY rate ASC LIMIT 3
""", (data.player_id,))
weak_rows = c.fetchall()
conn.close()

weak_info = "、".join([f"{r[0]}（{r[1]}%）" for r in weak_rows]) if weak_rows else "尚無紀錄"

system = f"""你是一位專業英文老師，幫助學生從國中程度提升到學士後中醫考試英文程度。
```

學生弱點：{weak_info}
請用繁體中文說明，英文舉例。回答簡潔易懂，適合手機閱讀。
遇到單字給音標和例句。遇到文法給公式和例子。”””

```
client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=600,
    system=system,
    messages=data.history + [{"role": "user", "content": data.message}]
)

return {"reply": response.content[0].text}
```

# ── 成就系統 ──

def check_achievements(player_id: str) -> list:
conn = get_db()
c = conn.cursor()

```
earned = []

# 查詢已有成就
c.execute("SELECT achievement_key FROM achievements WHERE player_id = ?", (player_id,))
existing = {row[0] for row in c.fetchall()}

# 查詢統計
c.execute("SELECT COUNT(*), SUM(correct) FROM grammar_records WHERE player_id = ?", (player_id,))
total_q, total_correct = c.fetchone()
total_q = total_q or 0
total_correct = total_correct or 0

player = get_player(player_id)

# 定義成就條件
checks = [
    ("first_answer", total_q >= 1, "第一步"),
    ("ten_correct", total_correct >= 10, "連勝初學者"),
    ("hundred_correct", total_correct >= 100, "文法戰士"),
    ("level_5", player and player["level"] >= 5, "升到5級"),
    ("level_10", player and player["level"] >= 10, "升到10級"),
]

now = datetime.now().isoformat()
for key, condition, name in checks:
    if condition and key not in existing:
        c.execute(
            "INSERT INTO achievements (player_id, achievement_key, earned_at) VALUES (?, ?, ?)",
            (player_id, key, now)
        )
        earned.append({"key": key, "name": name})

conn.commit()
conn.close()
return earned
```

@app.get(”/achievements/{player_id}”)
def get_achievements(player_id: str):
conn = get_db()
c = conn.cursor()
c.execute(“SELECT achievement_key, earned_at FROM achievements WHERE player_id = ?”, (player_id,))
rows = c.fetchall()
conn.close()
return {“achievements”: [{“key”: r[0], “earned_at”: r[1]} for r in rows]}
