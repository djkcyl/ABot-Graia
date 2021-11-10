import os
import json

from database.database import add_word


bookid = {
    "CET4luan_1": {"name": "四级真题核心词", "id": "1"},
    "CET6luan_1": {"name": "六级真题核心词", "id": "2"},
    "KaoYanluan_1": {"name": "考研必考词汇", "id": "3"},
    "Level4luan_1": {"name": "专四真题高频词", "id": "4"},
    "Level8_1": {"name": "专八真题高频词", "id": "5"},
    "IELTSluan_2": {"name": "雅思词汇", "id": "6"},
    "TOEFL_2": {"name": "TOEFL 词汇", "id": "7"},
    "ChuZhongluan_2": {"name": "中考必备词汇", "id": "8"},
    "GaoZhongluan_2": {"name": "高考必备词汇", "id": "9"},
    "PEPXiaoXue3_1": {"name": "人教版小学英语-三年级上册", "id": "10"},
    "PEPChuZhong7_1": {"name": "人教版初中英语-七年级上册", "id": "11"},
    "PEPGaoZhong": {"name": "人教版高中英语-必修", "id": "12"},
    "ChuZhong_2": {"name": "初中英语词汇", "id": "13"},
    "GaoZhong_2": {"name": "高中英语词汇", "id": "14"},
    "BEC_2": {"name": "商务英语词汇", "id": "15"},
}


def replaceFran(str):
    fr_en = [
        ["é", "e"],
        ["ê", "e"],
        ["è", "e"],
        ["ë", "e"],
        ["à", "a"],
        ["â", "a"],
        ["ç", "c"],
        ["î", "i"],
        ["ï", "i"],
        ["ô", "o"],
        ["ù", "u"],
        ["û", "u"],
        ["ü", "u"],
        ["ÿ", "y"],
    ]
    for i in fr_en:
        str = str.replace(i[0], i[1])
    return str


for filename in os.listdir("./saya/EnglishTest/worddict"):
    with open("./saya/EnglishTest/worddict/" + filename, "r", encoding="utf-8") as f:
        for line in f.readlines():
            words = line.strip()
            word_json = json.loads(words)
            word_pop = []
            word_tran = []
            for tran in word_json["content"]["word"]["content"]["trans"]:
                if "pos" in tran:
                    word_pop.append(tran["pos"])
                word_tran.append(tran["tranCn"])
            data = [
                replaceFran(word_json["headWord"]),
                "&".join(word_pop),
                "&".join(word_tran),
                bookid[word_json["bookId"]]["id"],
            ]
            add_word(data)
