import time as t

from beanie import Document, Indexed


class ABotTurnoverData(Document):
    time: int = t.time()
    from_qid: Indexed(int)
    to_qid: int
    amount: int
    reason: str = None
    operator: int
