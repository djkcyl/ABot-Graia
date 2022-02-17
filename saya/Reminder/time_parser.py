import time
import jionlp


async def time_parser(timestr: str) -> str:
    data = jionlp.ner.extract_time(timestr, time_base=time.time())
    if len(data) != 1:
        return False
    elif "detail" not in data[0]:
        return False
    elif "time" not in data[0]["detail"]:
        return False
    else:
        return data[0]["detail"]["time"][0]
