from typing import List, Dict, Union

import uvicorn
from fastapi import FastAPI, Response, status, Body
from pydantic import BaseModel

from hebsafeharbor import Doc
from hsh_service import hsh_service

app = FastAPI()


class ReadyResponse(BaseModel):
    service: str
    status: str


class DocsRequest(BaseModel):
    docs: List[Dict[str, str]]


class DocItem(BaseModel):
    # TODO consider adding confidence score, etc.
    text: str
    textStartPosition: int
    textEndPosition: int
    textEntityType: str
    explanation: str
    mask: str
    maskStartPosition: int
    maskEndPosition: int
    maskOperator: str


class DocResponse(BaseModel):
    id: str
    text: str
    items: List[DocItem]

    class Config:
        schema_extra = {
            "example":
                {
                    "id": "doc_1",
                    "text": "<שם_> הגיע <תאריך_> <ארגון_> עם תלונות על כאבים בחזה",
                    "items": [
                        {
                            "text": "גדעון לבנה",
                            "textStartPosition": 0,
                            "textEndPosition": 10,
                            "textEntityType": "PERS",
                            "explanation": "HebSpacy",
                            "mask": "<שם_>",
                            "maskStartPosition": 0,
                            "maskEndPosition": 5,
                            "maskOperator": "replace_in_hebrew"
                        },
                        {
                            "text": "ב16.1.2022",
                            "textStartPosition": 16,
                            "textEndPosition": 26,
                            "textEntityType": "DATE",
                            "explanation": "HebSpacy",
                            "mask": "<תאריך_>",
                            "maskStartPosition": 11,
                            "maskEndPosition": 19,
                            "maskOperator": "replace_in_hebrew"
                        },
                        {
                            "text": "לבית החולים שערי צדק",
                            "textStartPosition": 27,
                            "textEndPosition": 47,
                            "textEntityType": "ORG",
                            "explanation": "HebSpacy",
                            "mask": "<ארגון_>",
                            "maskStartPosition": 20,
                            "maskEndPosition": 28,
                            "maskOperator": "replace_in_hebrew"
                        }
                    ]
                }

        }


class DocsResponse(BaseModel):
    docs: List[DocResponse]


def convert_to_response(doc: Doc) -> DocResponse:
    """
    Converts the Doc object to Pydanic DocResponse that would be returned to the client
    """
    items = []
    for mention, mask in zip(doc.consolidated_results, doc.anonymized_text.items):
        item_response = DocItem(text=doc.text[mention.start:mention.end],
                                textStartPosition=mention.start,
                                textEndPosition=mention.end,
                                textEntityType=mention.entity_type,
                                explanation=mention.analysis_explanation.recognizer,
                                mask=mask.text,
                                maskStartPosition=mask.start,
                                maskEndPosition=mask.end,
                                maskOperator=mask.operator)
        items.append(item_response)

    doc_response = DocResponse(id=doc.id, text=doc.anonymized_text.text, items=items)
    return doc_response


@app.get("/")
async def root():
    return {"message": "Welcome to the Hebrew Safe Harbor!"}


@app.post(path="/query", response_model=DocsResponse)
async def query(request: DocsRequest = Body(
    {
        "docs": [
            {
                "id": "doc_1",
                "text": "גדעון לבנה הגיע ב-16.1.2022 לבית החולים שערי צדק עם תלונות על כאבים בחזה"
            }
        ]
    }), response: Response = status.HTTP_200_OK):
    print(request)
    docs_result, response.status_code = hsh_service.query(request.docs)
    if response.status_code == status.HTTP_200_OK:
        results = []
        for doc in docs_result:
            doc_response = convert_to_response(doc)
            results.append(doc_response)
        docs_response = DocsResponse(docs=results)
        return docs_response
    return docs_result


@app.get(path='/ready', response_model=ReadyResponse)
def ready(response: Response):
    result, response.status_code = hsh_service.ready()
    return result


hsh_service.load_async()

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
