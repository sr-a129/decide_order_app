
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
import csv
import io
import random

app = FastAPI()

class Player(BaseModel):
    name: str
    gender: str
    grade: int
    level: int
    want_pair: Optional[str] = ""
    avoid_pair: Optional[str] = ""

def split_red_white(players):
    levels = {}

    for p in players:
        levels.setdefault(p["level"], []).append(p)

    red = []
    white = []

    for level_players in levels.values():
        random.shuffle(level_players)

        for i, p in enumerate(level_players):
            if i % 2 == 0:
                red.append(p)
            else:
                white.append(p)

    return red, white

def generate_matches(players, court_count):
    random.shuffle(players)

    matches = []
    round_num = 1
    court = 1

    for i in range(0, len(players) - 3, 4):
        pair1 = [players[i]["name"], players[i+1]["name"]]
        pair2 = [players[i+2]["name"], players[i+3]["name"]]

        matches.append({
            "court": court,
            "round": round_num,
            "pair1": pair1,
            "pair2": pair2,
            "status": "waiting"
        })

        court += 1

        if court > court_count:
            court = 1
            round_num += 1

    return matches

@app.get("/")
def root():
    return {"message": "Tennis Match Manager API"}

@app.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    content = await file.read()

    decoded = content.decode("utf-8")
    csv_reader = csv.DictReader(io.StringIO(decoded))

    players = []

    for row in csv_reader:
        players.append({
            "name": row["名前"],
            "gender": row["性別"],
            "grade": int(row["学年"]),
            "level": int(row["実力"]),
            "want_pair": row.get("組みたい", ""),
            "avoid_pair": row.get("組みたくない", "")
        })

    return {
        "count": len(players),
        "players": players
    }

@app.post("/generate")
async def generate(
    file: UploadFile = File(...),
    court_count: int = 3
):
    content = await file.read()

    decoded = content.decode("utf-8")
    csv_reader = csv.DictReader(io.StringIO(decoded))

    players = []

    for row in csv_reader:
        players.append({
            "name": row["名前"],
            "gender": row["性別"],
            "grade": int(row["学年"]),
            "level": int(row["実力"]),
            "want_pair": row.get("組みたい", ""),
            "avoid_pair": row.get("組みたくない", "")
        })

    red, white = split_red_white(players)
    matches = generate_matches(players, court_count)

    return {
        "red_team": [p["name"] for p in red],
        "white_team": [p["name"] for p in white],
        "matches": matches
    }
