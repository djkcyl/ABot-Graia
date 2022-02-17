import json
import random

from pathlib import Path

from .gamedata import props

DATAFILE = Path(__file__).parent.joinpath("data.json")
DATA = None

if DATAFILE.exists():
    with DATAFILE.open("r", encoding="utf-8") as f:
        data = json.load(f)
else:
    with DATAFILE.open("w", encoding="utf-8") as f:
        data = {"users": {}}
        json.dump(data, f, ensure_ascii=False, indent=2)


def init_user(user_id: int):
    if str(user_id) not in data["users"]:
        data["users"][str(user_id)] = {"wins": 0, "props": {}}
        with DATAFILE.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def get_wins(user_id: int):
    init_user(user_id)
    return data["users"][str(user_id)]["wins"]


def add_wins(user_id: int):
    init_user(user_id)
    data["users"][str(user_id)]["wins"] += 1
    with DATAFILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_props(user_id: int):
    init_user(user_id)
    return data["users"][str(user_id)].get("props", {})


def get_random_prop():
    weights = []
    for _, v in props.items():
        _, _, _, weight = v
        weights.append(weight)
    return random.choices(list(props.keys()), weights, k=1)[0]


def use_prop(user_id: int, prop: str):
    if data["users"][str(user_id)]["props"].get(prop, 0) > 0:
        data["users"][str(user_id)]["props"][prop] -= 1
        with DATAFILE.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    else:
        return False


def add_prop(user_id: int, prop: str, amount: int = 1):
    init_user(user_id)
    if prop not in data["users"][str(user_id)]["props"]:
        data["users"][str(user_id)]["props"][prop] = amount
    else:
        data["users"][str(user_id)]["props"][prop] += amount
    with DATAFILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def reduce_prop(user_id: int, prop: str, amount: int):
    init_user(user_id)
    if prop not in data["users"][str(user_id)]["props"]:
        return
    data["users"][str(user_id)]["props"][prop] -= amount
    with DATAFILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
