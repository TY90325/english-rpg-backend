from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sqlite3
import json
import os
import anthropic
from datetime import datetime, timedelta

app = FastAPI(title=“English RPG API”)

app.add_middleware(
CORSMiddleware,
allow_origins=[”*”],
allow_methods=[”*”],
allow_headers=[”*”],
)

CLAUDE_API_KEY = os.environ.get(“CLAUDE_API_KEY”, “”)

def init_db():
conn = sqlite3.connect(“rpg.db”)
c = conn.cursor()
c.execute(”””
CREATE TABLE IF NOT EXISTS players (
id TEXT PRIMARY KEY,
name TEXT DEFAULT ‘Hero’,
level INTEGER DEFAULT 1,
xp INTEGER DEFAULT 0,
hp INTEGER DEFAULT 100,
max_hp INTEGER DEFAULT 100,
gold INTEGER DEFAULT 0,
created_at TEXT
)
“””)
c.execute(”””
CREATE TABLE IF NOT EXISTS grammar_records (
id INTEGER PRIMARY KEY AUTOINCREMENT,
player_id TEXT,
zone TEXT,
question_type TEXT,
correct INTEGER,
answered_at TEXT
)
“””)
c.execute(”””
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
“””)
c.execute(”””
CREATE TABLE IF NOT EXISTS achievements (
id INTEGER PRIMARY KEY AUTOINCREMENT,
player_id TEXT,
achievement_key TEXT,
earned_at TEXT
)
“””)
conn.commit()
conn.close()

init_db()

class PlayerCreate(BaseModel):
player_id: str
name: Optional[str] = “Hero”

class AnswerSubmit(BaseModel):
player_id: str
zone: str
question_type: str
correct: bool
xp_gained: int

class VocabReview(BaseModel):
player_id: str
word: str
category: str
difficulty: str
rating: str

class AiQuestionRequest(BaseModel):
player_id: str
zone: str
weak_types: list[str]

class AiTutorChat(BaseModel):
player_id: str
message: str
history: list[dict]

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
level = 1
needed = 500
while xp >= needed:
xp -= needed
level += 1
needed = 500 * level
return level

@app.get(”/”)
def root():
return {“status”: “English RPG backend running”}

@app.post(”/player/create”)
def create_player(data: PlayerCreate):
existing = get_player(data.player_id)
if existing:
return {“success”: True, “player”: existing, “is_new”: False}
conn = get_db()
c = conn.cursor()
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
raise HTTPException(status_code=404, detail=“Player not found”)
return player

@app.post(”/answer/submit”)
def submit_answer(data: AnswerSubmit):
conn = get_db()
c = conn.cursor()
c.execute(”””
INSERT INTO grammar_records (player_id, zone, question_type, correct, answered_at)
VALUES (?, ?, ?, ?, ?)
“””, (data.player_id, data.zone, data.question_type,
1 if data.correct else 0, datetime.now().isoformat()))
if data.correct:
c.execute(“UPDATE players SET xp = xp + ?, gold = gold + 10 WHERE id = ?”,
(data.xp_gained, data.player_id))
else:
c.execute(“UPDATE players SET hp = MAX(0, hp - 10) WHERE id = ?”, (data.player_id,))
c.execute(“SELECT xp FROM players WHERE id = ?”, (data.player_id,))
row = c.fetchone()
if row:
new_level = calc_level(row[0])
c.execute(“UPDATE players SET level = ? WHERE id = ?”, (new_level, data.player_id))
conn.commit()
conn.close()
return {“success”: True, “player”: get_player(data.player_id), “new_achievements”: check_achievements(data.player_id)}

@app.get(”/analysis/{player_id}”)
def get_analysis(player_id: str):
conn = get_db()
c = conn.cursor()
c.execute(”””
SELECT question_type, SUM(correct) as cc, COUNT(*) as total
FROM grammar_records WHERE player_id = ?
GROUP BY question_type ORDER BY (CAST(SUM(correct) AS REAL) / COUNT(*)) ASC
“””, (player_id,))
rows = c.fetchall()
conn.close()
analysis = []
for row in rows:
qtype, correct, total = row
rate = round(correct / total * 100) if total > 0 else 0
analysis.append({“type”: qtype, “correct”: correct, “total”: total, “rate”: rate})
weak_types = [a[“type”] for a in analysis if a[“rate”] < 60]
return {“analysis”: analysis, “weak_types”: weak_types}

@app.post(”/vocab/review”)
def review_vocab(data: VocabReview):
conn = get_db()
c = conn.cursor()
c.execute(“SELECT id, ease_factor, interval_days, correct_count, wrong_count FROM vocab_records WHERE player_id = ? AND word = ?”,
(data.player_id, data.word))
row = c.fetchone()
now = datetime.now().isoformat()
interval = 1 if data.rating == “again” else 3 if data.rating == “hard” else 7
ease_delta = -0.2 if data.rating == “again” else -0.1 if data.rating == “hard” else 0.1
if row:
rec_id, ease, old_interval, cc, wc = row
new_ease = max(1.3, ease + ease_delta)
new_interval = 1 if data.rating == “again” else max(1, int(old_interval * new_ease))
next_review = (datetime.now() + timedelta(days=new_interval)).isoformat()
c.execute(“UPDATE vocab_records SET ease_factor=?, interval_days=?, correct_count=?, wrong_count=?, next_review=?, last_reviewed=? WHERE id=?”,
(new_ease, new_interval, cc + (1 if data.rating == “easy” else 0), wc + (1 if data.rating == “again” else 0), next_review, now, rec_id))
else:
next_review = (datetime.now() + timedelta(days=interval)).isoformat()
c.execute(“INSERT INTO vocab_records (player_id, word, category, difficulty, correct_count, wrong_count, next_review, ease_factor, interval_days, last_reviewed) VALUES (?, ?, ?, ?, ?, ?, ?, 2.5, ?, ?)”,
(data.player_id, data.word, data.category, data.difficulty,
1 if data.rating == “easy” else 0, 1 if data.rating == “again” else 0, next_review, interval, now))
conn.commit()
conn.close()
return {“success”: True, “next_review_days”: interval}

@app.get(”/vocab/due/{player_id}”)
def get_due_vocab(player_id: str):
conn = get_db()
c = conn.cursor()
now = datetime.now().isoformat()
c.execute(“SELECT word, category, difficulty, correct_count, wrong_count FROM vocab_records WHERE player_id = ? AND next_review <= ? ORDER BY next_review ASC LIMIT 20”,
(player_id, now))
rows = c.fetchall()
conn.close()
return {“due_count”: len(rows), “words”: [{“word”: r[0], “category”: r[1], “difficulty”: r[2]} for r in rows]}

@app.post(”/ai/generate-question”)
def generate_question(data: AiQuestionRequest):
if not CLAUDE_API_KEY:
raise HTTPException(status_code=500, detail=“CLAUDE_API_KEY not set”)
zone_info = {
“grammar-j”: “junior high English grammar (tenses, articles, pronouns)”,
“grammar-h”: “senior high English grammar (subjunctive, participial phrases, inversion)”,
“vocab-basic”: “common junior/senior high school English vocabulary”,
“vocab-medical”: “medical English for Taiwan TCM exam”,
“vocab-gre”: “GRE level advanced academic vocabulary”,
}
zone_desc = zone_info.get(data.zone, “junior high English”)
weak_str = “, “.join(data.weak_types) if data.weak_types else “general”
prompt = ’Create one multiple choice question about ’ + zone_desc + ’. Student weak areas: ’ + weak_str + ‘. Reply ONLY with this JSON: {“type”: “type in Chinese”, “question”: “question with ___ for blank”, “options”: [“A”, “B”, “C”, “D”], “answer_index”: 0, “explanation”: “explanation in Traditional Chinese under 50 chars”}’
client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
response = client.messages.create(
model=“claude-sonnet-4-6”,
max_tokens=400,
messages=[{“role”: “user”, “content”: prompt}]
)
raw = response.content[0].text.strip().replace(”`json", "").replace("`”, “”).strip()
return {“success”: True, “question”: json.loads(raw)}

@app.post(”/ai/tutor”)
def ai_tutor(data: AiTutorChat):
if not CLAUDE_API_KEY:
raise HTTPException(status_code=500, detail=“CLAUDE_API_KEY not set”)
client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
response = client.messages.create(
model=“claude-sonnet-4-6”,
max_tokens=600,
system=“You are an English teacher for Taiwanese students preparing for the bachelor TCM exam. Reply in Traditional Chinese with English examples. Keep responses concise.”,
messages=data.history + [{“role”: “user”, “content”: data.message}]
)
return {“reply”: response.content[0].text}

def check_achievements(player_id: str) -> list:
conn = get_db()
c = conn.cursor()
earned = []
c.execute(“SELECT achievement_key FROM achievements WHERE player_id = ?”, (player_id,))
existing = {row[0] for row in c.fetchall()}
c.execute(“SELECT COUNT(*), SUM(correct) FROM grammar_records WHERE player_id = ?”, (player_id,))
total_q, total_correct = c.fetchone()
total_q = total_q or 0
total_correct = total_correct or 0
player = get_player(player_id)
checks = [
(“first_answer”, total_q >= 1, “First Answer”),
(“ten_correct”, total_correct >= 10, “10 Correct”),
(“level_5”, player and player[“level”] >= 5, “Level 5”),
]
now = datetime.now().isoformat()
for key, condition, name in checks:
if condition and key not in existing:
c.execute(“INSERT INTO achievements (player_id, achievement_key, earned_at) VALUES (?, ?, ?)”, (player_id, key, now))
earned.append({“key”: key, “name”: name})
conn.commit()
conn.close()
return earned

@app.get(”/achievements/{player_id}”)
def get_achievements(player_id: str):
conn = get_db()
c = conn.cursor()
c.execute(“SELECT achievement_key, earned_at FROM achievements WHERE player_id = ?”, (player_id,))
rows = c.fetchall()
conn.close()
return {“achievements”: [{“key”: r[0], “earned_at”: r[1]} for r in rows]}
