from pydantic import BaseModel

from . import ResponseModel


class Tags(BaseModel):
    Keyword: str
    Score: float
    SubLabel: str


class DetailResults(BaseModel):
    Keywords: list[str]
    Label: str
    LibId: str
    LibName: str
    LibType: int
    Score: int
    SubLabel: str
    Suggestion: str
    Tags: list[Tags]


class Response(BaseModel):
    BizType: str
    ContextText: str
    DataId: str
    DetailResults: list[DetailResults]
    Extra: str
    Keywords: list[str]
    Label: str
    RequestId: str
    RiskDetails: list[str]
    Score: int
    SubLabel: str
    Suggestion: str


class TMSResponseModel(ResponseModel):
    Response: Response
