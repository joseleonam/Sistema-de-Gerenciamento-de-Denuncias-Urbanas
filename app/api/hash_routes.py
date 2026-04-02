from hashlib import md5, sha1, sha256

from fastapi import APIRouter, HTTPException

from pydantic import BaseModel, Field

router = APIRouter()


class HashRequest(BaseModel):
    text: str
    algorithm: str = Field(..., regex="^(md5|sha1|sha256)$")


class HashResponse(BaseModel):
    algorithm: str
    value: str


@router.post("/", response_model=HashResponse)
def compute_hash(payload: HashRequest):
    data = payload.text.encode("utf-8")
    if payload.algorithm == "md5":
        digest = md5(data).hexdigest()
    elif payload.algorithm == "sha1":
        digest = sha1(data).hexdigest()
    elif payload.algorithm == "sha256":
        digest = sha256(data).hexdigest()
    else:
        raise HTTPException(status_code=400, detail="Algoritmo inválido")

    return HashResponse(algorithm=payload.algorithm, value=digest)
