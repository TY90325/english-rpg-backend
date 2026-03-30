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

origins = [chr(42)]
app.add_middleware(
CORSMiddleware,
allow_origins=origins,
allow_credentials=True,
allow_methods=origins,
allow_headers=origins,
)

API_KEY = os.environ.get(chr(67)+chr(76)+chr(65)+chr(85)+chr(68)+chr(69)+chr(95)+chr(65)+chr(80)+chr(73)+chr(95)+chr(75)+chr(69)+chr(89)) or chr(32)

DB = chr(114)+chr(112)+chr(103)+chr(46)+chr(100)+chr(98)

T_PLAYERS = chr(112)+chr(108)+chr(97)+chr(121)+chr(101)+chr(114)+chr(115)
T_GRAMMAR = chr(103)+chr(114)+chr(97)+chr(109)+chr(109)+chr(97)+chr(114)+chr(95)+chr(114)+chr(101)+chr(99)+chr(111)+chr(114)+chr(100)+chr(115)
T_VOCAB = chr(118)+chr(111)+chr(99)+chr(97)+chr(98)+chr(95)+chr(114)+chr(101)+chr(99)+chr(111)+chr(114)+chr(100)+chr(115)
T_ACH = chr(97)+chr(99)+chr(104)+chr(105)+chr(101)+chr(118)+chr(101)+chr(109)+chr(101)+chr(110)+chr(116)+chr(115)

def init_db():
conn = sqlite3.connect(DB)
c = conn.cursor()
c.execute(””“CREATE TABLE IF NOT EXISTS players (
id TEXT PRIMARY KEY, name TEXT,
level INTEGER DEFAULT 1, xp INTEGER DEFAULT 0,
hp INTEGER DEFAULT 100, gold INTEGER DEFAULT 0,
created_at TEXT)”””)
c.execute(””“CREATE TABLE IF NOT EXISTS grammar_records (
id INTEGER PRIMARY KEY AUTOINCREMENT,
player_id TEXT, zone TEXT, question_type TEXT,
correct INTEGER, answered_at TEXT)”””)
c.execute(””“CREATE TABLE IF NOT EXISTS vocab_records (
id INTEGER PRIMARY KEY AUTOINCREMENT,
player_id TEXT, word TEXT, category TEXT, difficulty TEXT,
correct_count INTEGER DEFAULT 0, wrong_count INTEGER DEFAULT 0,
next_review TEXT, ease_factor REAL DEFAULT 2.5,
interval_days INTEGER DEFAULT 1, last_reviewed TEXT)”””)
c.execute(””“CREATE TABLE IF NOT EXISTS achievements (
id INTEGER PRIMARY KEY AUTOINCREMENT,
player_id TEXT, achievement_key TEXT, earned_at TEXT)”””)
conn.commit()
conn.close()

init_db()

def get_db():
return sqlite3.connect(DB)

def get_player(pid):
conn = get_db()
c = conn.cursor()
c.execute(””“SELECT id,name,level,xp,hp,gold,created_at FROM players WHERE id=?”””, (pid,))
row = c.fetchone()
conn.close()
if not row:
return None
keys = [chr(105)+chr(100), chr(110)+chr(97)+chr(109)+chr(101),
chr(108)+chr(101)+chr(118)+chr(101)+chr(108),
chr(120)+chr(112), chr(104)+chr(112),
chr(103)+chr(111)+chr(108)+chr(100),
chr(99)+chr(114)+chr(101)+chr(97)+chr(116)+chr(101)+chr(100)+chr(95)+chr(97)+chr(116)]
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
name: Optional[str] = None

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

ROUTE_ROOT = chr(47)
ROUTE_CREATE = chr(47)+chr(112)+chr(108)+chr(97)+chr(121)+chr(101)+chr(114)+chr(47)+chr(99)+chr(114)+chr(101)+chr(97)+chr(116)+chr(101)
ROUTE_PLAYER = chr(47)+chr(112)+chr(108)+chr(97)+chr(121)+chr(101)+chr(114)+chr(47)+chr(123)+chr(112)+chr(108)+chr(97)+chr(121)+chr(101)+chr(114)+chr(95)+chr(105)+chr(100)+chr(125)
ROUTE_ANSWER = chr(47)+chr(97)+chr(110)+chr(115)+chr(119)+chr(101)+chr(114)+chr(47)+chr(115)+chr(117)+chr(98)+chr(109)+chr(105)+chr(116)
ROUTE_ANALYSIS = chr(47)+chr(97)+chr(110)+chr(97)+chr(108)+chr(121)+chr(115)+chr(105)+chr(115)+chr(47)+chr(123)+chr(112)+chr(108)+chr(97)+chr(121)+chr(101)+chr(114)+chr(95)+chr(105)+chr(100)+chr(125)
ROUTE_VOCAB = chr(47)+chr(118)+chr(111)+chr(99)+chr(97)+chr(98)+chr(47)+chr(114)+chr(101)+chr(118)+chr(105)+chr(101)+chr(119)
ROUTE_DUE = chr(47)+chr(118)+chr(111)+chr(99)+chr(97)+chr(98)+chr(47)+chr(100)+chr(117)+chr(101)+chr(47)+chr(123)+chr(112)+chr(108)+chr(97)+chr(121)+chr(101)+chr(114)+chr(95)+chr(105)+chr(100)+chr(125)
ROUTE_AIGEN = chr(47)+chr(97)+chr(105)+chr(47)+chr(103)+chr(101)+chr(110)+chr(101)+chr(114)+chr(97)+chr(116)+chr(101)+chr(45)+chr(113)+chr(117)+chr(101)+chr(115)+chr(116)+chr(105)+chr(111)+chr(110)
ROUTE_TUTOR = chr(47)+chr(97)+chr(105)+chr(47)+chr(116)+chr(117)+chr(116)+chr(111)+chr(114)
ROUTE_ACH = chr(47)+chr(97)+chr(99)+chr(104)+chr(105)+chr(101)+chr(118)+chr(101)+chr(109)+chr(101)+chr(110)+chr(116)+chr(115)+chr(47)+chr(123)+chr(112)+chr(108)+chr(97)+chr(121)+chr(101)+chr(114)+chr(95)+chr(105)+chr(100)+chr(125)

@app.get(ROUTE_ROOT)
def root():
return {chr(115)+chr(116)+chr(97)+chr(116)+chr(117)+chr(115): chr(111)+chr(107)}

@app.post(ROUTE_CREATE)
def create_player(data: PlayerCreate):
existing = get_player(data.player_id)
if existing:
return {chr(115)+chr(117)+chr(99)+chr(99)+chr(101)+chr(115)+chr(115): True, chr(112)+chr(108)+chr(97)+chr(121)+chr(101)+chr(114): existing}
conn = get_db()
c = conn.cursor()
now = datetime.now().isoformat()
nm = data.name if data.name else chr(72)+chr(101)+chr(114)+chr(111)
c.execute(””“INSERT INTO players (id, name, created_at) VALUES (?,?,?)”””, (data.player_id, nm, now))
conn.commit()
conn.close()
return {chr(115)+chr(117)+chr(99)+chr(99)+chr(101)+chr(115)+chr(115): True, chr(112)+chr(108)+chr(97)+chr(121)+chr(101)+chr(114): get_player(data.player_id)}

@app.get(ROUTE_PLAYER)
def get_player_api(player_id: str):
p = get_player(player_id)
if not p:
raise HTTPException(status_code=404, detail=chr(110)+chr(111)+chr(116)+chr(32)+chr(102)+chr(111)+chr(117)+chr(110)+chr(100))
return p

@app.post(ROUTE_ANSWER)
def submit_answer(data: AnswerSubmit):
conn = get_db()
c = conn.cursor()
now = datetime.now().isoformat()
c.execute(””“INSERT INTO grammar_records (player_id,zone,question_type,correct,answered_at) VALUES (?,?,?,?,?)”””,
(data.player_id, data.zone, data.question_type, 1 if data.correct else 0, now))
if data.correct:
c.execute(””“UPDATE players SET xp=xp+?, gold=gold+10 WHERE id=?”””, (data.xp_gained, data.player_id))
else:
c.execute(””“UPDATE players SET hp=MAX(0,hp-10) WHERE id=?”””, (data.player_id,))
c.execute(””“SELECT xp FROM players WHERE id=?”””, (data.player_id,))
row = c.fetchone()
if row:
c.execute(””“UPDATE players SET level=? WHERE id=?”””, (calc_level(row[0]), data.player_id))
conn.commit()
conn.close()
return {chr(115)+chr(117)+chr(99)+chr(99)+chr(101)+chr(115)+chr(115): True, chr(112)+chr(108)+chr(97)+chr(121)+chr(101)+chr(114): get_player(data.player_id)}

@app.get(ROUTE_ANALYSIS)
def get_analysis(player_id: str):
conn = get_db()
c = conn.cursor()
c.execute(””“SELECT question_type,SUM(correct),COUNT(*) FROM grammar_records WHERE player_id=? GROUP BY question_type”””, (player_id,))
rows = c.fetchall()
conn.close()
result = []
for row in rows:
rate = round(row[1]/row[2]*100) if row[2] > 0 else 0
result.append({chr(116)+chr(121)+chr(112)+chr(101): row[0], chr(114)+chr(97)+chr(116)+chr(101): rate})
weak = [r[chr(116)+chr(121)+chr(112)+chr(101)] for r in result if r[chr(114)+chr(97)+chr(116)+chr(101)] < 60]
return {chr(97)+chr(110)+chr(97)+chr(108)+chr(121)+chr(115)+chr(105)+chr(115): result, chr(119)+chr(101)+chr(97)+chr(107)+chr(95)+chr(116)+chr(121)+chr(112)+chr(101)+chr(115): weak}

@app.post(ROUTE_VOCAB)
def review_vocab(data: VocabReview):
conn = get_db()
c = conn.cursor()
c.execute(””“SELECT id,ease_factor,interval_days FROM vocab_records WHERE player_id=? AND word=?”””, (data.player_id, data.word))
row = c.fetchone()
now = datetime.now().isoformat()
interval = 1 if data.rating == chr(97)+chr(103)+chr(97)+chr(105)+chr(110) else 3 if data.rating == chr(104)+chr(97)+chr(114)+chr(100) else 7
next_review = (datetime.now() + timedelta(days=interval)).isoformat()
if row:
new_ease = max(1.3, row[1] + (-0.2 if interval==1 else -0.1 if interval==3 else 0.1))
new_int = 1 if interval==1 else max(1, int(row[2]*new_ease))
next_review = (datetime.now() + timedelta(days=new_int)).isoformat()
c.execute(””“UPDATE vocab_records SET ease_factor=?,interval_days=?,next_review=?,last_reviewed=? WHERE id=?”””,
(new_ease, new_int, next_review, now, row[0]))
else:
c.execute(””“INSERT INTO vocab_records (player_id,word,category,difficulty,next_review,ease_factor,interval_days,last_reviewed) VALUES (?,?,?,?,?,2.5,?,?)”””,
(data.player_id, data.word, data.category, data.difficulty, next_review, interval, now))
conn.commit()
conn.close()
return {chr(115)+chr(117)+chr(99)+chr(99)+chr(101)+chr(115)+chr(115): True}

@app.get(ROUTE_DUE)
def get_due(player_id: str):
conn = get_db()
c = conn.cursor()
now = datetime.now().isoformat()
c.execute(””“SELECT word,category,difficulty FROM vocab_records WHERE player_id=? AND next_review<=? LIMIT 20”””, (player_id, now))
rows = c.fetchall()
conn.close()
return {chr(100)+chr(117)+chr(101)+chr(95)+chr(99)+chr(111)+chr(117)+chr(110)+chr(116): len(rows),
chr(119)+chr(111)+chr(114)+chr(100)+chr(115): [{chr(119)+chr(111)+chr(114)+chr(100): r[0]} for r in rows]}

@app.post(ROUTE_AIGEN)
def gen_question(data: AiQuestion):
if not API_KEY.strip():
raise HTTPException(status_code=500, detail=chr(110)+chr(111)+chr(32)+chr(107)+chr(101)+chr(121))
weak_str = chr(44)+chr(32).join(data.weak_types) if data.weak_types else chr(103)+chr(101)+chr(110)+chr(101)+chr(114)+chr(97)+chr(108)
prompt = (chr(67)+chr(114)+chr(101)+chr(97)+chr(116)+chr(101)+chr(32)+chr(111)+chr(110)+chr(101)+chr(32)+
chr(69)+chr(110)+chr(103)+chr(108)+chr(105)+chr(115)+chr(104)+chr(32)+chr(103)+chr(114)+chr(97)+chr(109)+chr(109)+chr(97)+chr(114)+chr(32)+
chr(109)+chr(117)+chr(108)+chr(116)+chr(105)+chr(112)+chr(108)+chr(101)+chr(32)+chr(99)+chr(104)+chr(111)+chr(105)+chr(99)+chr(101)+chr(32)+
chr(113)+chr(117)+chr(101)+chr(115)+chr(116)+chr(105)+chr(111)+chr(110)+chr(46)+chr(32)+
chr(90)+chr(111)+chr(110)+chr(101)+chr(58)+chr(32)) + data.zone + (
chr(46)+chr(32)+chr(87)+chr(101)+chr(97)+chr(107)+chr(58)+chr(32)) + weak_str + (
chr(46)+chr(32)+chr(82)+chr(101)+chr(112)+chr(108)+chr(121)+chr(32)+
chr(79)+chr(78)+chr(76)+chr(89)+chr(32)+chr(119)+chr(105)+chr(116)+chr(104)+chr(32)+
chr(74)+chr(83)+chr(79)+chr(78)+chr(58)+chr(32)+
chr(123)+chr(116)+chr(121)+chr(112)+chr(101)+chr(58)+chr(115)+chr(116)+chr(114)+chr(44)+
chr(113)+chr(117)+chr(101)+chr(115)+chr(116)+chr(105)+chr(111)+chr(110)+chr(58)+chr(115)+chr(116)+chr(114)+chr(44)+
chr(111)+chr(112)+chr(116)+chr(105)+chr(111)+chr(110)+chr(115)+chr(58)+chr(91)+chr(93)+chr(44)+
chr(97)+chr(110)+chr(115)+chr(119)+chr(101)+chr(114)+chr(95)+chr(105)+chr(110)+chr(100)+chr(101)+chr(120)+chr(58)+chr(48)+chr(44)+
chr(101)+chr(120)+chr(112)+chr(108)+chr(97)+chr(110)+chr(97)+chr(116)+chr(105)+chr(111)+chr(110)+chr(58)+chr(115)+chr(116)+chr(114)+chr(125))
client = anthropic.Anthropic(api_key=API_KEY.strip())
resp = client.messages.create(
model=chr(99)+chr(108)+chr(97)+chr(117)+chr(100)+chr(101)+chr(45)+chr(115)+chr(111)+chr(110)+chr(110)+chr(101)+chr(116)+chr(45)+chr(52)+chr(45)+chr(54),
max_tokens=400,
messages=[{chr(114)+chr(111)+chr(108)+chr(101): chr(117)+chr(115)+chr(101)+chr(114), chr(99)+chr(111)+chr(110)+chr(116)+chr(101)+chr(110)+chr(116): prompt}]
)
text = resp.content[0].text.strip()
for ch in [chr(96)+chr(96)+chr(96)+chr(106)+chr(115)+chr(111)+chr(110), chr(96)+chr(96)+chr(96)]:
text = text.replace(ch, chr(32))
return {chr(115)+chr(117)+chr(99)+chr(99)+chr(101)+chr(115)+chr(115): True, chr(113)+chr(117)+chr(101)+chr(115)+chr(116)+chr(105)+chr(111)+chr(110): json.loads(text.strip())}

@app.post(ROUTE_TUTOR)
def ai_tutor(data: AiChat):
if not API_KEY.strip():
raise HTTPException(status_code=500, detail=chr(110)+chr(111)+chr(32)+chr(107)+chr(101)+chr(121))
client = anthropic.Anthropic(api_key=API_KEY.strip())
sys_msg = (chr(89)+chr(111)+chr(117)+chr(32)+chr(97)+chr(114)+chr(101)+chr(32)+chr(97)+chr(110)+chr(32)+
chr(69)+chr(110)+chr(103)+chr(108)+chr(105)+chr(115)+chr(104)+chr(32)+chr(116)+chr(101)+chr(97)+chr(99)+chr(104)+chr(101)+chr(114)+chr(46)+chr(32)+
chr(82)+chr(101)+chr(112)+chr(108)+chr(121)+chr(32)+chr(105)+chr(110)+chr(32)+
chr(84)+chr(114)+chr(97)+chr(100)+chr(105)+chr(116)+chr(105)+chr(111)+chr(110)+chr(97)+chr(108)+chr(32)+
chr(67)+chr(104)+chr(105)+chr(110)+chr(101)+chr(115)+chr(101)+chr(46))
msgs = data.history + [{chr(114)+chr(111)+chr(108)+chr(101): chr(117)+chr(115)+chr(101)+chr(114), chr(99)+chr(111)+chr(110)+chr(116)+chr(101)+chr(110)+chr(116): data.message}]
resp = client.messages.create(
model=chr(99)+chr(108)+chr(97)+chr(117)+chr(100)+chr(101)+chr(45)+chr(115)+chr(111)+chr(110)+chr(110)+chr(101)+chr(116)+chr(45)+chr(52)+chr(45)+chr(54),
max_tokens=600,
system=sys_msg,
messages=msgs
)
return {chr(114)+chr(101)+chr(112)+chr(108)+chr(121): resp.content[0].text}

@app.get(ROUTE_ACH)
def get_achievements(player_id: str):
conn = get_db()
c = conn.cursor()
c.execute(””“SELECT achievement_key,earned_at FROM achievements WHERE player_id=?”””, (player_id,))
rows = c.fetchall()
conn.close()
return {chr(97)+chr(99)+chr(104)+chr(105)+chr(101)+chr(118)+chr(101)+chr(109)+chr(101)+chr(110)+chr(116)+chr(115): [{chr(107)+chr(101)+chr(121): r[0], chr(101)+chr(97)+chr(114)+chr(110)+chr(101)+chr(100): r[1]} for r in rows]}
