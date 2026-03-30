from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
import json
import os
import anthropic
from datetime import datetime, timedelta

app = FastAPI()

origins = [”*”]
app.add_middleware(
CORSMiddleware,
allow_origins=origins,
allow_credentials=True,
allow_methods=origins,
allow_headers=origins,
)

API_KEY = os.environ.get(“CLAUDE_API_KEY”) or “”

DB = “rpg.db”

CREATE_PLAYERS = “””
CREATE TABLE IF NOT EXISTS players (
id TEXT PRIMARY KEY,
name TEXT,
level INTEGER DEFAULT 1,
xp INTEGER DEFAULT 0,
hp INTEGER DEFAULT 100,
max_hp INTEGER DEFAULT 100,
gold INTEGER DEFAULT 0,
created_at TEXT
)
“””

CREATE_GRAMMAR = “””
CREATE TABLE IF NOT EXISTS grammar_records (
id INTEGER PRIMARY KEY AUTOINCREMENT,
player_id TEXT,
zone TEXT,
question_type TEXT,
correct INTEGER,
answered_at TEXT
)
“””

CREATE_VOCAB = “””
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
“””

CREATE_ACH = “””
CREATE TABLE IF NOT EXISTS achievements (
id INTEGER PRIMARY KEY AUTOINCREMENT,
player_id TEXT,
achievement_key TEXT,
earned_at TEXT
)
“””

def init_db():
conn = sqlite3.connect(DB)
c = conn.cursor()
c.execute(CREATE_PLAYERS)
c.execute(CREATE_GRAMMAR)
c.execute(CREATE_VOCAB)
c.execute(CREATE_ACH)
conn.commit()
conn.close()

init_db()

def get_db():
return sqlite3.connect(DB)

def get_player(pid):
conn = get_db()
c = conn.cursor()
c.execute(“SELECT * FROM players WHERE id = ?”, (pid,))
row = c.fetchone()
conn.close()
if not row:
return None
keys = [“id”,“name”,“level”,“xp”,“hp”,“max_hp”,“gold”,“created_at”]
return dict(zip(keys, row))

def calc_level(xp):
level = 1
needed = 500
while xp >= needed:
xp -= needed
level += 1
needed = 500 * level
return level

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

class AiQuestion(BaseModel):
player_id: str
zone: str
weak_types: List[str]

class AiChat(BaseModel):
player_id: str
message: str
history: List[dict]

@app.get(”/”)
def root():
return {“status”: “ok”}

@app.post(”/player/create”)
def create_player(data: PlayerCreate):
existing = get_player(data.player_id)
if existing:
return {“success”: True, “player”: existing, “is_new”: False}
conn = get_db()
c = conn.cursor()
now = datetime.now().isoformat()
c.execute(
“INSERT INTO players (id, name, created_at) VALUES (?, ?, ?)”,
(data.player_id, data.name, now)
)
conn.commit()
conn.close()
return {“success”: True, “player”: get_player(data.player_id), “is_new”: True}

@app.get(”/player/{player_id}”)
def get_player_api(player_id: str):
p = get_player(player_id)
if not p:
raise HTTPException(status_code=404, detail=“not found”)
return p

@app.post(”/answer/submit”)
def submit_answer(data: AnswerSubmit):
conn = get_db()
c = conn.cursor()
now = datetime.now().isoformat()
correct_int = 1 if data.correct else 0
c.execute(
“INSERT INTO grammar_records (player_id, zone, question_type, correct, answered_at) VALUES (?, ?, ?, ?, ?)”,
(data.player_id, data.zone, data.question_type, correct_int, now)
)
if data.correct:
c.execute(
“UPDATE players SET xp = xp + ?, gold = gold + 10 WHERE id = ?”,
(data.xp_gained, data.player_id)
)
else:
c.execute(
“UPDATE players SET hp = MAX(0, hp - 10) WHERE id = ?”,
(data.player_id,)
)
c.execute(“SELECT xp FROM players WHERE id = ?”, (data.player_id,))
row = c.fetchone()
if row:
new_level = calc_level(row[0])
c.execute(“UPDATE players SET level = ? WHERE id = ?”, (new_level, data.player_id))
conn.commit()
conn.close()
return {“success”: True, “player”: get_player(data.player_id)}

@app.get(”/analysis/{player_id}”)
def get_analysis(player_id: str):
conn = get_db()
c = conn.cursor()
c.execute(
“SELECT question_type, SUM(correct), COUNT(*) FROM grammar_records WHERE player_id = ? GROUP BY question_type”,
(player_id,)
)
rows = c.fetchall()
conn.close()
result = []
for row in rows:
qtype, correct, total = row
rate = round(correct / total * 100) if total > 0 else 0
result.append({“type”: qtype, “rate”: rate})
weak = [r[“type”] for r in result if r[“rate”] < 60]
return {“analysis”: result, “weak_types”: weak}

@app.post(”/vocab/review”)
def review_vocab(data: VocabReview):
conn = get_db()
c = conn.cursor()
c.execute(
“SELECT id, ease_factor, interval_days, correct_count, wrong_count FROM vocab_records WHERE player_id = ? AND word = ?”,
(data.player_id, data.word)
)
row = c.fetchone()
now = datetime.now().isoformat()
if data.rating == “again”:
interval = 1
delta = -0.2
elif data.rating == “hard”:
interval = 3
delta = -0.1
else:
interval = 7
delta = 0.1
next_review = (datetime.now() + timedelta(days=interval)).isoformat()
if row:
rid, ease, old_int, cc, wc = row
new_ease = max(1.3, ease + delta)
new_int = 1 if data.rating == “again” else max(1, int(old_int * new_ease))
next_review = (datetime.now() + timedelta(days=new_int)).isoformat()
c.execute(
“UPDATE vocab_records SET ease_factor=?, interval_days=?, next_review=?, last_reviewed=? WHERE id=?”,
(new_ease, new_int, next_review, now, rid)
)
else:
c.execute(
“INSERT INTO vocab_records (player_id, word, category, difficulty, next_review, ease_factor, interval_days, last_reviewed) VALUES (?, ?, ?, ?, ?, 2.5, ?, ?)”,
(data.player_id, data.word, data.category, data.difficulty, next_review, interval, now)
)
conn.commit()
conn.close()
return {“success”: True}

@app.get(”/vocab/due/{player_id}”)
def get_due(player_id: str):
conn = get_db()
c = conn.cursor()
now = datetime.now().isoformat()
c.execute(
“SELECT word, category, difficulty FROM vocab_records WHERE player_id = ? AND next_review <= ? LIMIT 20”,
(player_id, now)
)
rows = c.fetchall()
conn.close()
return {“due_count”: len(rows), “words”: [{“word”: r[0], “category”: r[1], “difficulty”: r[2]} for r in rows]}

@app.post(”/ai/generate-question”)
def gen_question(data: AiQuestion):
if not API_KEY:
raise HTTPException(status_code=500, detail=“No API key”)
weak_str = “, “.join(data.weak_types) if data.weak_types else “general”
prompt = (
“Create one English grammar multiple choice question. “
“Zone: “ + data.zone + “. “
“Student weak areas: “ + weak_str + “. “
“Reply ONLY with JSON: “
‘{“type”:“type in Chinese”,“question”:“question with ___ blank”,“options”:[“A”,“B”,“C”,“D”],“answer_index”:0,“explanation”:“Chinese explanation”}’
)
client = anthropic.Anthropic(api_key=API_KEY)
resp = client.messages.create(
model=“claude-sonnet-4-6”,
max_tokens=400,
messages=[{“role”: “user”, “content”: prompt}]
)
text = resp.content[0].text.strip()
text = text.replace(”`json", "").replace("`”, “”).strip()
return {“success”: True, “question”: json.loads(text)}

@app.post(”/ai/tutor”)
def ai_tutor(data: AiChat):
if not API_KEY:
raise HTTPException(status_code=500, detail=“No API key”)
client = anthropic.Anthropic(api_key=API_KEY)
sys_msg = “You are an English teacher for Taiwanese students. Reply in Traditional Chinese with English examples.”
msgs = data.history + [{“role”: “user”, “content”: data.message}]
resp = client.messages.create(
model=“claude-sonnet-4-6”,
max_tokens=600,
system=sys_msg,
messages=msgs
)
return {“reply”: resp.content[0].text}

@app.get(”/achievements/{player_id}”)
def get_achievements(player_id: str):
conn = get_db()
c = conn.cursor()
c.execute(“SELECT achievement_key, earned_at FROM achievements WHERE player_id = ?”, (player_id,))
rows = c.fetchall()
conn.close()
return {“achievements”: [{“key”: r[0], “earned_at”: r[1]} for r in rows]}
