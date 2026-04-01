from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sqlite3, json, os, anthropic
from datetime import datetime, timedelta

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

KEY = os.environ.get("CLAUDE_API_KEY", "")


def db():
    return sqlite3.connect("rpg.db")


def setup():
    c = db()
    c.execute("CREATE TABLE IF NOT EXISTS players(id TEXT PRIMARY KEY,name TEXT,level INT DEFAULT 1,xp INT DEFAULT 0,hp INT DEFAULT 100,gold INT DEFAULT 0,ts TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS grammar(id INTEGER PRIMARY KEY AUTOINCREMENT,pid TEXT,zone TEXT,qtype TEXT,correct INT,ts TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS vocab(id INTEGER PRIMARY KEY AUTOINCREMENT,pid TEXT,word TEXT,cat TEXT,diff TEXT,ease REAL DEFAULT 2.5,interval INT DEFAULT 1,next TEXT,ts TEXT)")
    c.commit()
    c.close()


setup()


def player(pid):
    c = db()
    r = c.execute("SELECT id,name,level,xp,hp,gold FROM players WHERE id=?", (pid,)).fetchone()
    c.close()
    if not r:
        return None
    return {"id": r[0], "name": r[1], "level": r[2], "xp": r[3], "hp": r[4], "gold": r[5]}


def lvl(xp):
    l, n = 1, 500
    while xp >= n:
        xp -= n
        l += 1
        n = 500 * l
    return l


class PC(BaseModel):
    player_id: str
    name: Optional[str] = None


class AS(BaseModel):
    player_id: str
    zone: str
    question_type: str
    correct: bool
    xp_gained: int


class VR(BaseModel):
    player_id: str
    word: str
    category: str
    difficulty: str
    rating: str


class AQ(BaseModel):
    player_id: str
    zone: str
    weak_types: List[str]


class AC(BaseModel):
    player_id: str
    message: str
    history: List[dict]


@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/player/create")
def create(data: PC):
    p = player(data.player_id)
    if p:
        return {"ok": True, "player": p}
    c = db()
    c.execute(
        "INSERT INTO players(id,name,ts) VALUES(?,?,?)",
        (data.player_id, data.name or "Hero", datetime.now().isoformat())
    )
    c.commit()
    c.close()
    return {"ok": True, "player": player(data.player_id)}


@app.get("/player/{pid}")
def get_p(pid: str):
    p = player(pid)
    if not p:
        raise HTTPException(404, "not found")
    return p


@app.post("/answer/submit")
def answer(data: AS):
    c = db()
    now = datetime.now().isoformat()
    c.execute(
        "INSERT INTO grammar(pid,zone,qtype,correct,ts) VALUES(?,?,?,?,?)",
        (data.player_id, data.zone, data.question_type, 1 if data.correct else 0, now)
    )
    if data.correct:
        c.execute("UPDATE players SET xp=xp+?,gold=gold+10 WHERE id=?", (data.xp_gained, data.player_id))
    else:
        c.execute("UPDATE players SET hp=MAX(0,hp-10) WHERE id=?", (data.player_id,))
    r = c.execute("SELECT xp FROM players WHERE id=?", (data.player_id,)).fetchone()
    if r:
        c.execute("UPDATE players SET level=? WHERE id=?", (lvl(r[0]), data.player_id))
    c.commit()
    c.close()
    return {"ok": True, "player": player(data.player_id)}


@app.get("/analysis/{pid}")
def analysis(pid: str):
    c = db()
    rows = c.execute(
        "SELECT qtype,SUM(correct),COUNT(*) FROM grammar WHERE pid=? GROUP BY qtype", (pid,)
    ).fetchall()
    c.close()
    res = [{"type": r[0], "rate": round(r[1] / r[2] * 100) if r[2] else 0} for r in rows]
    return {"analysis": res, "weak": [r["type"] for r in res if r["rate"] < 60]}


@app.post("/vocab/review")
def vocab(data: VR):
    c = db()
    r = c.execute(
        "SELECT id,ease,interval FROM vocab WHERE pid=? AND word=?", (data.player_id, data.word)
    ).fetchone()
    now = datetime.now().isoformat()
    i = 1 if data.rating == "again" else 3 if data.rating == "hard" else 7
    nr = (datetime.now() + timedelta(days=i)).isoformat()
    if r:
        c.execute(
            "UPDATE vocab SET ease=?,interval=?,next=?,ts=? WHERE id=?",
            (max(1.3, r[1] + (-0.2 if i == 1 else -0.1 if i == 3 else 0.1)),
             1 if i == 1 else max(1, int(r[2] * r[1])), nr, now, r[0])
        )
    else:
        c.execute(
            "INSERT INTO vocab(pid,word,cat,diff,next,ts) VALUES(?,?,?,?,?,?)",
            (data.player_id, data.word, data.category, data.difficulty, nr, now)
        )
    c.commit()
    c.close()
    return {"ok": True}


@app.get("/vocab/due/{pid}")
def due(pid: str):
    c = db()
    rows = c.execute(
        "SELECT word,cat,diff FROM vocab WHERE pid=? AND next<=? LIMIT 20",
        (pid, datetime.now().isoformat())
    ).fetchall()
    c.close()
    return {"count": len(rows), "words": [{"word": r[0], "cat": r[1]} for r in rows]}


@app.post("/ai/question")
def ai_q(data: AQ):
    if not KEY:
        raise HTTPException(500, "no key")
    p = (
        "Create one English grammar MCQ. Zone:" + data.zone +
        ". Weak:" + ",".join(data.weak_types or ["general"]) +
        ". JSON only: {\"type\",\"question\",\"options\":[],\"answer_index\",\"explanation\"}"
    )
    r = anthropic.Anthropic(api_key=KEY).messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        messages=[{"role": "user", "content": p}]
    )
    return {
        "ok": True,
        "question": json.loads(
            r.content[0].text.strip().replace("```json", "").replace("```", "").strip()
        )
    }


@app.post("/ai/tutor")
def ai_t(data: AC):
    if not KEY:
        raise HTTPException(500, "no key")
    r = anthropic.Anthropic(api_key=KEY).messages.create(
        model="claude-sonnet-4-6",
        max_tokens=600,
        system="You are an English teacher. Reply in Traditional Chinese.",
        messages=data.history + [{"role": "user", "content": data.message}]
    )
    return {"reply": r.content[0].text}
