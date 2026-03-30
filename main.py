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

SQL_CREATE_PLAYERS = chr(67)+chr(82)+chr(69)+chr(65)+chr(84)+chr(69)+chr(32)+chr(84)+chr(65)+chr(66)+chr(76)+chr(69)+chr(32)+chr(73)+chr(70)+chr(32)+chr(78)+chr(79)+chr(84)+chr(32)+chr(69)+chr(88)+chr(73)+chr(83)+chr(84)+chr(83)+chr(32)+chr(112)+chr(108)+chr(97)+chr(121)+chr(101)+chr(114)+chr(115)+chr(32)+chr(40)+chr(105)+chr(100)+chr(32)+chr(84)+chr(69)+chr(88)+chr(84)+chr(32)+chr(80)+chr(82)+chr(73)+chr(77)+chr(65)+chr(82)+chr(89)+chr(32)+chr(75)+chr(69)+chr(89)+chr(44)+chr(32)+chr(110)+chr(97)+chr(109)+chr(101)+chr(32)+chr(84)+chr(69)+chr(88)+chr(84)+chr(44)+chr(32)+chr(108)+chr(101)+chr(118)+chr(101)+chr(108)+chr(32)+chr(73)+chr(78)+chr(84)+chr(69)+chr(71)+chr(69)+chr(82)+chr(32)+chr(68)+chr(69)+chr(70)+chr(65)+chr(85)+chr(76)+chr(84)+chr(32)+chr(49)+chr(44)+chr(32)+chr(120)+chr(112)+chr(32)+chr(73)+chr(78)+chr(84)+chr(69)+chr(71)+chr(69)+chr(82)+chr(32)+chr(68)+chr(69)+chr(70)+chr(65)+chr(85)+chr(76)+chr(84)+chr(32)+chr(48)+chr(44)+chr(32)+chr(104)+chr(112)+chr(32)+chr(73)+chr(78)+chr(84)+chr(69)+chr(71)+chr(69)+chr(82)+chr(32)+chr(68)+chr(69)+chr(70)+chr(65)+chr(85)+chr(76)+chr(84)+chr(32)+chr(49)+chr(48)+chr(48)+chr(44)+chr(32)+chr(103)+chr(111)+chr(108)+chr(100)+chr(32)+chr(73)+chr(78)+chr(84)+chr(69)+chr(71)+chr(69)+chr(82)+chr(32)+chr(68)+chr(69)+chr(70)+chr(65)+chr(85)+chr(76)+chr(84)+chr(32)+chr(48)+chr(44)+chr(32)+chr(99)+chr(114)+chr(101)+chr(97)+chr(116)+chr(101)+chr(100)+chr(95)+chr(97)+chr(116)+chr(32)+chr(84)+chr(69)+chr(88)+chr(84)+chr(41)
SQL_CREATE_GRAMMAR = chr(67)+chr(82)+chr(69)+chr(65)+chr(84)+chr(69)+chr(32)+chr(84)+chr(65)+chr(66)+chr(76)+chr(69)+chr(32)+chr(73)+chr(70)+chr(32)+chr(78)+chr(79)+chr(84)+chr(32)+chr(69)+chr(88)+chr(73)+chr(83)+chr(84)+chr(83)+chr(32)+chr(103)+chr(114)+chr(97)+chr(109)+chr(109)+chr(97)+chr(114)+chr(95)+chr(114)+chr(101)+chr(99)+chr(111)+chr(114)+chr(100)+chr(115)+chr(32)+chr(40)+chr(105)+chr(100)+chr(32)+chr(73)+chr(78)+chr(84)+chr(69)+chr(71)+chr(69)+chr(82)+chr(32)+chr(80)+chr(82)+chr(73)+chr(77)+chr(65)+chr(82)+chr(89)+chr(32)+chr(75)+chr(69)+chr(89)+chr(32)+chr(65)+chr(85)+chr(84)+chr(79)+chr(73)+chr(78)+chr(67)+chr(82)+chr(69)+chr(77)+chr(69)+chr(78)+chr(84)+chr(44)+chr(32)+chr(112)+chr(108)+chr(97)+chr(121)+chr(101)+chr(114)+chr(95)+chr(105)+chr(100)+chr(32)+chr(84)+chr(69)+chr(88)+chr(84)+chr(44)+chr(32)+chr(122)+chr(111)+chr(110)+chr(101)+chr(32)+chr(84)+chr(69)+chr(88)+chr(84)+chr(44)+chr(32)+chr(113)+chr(117)+chr(101)+chr(115)+chr(116)+chr(105)+chr(111)+chr(110)+chr(95)+chr(116)+chr(121)+chr(112)+chr(101)+chr(32)+chr(84)+chr(69)+chr(88)+chr(84)+chr(44)+chr(32)+chr(99)+chr(111)+chr(114)+chr(114)+chr(101)+chr(99)+chr(116)+chr(32)+chr(73)+chr(78)+chr(84)+chr(69)+chr(71)+chr(69)+chr(82)+chr(44)+chr(32)+chr(97)+chr(110)+chr(115)+chr(119)+chr(101)+chr(114)+chr(101)+chr(100)+chr(95)+chr(97)+chr(116)+chr(32)+chr(84)+chr(69)+chr(88)+chr(84)+chr(41)
SQL_CREATE_VOCAB = chr(67)+chr(82)+chr(69)+chr(65)+chr(84)+chr(69)+chr(32)+chr(84)+chr(65)+chr(66)+chr(76)+chr(69)+chr(32)+chr(73)+chr(70)+chr(32)+chr(78)+chr(79)+chr(84)+chr(32)+chr(69)+chr(88)+chr(73)+chr(83)+chr(84)+chr(83)+chr(32)+chr(118)+chr(111)+chr(99)+chr(97)+chr(98)+chr(95)+chr(114)+chr(101)+chr(99)+chr(111)+chr(114)+chr(100)+chr(115)+chr(32)+chr(40)+chr(105)+chr(100)+chr(32)+chr(73)+chr(78)+chr(84)+chr(69)+chr(71)+chr(69)+chr(82)+chr(32)+chr(80)+chr(82)+chr(73)+chr(77)+chr(65)+chr(82)+chr(89)+chr(32)+chr(75)+chr(69)+chr(89)+chr(32)+chr(65)+chr(85)+chr(84)+chr(79)+chr(73)+chr(78)+chr(67)+chr(82)+chr(69)+chr(77)+chr(69)+chr(78)+chr(84)+chr(44)+chr(32)+chr(112)+chr(108)+chr(97)+chr(121)+chr(101)+chr(114)+chr(95)+chr(105)+chr(100)+chr(32)+chr(84)+chr(69)+chr(88)+chr(84)+chr(44)+chr(32)+chr(119)+chr(111)+chr(114)+chr(100)+chr(32)+chr(84)+chr(69)+chr(88)+chr(84)+chr(44)+chr(32)+chr(99)+chr(97)+chr(116)+chr(101)+chr(103)+chr(111)+chr(114)+chr(121)+chr(32)+chr(84)+chr(69)+chr(88)+chr(84)+chr(44)+chr(32)+chr(100)+chr(105)+chr(102)+chr(102)+chr(105)+chr(99)+chr(117)+chr(108)+chr(116)+chr(121)+chr(32)+chr(84)+chr(69)+chr(88)+chr(84)+chr(44)+chr(32)+chr(99)+chr(111)+chr(114)+chr(114)+chr(101)+chr(99)+chr(116)+chr(95)+chr(99)+chr(111)+chr(117)+chr(110)+chr(116)+chr(32)+chr(73)+chr(78)+chr(84)+chr(69)+chr(71)+chr(69)+chr(82)+chr(32)+chr(68)+chr(69)+chr(70)+chr(65)+chr(85)+chr(76)+chr(84)+chr(32)+chr(48)+chr(44)+chr(32)+chr(119)+chr(114)+chr(111)+chr(110)+chr(103)+chr(95)+chr(99)+chr(111)+chr(117)+chr(110)+chr(116)+chr(32)+chr(73)+chr(78)+chr(84)+chr(69)+chr(71)+chr(69)+chr(82)+chr(32)+chr(68)+chr(69)+chr(70)+chr(65)+chr(85)+chr(76)+chr(84)+chr(32)+chr(48)+chr(44)+chr(32)+chr(110)+chr(101)+chr(120)+chr(116)+chr(95)+chr(114)+chr(101)+chr(118)+chr(105)+chr(101)+chr(119)+chr(32)+chr(84)+chr(69)+chr(88)+chr(84)+chr(44)+chr(32)+chr(101)+chr(97)+chr(115)+chr(101)+chr(95)+chr(102)+chr(97)+chr(99)+chr(116)+chr(111)+chr(114)+chr(32)+chr(82)+chr(69)+chr(65)+chr(76)+chr(32)+chr(68)+chr(69)+chr(70)+chr(65)+chr(85)+chr(76)+chr(84)+chr(32)+chr(50)+chr(46)+chr(53)+chr(44)+chr(32)+chr(105)+chr(110)+chr(116)+chr(101)+chr(114)+chr(118)+chr(97)+chr(108)+chr(95)+chr(100)+chr(97)+chr(121)+chr(115)+chr(32)+chr(73)+chr(78)+chr(84)+chr(69)+chr(71)+chr(69)+chr(82)+chr(32)+chr(68)+chr(69)+chr(70)+chr(65)+chr(85)+chr(76)+chr(84)+chr(32)+chr(49)+chr(44)+chr(32)+chr(108)+chr(97)+chr(115)+chr(116)+chr(95)+chr(114)+chr(101)+chr(118)+chr(105)+chr(101)+chr(119)+chr(101)+chr(100)+chr(32)+chr(84)+chr(69)+chr(88)+chr(84)+chr(41)
SQL_CREATE_ACH = chr(67)+chr(82)+chr(69)+chr(65)+chr(84)+chr(69)+chr(32)+chr(84)+chr(65)+chr(66)+chr(76)+chr(69)+chr(32)+chr(73)+chr(70)+chr(32)+chr(78)+chr(79)+chr(84)+chr(32)+chr(69)+chr(88)+chr(73)+chr(83)+chr(84)+chr(83)+chr(32)+chr(97)+chr(99)+chr(104)+chr(105)+chr(101)+chr(118)+chr(101)+chr(109)+chr(101)+chr(110)+chr(116)+chr(115)+chr(32)+chr(40)+chr(105)+chr(100)+chr(32)+chr(73)+chr(78)+chr(84)+chr(69)+chr(71)+chr(69)+chr(82)+chr(32)+chr(80)+chr(82)+chr(73)+chr(77)+chr(65)+chr(82)+chr(89)+chr(32)+chr(75)+chr(69)+chr(89)+chr(32)+chr(65)+chr(85)+chr(84)+chr(79)+chr(73)+chr(78)+chr(67)+chr(82)+chr(69)+chr(77)+chr(69)+chr(78)+chr(84)+chr(44)+chr(32)+chr(112)+chr(108)+chr(97)+chr(121)+chr(101)+chr(114)+chr(95)+chr(105)+chr(100)+chr(32)+chr(84)+chr(69)+chr(88)+chr(84)+chr(44)+chr(32)+chr(97)+chr(99)+chr(104)+chr(105)+chr(101)+chr(118)+chr(101)+chr(109)+chr(101)+chr(110)+chr(116)+chr(95)+chr(107)+chr(101)+chr(121)+chr(32)+chr(84)+chr(69)+chr(88)+chr(84)+chr(44)+chr(32)+chr(101)+chr(97)+chr(114)+chr(110)+chr(101)+chr(100)+chr(95)+chr(97)+chr(116)+chr(32)+chr(84)+chr(69)+chr(88)+chr(84)+chr(41)
SQL_GET_PLAYER = chr(83)+chr(69)+chr(76)+chr(69)+chr(67)+chr(84)+chr(32)+chr(105)+chr(100)+chr(44)+chr(110)+chr(97)+chr(109)+chr(101)+chr(44)+chr(108)+chr(101)+chr(118)+chr(101)+chr(108)+chr(44)+chr(120)+chr(112)+chr(44)+chr(104)+chr(112)+chr(44)+chr(103)+chr(111)+chr(108)+chr(100)+chr(44)+chr(99)+chr(114)+chr(101)+chr(97)+chr(116)+chr(101)+chr(100)+chr(95)+chr(97)+chr(116)+chr(32)+chr(70)+chr(82)+chr(79)+chr(77)+chr(32)+chr(112)+chr(108)+chr(97)+chr(121)+chr(101)+chr(114)+chr(115)+chr(32)+chr(87)+chr(72)+chr(69)+chr(82)+chr(69)+chr(32)+chr(105)+chr(100)+chr(61)+chr(63)
SQL_INSERT_PLAYER = chr(73)+chr(78)+chr(83)+chr(69)+chr(82)+chr(84)+chr(32)+chr(73)+chr(78)+chr(84)+chr(79)+chr(32)+chr(112)+chr(108)+chr(97)+chr(121)+chr(101)+chr(114)+chr(115)+chr(32)+chr(40)+chr(105)+chr(100)+chr(44)+chr(32)+chr(110)+chr(97)+chr(109)+chr(101)+chr(44)+chr(32)+chr(99)+chr(114)+chr(101)+chr(97)+chr(116)+chr(101)+chr(100)+chr(95)+chr(97)+chr(116)+chr(41)+chr(32)+chr(86)+chr(65)+chr(76)+chr(85)+chr(69)+chr(83)+chr(32)+chr(40)+chr(63)+chr(44)+chr(63)+chr(44)+chr(63)+chr(41)
SQL_INSERT_GRAMMAR = chr(73)+chr(78)+chr(83)+chr(69)+chr(82)+chr(84)+chr(32)+chr(73)+chr(78)+chr(84)+chr(79)+chr(32)+chr(103)+chr(114)+chr(97)+chr(109)+chr(109)+chr(97)+chr(114)+chr(95)+chr(114)+chr(101)+chr(99)+chr(111)+chr(114)+chr(100)+chr(115)+chr(32)+chr(40)+chr(112)+chr(108)+chr(97)+chr(121)+chr(101)+chr(114)+chr(95)+chr(105)+chr(100)+chr(44)+chr(122)+chr(111)+chr(110)+chr(101)+chr(44)+chr(113)+chr(117)+chr(101)+chr(115)+chr(116)+chr(105)+chr(111)+chr(110)+chr(95)+chr(116)+chr(121)+chr(112)+chr(101)+chr(44)+chr(99)+chr(111)+chr(114)+chr(114)+chr(101)+chr(99)+chr(116)+chr(44)+chr(97)+chr(110)+chr(115)+chr(119)+chr(101)+chr(114)+chr(101)+chr(100)+chr(95)+chr(97)+chr(116)+chr(41)+chr(32)+chr(86)+chr(65)+chr(76)+chr(85)+chr(69)+chr(83)+chr(32)+chr(40)+chr(63)+chr(44)+chr(63)+chr(44)+chr(63)+chr(44)+chr(63)+chr(44)+chr(63)+chr(41)
SQL_UPDATE_XP = chr(85)+chr(80)+chr(68)+chr(65)+chr(84)+chr(69)+chr(32)+chr(112)+chr(108)+chr(97)+chr(121)+chr(101)+chr(114)+chr(115)+chr(32)+chr(83)+chr(69)+chr(84)+chr(32)+chr(120)+chr(112)+chr(61)+chr(120)+chr(112)+chr(43)+chr(63)+chr(44)+chr(32)+chr(103)+chr(111)+chr(108)+chr(100)+chr(61)+chr(103)+chr(111)+chr(108)+chr(100)+chr(43)+chr(49)+chr(48)+chr(32)+chr(87)+chr(72)+chr(69)+chr(82)+chr(69)+chr(32)+chr(105)+chr(100)+chr(61)+chr(63)
SQL_UPDATE_HP = chr(85)+chr(80)+chr(68)+chr(65)+chr(84)+chr(69)+chr(32)+chr(112)+chr(108)+chr(97)+chr(121)+chr(101)+chr(114)+chr(115)+chr(32)+chr(83)+chr(69)+chr(84)+chr(32)+chr(104)+chr(112)+chr(61)+chr(77)+chr(65)+chr(88)+chr(40)+chr(48)+chr(44)+chr(104)+chr(112)+chr(45)+chr(49)+chr(48)+chr(41)+chr(32)+chr(87)+chr(72)+chr(69)+chr(82)+chr(69)+chr(32)+chr(105)+chr(100)+chr(61)+chr(63)
SQL_GET_XP = chr(83)+chr(69)+chr(76)+chr(69)+chr(67)+chr(84)+chr(32)+chr(120)+chr(112)+chr(32)+chr(70)+chr(82)+chr(79)+chr(77)+chr(32)+chr(112)+chr(108)+chr(97)+chr(121)+chr(101)+chr(114)+chr(115)+chr(32)+chr(87)+chr(72)+chr(69)+chr(82)+chr(69)+chr(32)+chr(105)+chr(100)+chr(61)+chr(63)
SQL_UPDATE_LEVEL = chr(85)+chr(80)+chr(68)+chr(65)+chr(84)+chr(69)+chr(32)+chr(112)+chr(108)+chr(97)+chr(121)+chr(101)+chr(114)+chr(115)+chr(32)+chr(83)+chr(69)+chr(84)+chr(32)+chr(108)+chr(101)+chr(118)+chr(101)+chr(108)+chr(61)+chr(63)+chr(32)+chr(87)+chr(72)+chr(69)+chr(82)+chr(69)+chr(32)+chr(105)+chr(100)+chr(61)+chr(63)
SQL_GET_ANALYSIS = chr(83)+chr(69)+chr(76)+chr(69)+chr(67)+chr(84)+chr(32)+chr(113)+chr(117)+chr(101)+chr(115)+chr(116)+chr(105)+chr(111)+chr(110)+chr(95)+chr(116)+chr(121)+chr(112)+chr(101)+chr(44)+chr(83)+chr(85)+chr(77)+chr(40)+chr(99)+chr(111)+chr(114)+chr(114)+chr(101)+chr(99)+chr(116)+chr(41)+chr(44)+chr(67)+chr(79)+chr(85)+chr(78)+chr(84)+chr(40)+chr(42)+chr(41)+chr(32)+chr(70)+chr(82)+chr(79)+chr(77)+chr(32)+chr(103)+chr(114)+chr(97)+chr(109)+chr(109)+chr(97)+chr(114)+chr(95)+chr(114)+chr(101)+chr(99)+chr(111)+chr(114)+chr(100)+chr(115)+chr(32)+chr(87)+chr(72)+chr(69)+chr(82)+chr(69)+chr(32)+chr(112)+chr(108)+chr(97)+chr(121)+chr(101)+chr(114)+chr(95)+chr(105)+chr(100)+chr(61)+chr(63)+chr(32)+chr(71)+chr(82)+chr(79)+chr(85)+chr(80)+chr(32)+chr(66)+chr(89)+chr(32)+chr(113)+chr(117)+chr(101)+chr(115)+chr(116)+chr(105)+chr(111)+chr(110)+chr(95)+chr(116)+chr(121)+chr(112)+chr(101)
SQL_GET_VOCAB = chr(83)+chr(69)+chr(76)+chr(69)+chr(67)+chr(84)+chr(32)+chr(105)+chr(100)+chr(44)+chr(101)+chr(97)+chr(115)+chr(101)+chr(95)+chr(102)+chr(97)+chr(99)+chr(116)+chr(111)+chr(114)+chr(44)+chr(105)+chr(110)+chr(116)+chr(101)+chr(114)+chr(118)+chr(97)+chr(108)+chr(95)+chr(100)+chr(97)+chr(121)+chr(115)+chr(32)+chr(70)+chr(82)+chr(79)+chr(77)+chr(32)+chr(118)+chr(111)+chr(99)+chr(97)+chr(98)+chr(95)+chr(114)+chr(101)+chr(99)+chr(111)+chr(114)+chr(100)+chr(115)+chr(32)+chr(87)+chr(72)+chr(69)+chr(82)+chr(69)+chr(32)+chr(112)+chr(108)+chr(97)+chr(121)+chr(101)+chr(114)+chr(95)+chr(105)+chr(100)+chr(61)+chr(63)+chr(32)+chr(65)+chr(78)+chr(68)+chr(32)+chr(119)+chr(111)+chr(114)+chr(100)+chr(61)+chr(63)
SQL_UPDATE_VOCAB = chr(85)+chr(80)+chr(68)+chr(65)+chr(84)+chr(69)+chr(32)+chr(118)+chr(111)+chr(99)+chr(97)+chr(98)+chr(95)+chr(114)+chr(101)+chr(99)+chr(111)+chr(114)+chr(100)+chr(115)+chr(32)+chr(83)+chr(69)+chr(84)+chr(32)+chr(101)+chr(97)+chr(115)+chr(101)+chr(95)+chr(102)+chr(97)+chr(99)+chr(116)+chr(111)+chr(114)+chr(61)+chr(63)+chr(44)+chr(105)+chr(110)+chr(116)+chr(101)+chr(114)+chr(118)+chr(97)+chr(108)+chr(95)+chr(100)+chr(97)+chr(121)+chr(115)+chr(61)+chr(63)+chr(44)+chr(110)+chr(101)+chr(120)+chr(116)+chr(95)+chr(114)+chr(101)+chr(118)+chr(105)+chr(101)+chr(119)+chr(61)+chr(63)+chr(44)+chr(108)+chr(97)+chr(115)+chr(116)+chr(95)+chr(114)+chr(101)+chr(118)+chr(105)+chr(101)+chr(119)+chr(101)+chr(100)+chr(61)+chr(63)+chr(32)+chr(87)+chr(72)+chr(69)+chr(82)+chr(69)+chr(32)+chr(105)+chr(100)+chr(61)+chr(63)
SQL_INSERT_VOCAB = chr(73)+chr(78)+chr(83)+chr(69)+chr(82)+chr(84)+chr(32)+chr(73)+chr(78)+chr(84)+chr(79)+chr(32)+chr(118)+chr(111)+chr(99)+chr(97)+chr(98)+chr(95)+chr(114)+chr(101)+chr(99)+chr(111)+chr(114)+chr(100)+chr(115)+chr(32)+chr(40)+chr(112)+chr(108)+chr(97)+chr(121)+chr(101)+chr(114)+chr(95)+chr(105)+chr(100)+chr(44)+chr(119)+chr(111)+chr(114)+chr(100)+chr(44)+chr(99)+chr(97)+chr(116)+chr(101)+chr(103)+chr(111)+chr(114)+chr(121)+chr(44)+chr(100)+chr(105)+chr(102)+chr(102)+chr(105)+chr(99)+chr(117)+chr(108)+chr(116)+chr(121)+chr(44)+chr(110)+chr(101)+chr(120)+chr(116)+chr(95)+chr(114)+chr(101)+chr(118)+chr(105)+chr(101)+chr(119)+chr(44)+chr(101)+chr(97)+chr(115)+chr(101)+chr(95)+chr(102)+chr(97)+chr(99)+chr(116)+chr(111)+chr(114)+chr(44)+chr(105)+chr(110)+chr(116)+chr(101)+chr(114)+chr(118)+chr(97)+chr(108)+chr(95)+chr(100)+chr(97)+chr(121)+chr(115)+chr(44)+chr(108)+chr(97)+chr(115)+chr(116)+chr(95)+chr(114)+chr(101)+chr(118)+chr(105)+chr(101)+chr(119)+chr(101)+chr(100)+chr(41)+chr(32)+chr(86)+chr(65)+chr(76)+chr(85)+chr(69)+chr(83)+chr(32)+chr(40)+chr(63)+chr(44)+chr(63)+chr(44)+chr(63)+chr(44)+chr(63)+chr(44)+chr(63)+chr(44)+chr(50)+chr(46)+chr(53)+chr(44)+chr(63)+chr(44)+chr(63)+chr(41)
SQL_GET_DUE = chr(83)+chr(69)+chr(76)+chr(69)+chr(67)+chr(84)+chr(32)+chr(119)+chr(111)+chr(114)+chr(100)+chr(44)+chr(99)+chr(97)+chr(116)+chr(101)+chr(103)+chr(111)+chr(114)+chr(121)+chr(44)+chr(100)+chr(105)+chr(102)+chr(102)+chr(105)+chr(99)+chr(117)+chr(108)+chr(116)+chr(121)+chr(32)+chr(70)+chr(82)+chr(79)+chr(77)+chr(32)+chr(118)+chr(111)+chr(99)+chr(97)+chr(98)+chr(95)+chr(114)+chr(101)+chr(99)+chr(111)+chr(114)+chr(100)+chr(115)+chr(32)+chr(87)+chr(72)+chr(69)+chr(82)+chr(69)+chr(32)+chr(112)+chr(108)+chr(97)+chr(121)+chr(101)+chr(114)+chr(95)+chr(105)+chr(100)+chr(61)+chr(63)+chr(32)+chr(65)+chr(78)+chr(68)+chr(32)+chr(110)+chr(101)+chr(120)+chr(116)+chr(95)+chr(114)+chr(101)+chr(118)+chr(105)+chr(101)+chr(119)+chr(60)+chr(61)+chr(63)+chr(32)+chr(76)+chr(73)+chr(77)+chr(73)+chr(84)+chr(32)+chr(50)+chr(48)
SQL_GET_ACH = chr(83)+chr(69)+chr(76)+chr(69)+chr(67)+chr(84)+chr(32)+chr(97)+chr(99)+chr(104)+chr(105)+chr(101)+chr(118)+chr(101)+chr(109)+chr(101)+chr(110)+chr(116)+chr(95)+chr(107)+chr(101)+chr(121)+chr(44)+chr(101)+chr(97)+chr(114)+chr(110)+chr(101)+chr(100)+chr(95)+chr(97)+chr(116)+chr(32)+chr(70)+chr(82)+chr(79)+chr(77)+chr(32)+chr(97)+chr(99)+chr(104)+chr(105)+chr(101)+chr(118)+chr(101)+chr(109)+chr(101)+chr(110)+chr(116)+chr(115)+chr(32)+chr(87)+chr(72)+chr(69)+chr(82)+chr(69)+chr(32)+chr(112)+chr(108)+chr(97)+chr(121)+chr(101)+chr(114)+chr(95)+chr(105)+chr(100)+chr(61)+chr(63)
MODEL = chr(99)+chr(108)+chr(97)+chr(117)+chr(100)+chr(101)+chr(45)+chr(115)+chr(111)+chr(110)+chr(110)+chr(101)+chr(116)+chr(45)+chr(52)+chr(45)+chr(54)
ROLE_USER = chr(117)+chr(115)+chr(101)+chr(114)
ROLE_CONTENT = chr(99)+chr(111)+chr(110)+chr(116)+chr(101)+chr(110)+chr(116)
ROLE_KEY = chr(114)+chr(111)+chr(108)+chr(101)
ENV_KEY = chr(67)+chr(76)+chr(65)+chr(85)+chr(68)+chr(69)+chr(95)+chr(65)+chr(80)+chr(73)+chr(95)+chr(75)+chr(69)+chr(89)
DB_NAME = chr(114)+chr(112)+chr(103)+chr(46)+chr(100)+chr(98)

API_KEY = os.environ.get(ENV_KEY) or chr(32)

def init_db():
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()
c.execute(SQL_CREATE_PLAYERS)
c.execute(SQL_CREATE_GRAMMAR)
c.execute(SQL_CREATE_VOCAB)
c.execute(SQL_CREATE_ACH)
conn.commit()
conn.close()

init_db()

def get_db():
return sqlite3.connect(DB_NAME)

def get_player(pid):
conn = get_db()
c = conn.cursor()
c.execute(SQL_GET_PLAYER, (pid,))
row = c.fetchone()
conn.close()
if not row:
return None
keys = [chr(105)+chr(100), chr(110)+chr(97)+chr(109)+chr(101),
chr(108)+chr(101)+chr(118)+chr(101)+chr(108), chr(120)+chr(112),
chr(104)+chr(112), chr(103)+chr(111)+chr(108)+chr(100),
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

R_ROOT = chr(47)
R_CREATE = chr(47)+chr(112)+chr(108)+chr(97)+chr(121)+chr(101)+chr(114)+chr(47)+chr(99)+chr(114)+chr(101)+chr(97)+chr(116)+chr(101)
R_PLAYER = chr(47)+chr(112)+chr(108)+chr(97)+chr(121)+chr(101)+chr(114)+chr(47)+chr(123)+chr(112)+chr(108)+chr(97)+chr(121)+chr(101)+chr(114)+chr(95)+chr(105)+chr(100)+chr(125)
R_ANSWER = chr(47)+chr(97)+chr(110)+chr(115)+chr(119)+chr(101)+chr(114)+chr(47)+chr(115)+chr(117)+chr(98)+chr(109)+chr(105)+chr(116)
R_ANALYSIS = chr(47)+chr(97)+chr(110)+chr(97)+chr(108)+chr(121)+chr(115)+chr(105)+chr(115)+chr(47)+chr(123)+chr(112)+chr(108)+chr(97)+chr(121)+chr(101)+chr(114)+chr(95)+chr(105)+chr(100)+chr(125)
R_VOCAB = chr(47)+chr(118)+chr(111)+chr(99)+chr(97)+chr(98)+chr(47)+chr(114)+chr(101)+chr(118)+chr(105)+chr(101)+chr(119)
R_DUE = chr(47)+chr(118)+chr(111)+chr(99)+chr(97)+chr(98)+chr(47)+chr(100)+chr(117)+chr(101)+chr(47)+chr(123)+chr(112)+chr(108)+chr(97)+chr(121)+chr(101)+chr(114)+chr(95)+chr(105)+chr(100)+chr(125)
R_AIGEN = chr(47)+chr(97)+chr(105)+chr(47)+chr(103)+chr(101)+chr(110)
R_TUTOR = chr(47)+chr(97)+chr(105)+chr(47)+chr(116)+chr(117)+chr(116)+chr(111)+chr(114)
R_ACH = chr(47)+chr(97)+chr(99)+chr(104)+chr(47)+chr(123)+chr(112)+chr(108)+chr(97)+chr(121)+chr(101)+chr(114)+chr(95)+chr(105)+chr(100)+chr(125)

K_OK = chr(111)+chr(107)
K_STATUS = chr(115)+chr(116)+chr(97)+chr(116)+chr(117)+chr(115)
K_SUCCESS = chr(115)+chr(117)+chr(99)+chr(99)+chr(101)+chr(115)+chr(115)
K_PLAYER = chr(112)+chr(108)+chr(97)+chr(121)+chr(101)+chr(114)
K_TYPE = chr(116)+chr(121)+chr(112)+chr(101)
K_RATE = chr(114)+chr(97)+chr(116)+chr(101)
K_ANALYSIS = chr(97)+chr(110)+chr(97)+chr(108)+chr(121)+chr(115)+chr(105)+chr(115)
K_WEAK = chr(119)+chr(101)+chr(97)+chr(107)+chr(95)+chr(116)+chr(121)+chr(112)+chr(101)+chr(115)
K_DUE = chr(100)+chr(117)+chr(101)+chr(95)+chr(99)+chr(111)+chr(117)+chr(110)+chr(116)
K_WORDS = chr(119)+chr(111)+chr(114)+chr(100)+chr(115)
K_WORD = chr(119)+chr(111)+chr(114)+chr(100)
K_QUESTION = chr(113)+chr(117)+chr(101)+chr(115)+chr(116)+chr(105)+chr(111)+chr(110)
K_REPLY = chr(114)+chr(101)+chr(112)+chr(108)+chr(121)
K_ACH = chr(97)+chr(99)+chr(104)+chr(105)+chr(101)+chr(118)+chr(101)+chr(109)+chr(101)+chr(110)+chr(116)+chr(115)
K_KEY = chr(107)+chr(101)+chr(121)
K_EARNED = chr(101)+chr(97)+chr(114)+chr(110)+chr(101)+chr(100)
K_NOT_FOUND = chr(110)+chr(111)+chr(116)+chr(32)+chr(102)+chr(111)+chr(117)+chr(110)+chr(100)
K_NO_KEY = chr(110)+chr(111)+chr(32)+chr(107)+chr(101)+chr(121)
K_AGAIN = chr(97)+chr(103)+chr(97)+chr(105)+chr(110)
K_HARD = chr(104)+chr(97)+chr(114)+chr(100)

@app.get(R_ROOT)
def root():
return {K_STATUS: K_OK}

@app.post(R_CREATE)
def create_player(data: PlayerCreate):
existing = get_player(data.player_id)
if existing:
return {K_SUCCESS: True, K_PLAYER: existing}
conn = get_db()
c = conn.cursor()
now = datetime.now().isoformat()
nm = data.name if data.name else chr(72)+chr(101)+chr(114)+chr(111)
c.execute(SQL_INSERT_PLAYER, (data.player_id, nm, now))
conn.commit()
conn.close()
return {K_SUCCESS: True, K_PLAYER: get_player(data.player_id)}

@app.get(R_PLAYER)
def get_player_api(player_id: str):
p = get_player(player_id)
if not p:
raise HTTPException(status_code=404, detail=K_NOT_FOUND)
return p

@app.post(R_ANSWER)
def submit_answer(data: AnswerSubmit):
conn = get_db()
c = conn.cursor()
now = datetime.now().isoformat()
c.execute(SQL_INSERT_GRAMMAR, (data.player_id, data.zone, data.question_type, 1 if data.correct else 0, now))
if data.correct:
c.execute(SQL_UPDATE_XP, (data.xp_gained, data.player_id))
else:
c.execute(SQL_UPDATE_HP, (data.player_id,))
c.execute(SQL_GET_XP, (data.player_id,))
row = c.fetchone()
if row:
c.execute(SQL_UPDATE_LEVEL, (calc_level(row[0]), data.player_id))
conn.commit()
conn.close()
return {K_SUCCESS: True, K_PLAYER: get_player(data.player_id)}

@app.get(R_ANALYSIS)
def get_analysis(player_id: str):
conn = get_db()
c = conn.cursor()
c.execute(SQL_GET_ANALYSIS, (player_id,))
rows = c.fetchall()
conn.close()
result = []
for row in rows:
rate = round(row[1]/row[2]*100) if row[2] > 0 else 0
result.append({K_TYPE: row[0], K_RATE: rate})
weak = [r[K_TYPE] for r in result if r[K_RATE] < 60]
return {K_ANALYSIS: result, K_WEAK: weak}

@app.post(R_VOCAB)
def review_vocab(data: VocabReview):
conn = get_db()
c = conn.cursor()
c.execute(SQL_GET_VOCAB, (data.player_id, data.word))
row = c.fetchone()
now = datetime.now().isoformat()
interval = 1 if data.rating == K_AGAIN else 3 if data.rating == K_HARD else 7
delta = -0.2 if interval == 1 else -0.1 if interval == 3 else 0.1
next_review = (datetime.now() + timedelta(days=interval)).isoformat()
if row:
new_ease = max(1.3, row[1] + delta)
new_int = 1 if interval == 1 else max(1, int(row[2] * new_ease))
next_review = (datetime.now() + timedelta(days=new_int)).isoformat()
c.execute(SQL_UPDATE_VOCAB, (new_ease, new_int, next_review, now, row[0]))
else:
c.execute(SQL_INSERT_VOCAB, (data.player_id, data.word, data.category, data.difficulty, next_review, interval, now))
conn.commit()
conn.close()
return {K_SUCCESS: True}

@app.get(R_DUE)
def get_due(player_id: str):
conn = get_db()
c = conn.cursor()
now = datetime.now().isoformat()
c.execute(SQL_GET_DUE, (player_id, now))
rows = c.fetchall()
conn.close()
return {K_DUE: len(rows), K_WORDS: [{K_WORD: r[0]} for r in rows]}

@app.post(R_AIGEN)
def gen_question(data: AiQuestion):
if not API_KEY.strip():
raise HTTPException(status_code=500, detail=K_NO_KEY)
weak_str = chr(44).join(data.weak_types) if data.weak_types else chr(103)+chr(101)+chr(110)+chr(101)+chr(114)+chr(97)+chr(108)
prompt = chr(67)+chr(114)+chr(101)+chr(97)+chr(116)+chr(101)+chr(32)+chr(111)+chr(110)+chr(101)+chr(32)+chr(69)+chr(110)+chr(103)+chr(108)+chr(105)+chr(115)+chr(104)+chr(32)+chr(103)+chr(114)+chr(97)+chr(109)+chr(109)+chr(97)+chr(114)+chr(32)+chr(113)+chr(117)+chr(101)+chr(115)+chr(116)+chr(105)+chr(111)+chr(110)+chr(46)+chr(32)+chr(90)+chr(111)+chr(110)+chr(101)+chr(58)+chr(32)+data.zone+chr(46)+chr(32)+chr(87)+chr(101)+chr(97)+chr(107)+chr(58)+chr(32)+weak_str+chr(46)+chr(32)+chr(82)+chr(101)+chr(112)+chr(108)+chr(121)+chr(32)+chr(79)+chr(78)+chr(76)+chr(89)+chr(32)+chr(119)+chr(105)+chr(116)+chr(104)+chr(32)+chr(74)+chr(83)+chr(79)+chr(78)+chr(58)+chr(32)+chr(123)+chr(116)+chr(121)+chr(112)+chr(101)+chr(58)+chr(115)+chr(116)+chr(114)+chr(44)+chr(113)+chr(117)+chr(101)+chr(115)+chr(116)+chr(105)+chr(111)+chr(110)+chr(58)+chr(115)+chr(116)+chr(114)+chr(44)+chr(111)+chr(112)+chr(116)+chr(105)+chr(111)+chr(110)+chr(115)+chr(58)+chr(91)+chr(93)+chr(44)+chr(97)+chr(110)+chr(115)+chr(119)+chr(101)+chr(114)+chr(95)+chr(105)+chr(110)+chr(100)+chr(101)+chr(120)+chr(58)+chr(48)+chr(44)+chr(101)+chr(120)+chr(112)+chr(108)+chr(97)+chr(110)+chr(97)+chr(116)+chr(105)+chr(111)+chr(110)+chr(58)+chr(115)+chr(116)+chr(114)+chr(125)
client = anthropic.Anthropic(api_key=API_KEY.strip())
resp = client.messages.create(
model=MODEL,
max_tokens=400,
messages=[{ROLE_KEY: ROLE_USER, ROLE_CONTENT: prompt}]
)
text = resp.content[0].text.strip()
return {K_SUCCESS: True, K_QUESTION: json.loads(text)}

@app.post(R_TUTOR)
def ai_tutor(data: AiChat):
if not API_KEY.strip():
raise HTTPException(status_code=500, detail=K_NO_KEY)
client = anthropic.Anthropic(api_key=API_KEY.strip())
sys_msg = chr(89)+chr(111)+chr(117)+chr(32)+chr(97)+chr(114)+chr(101)+chr(32)+chr(97)+chr(110)+chr(32)+chr(69)+chr(110)+chr(103)+chr(108)+chr(105)+chr(115)+chr(104)+chr(32)+chr(116)+chr(101)+chr(97)+chr(99)+chr(104)+chr(101)+chr(114)+chr(46)+chr(32)+chr(82)+chr(101)+chr(112)+chr(108)+chr(121)+chr(32)+chr(105)+chr(110)+chr(32)+chr(84)+chr(114)+chr(97)+chr(100)+chr(105)+chr(116)+chr(105)+chr(111)+chr(110)+chr(97)+chr(108)+chr(32)+chr(67)+chr(104)+chr(105)+chr(110)+chr(101)+chr(115)+chr(101)+chr(46)
msgs = data.history + [{ROLE_KEY: ROLE_USER, ROLE_CONTENT: data.message}]
resp = client.messages.create(
model=MODEL,
max_tokens=600,
system=sys_msg,
messages=msgs
)
return {K_REPLY: resp.content[0].text}

@app.get(R_ACH)
def get_achievements(player_id: str):
conn = get_db()
c = conn.cursor()
c.execute(SQL_GET_ACH, (player_id,))
rows = c.fetchall()
conn.close()
return {K_ACH: [{K_KEY: r[0], K_EARNED: r[1]} for r in rows]}
