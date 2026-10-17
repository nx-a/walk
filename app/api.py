"""HTTP-слой. Обработчики синхронные (def): psycopg2 блокирующий, FastAPI
выполнит их в пуле потоков и не заблокирует event loop."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status

from .schemas import (
    DogIn,
    DogOut,
    HelperIn,
    HelperOut,
    KennelIn,
    KennelOut,
    WalkFinishIn,
    WalkIn,
    WalkOut,
)
from .services import DogService, HelperService, KennelService, WalkService


class Services:
    """Контейнер сервисов, создаётся один раз при старте приложения."""

    def __init__(self, db) -> None:
        self.kennels = KennelService(db)
        self.dogs = DogService(db)
        self.helpers = HelperService(db)
        self.walks = WalkService(db)


def get_services(request: Request) -> Services:
    return request.app.state.services


router = APIRouter(prefix="/api")
NO_CONTENT = {"status_code": status.HTTP_204_NO_CONTENT}


# --- Будки ---

@router.get("/kennels", response_model=list[KennelOut], tags=["kennels"])
def list_kennels(s: Services = Depends(get_services)):
    return s.kennels.list()


@router.post("/kennels", response_model=KennelOut, status_code=201, tags=["kennels"])
def create_kennel(body: KennelIn, s: Services = Depends(get_services)):
    return s.kennels.create(body.model_dump())


@router.put("/kennels/{kennel_id}", response_model=KennelOut, tags=["kennels"])
def update_kennel(kennel_id: int, body: KennelIn, s: Services = Depends(get_services)):
    return s.kennels.update(kennel_id, body.model_dump())


@router.delete("/kennels/{kennel_id}", tags=["kennels"], **NO_CONTENT)
def delete_kennel(kennel_id: int, s: Services = Depends(get_services)):
    s.kennels.delete(kennel_id)


# --- Собаки ---

@router.get("/dogs", response_model=list[DogOut], tags=["dogs"])
def list_dogs(s: Services = Depends(get_services)):
    return [DogOut.of(d) for d in s.dogs.list()]


@router.get("/dogs/{dog_id}", response_model=DogOut, tags=["dogs"])
def get_dog(dog_id: int, s: Services = Depends(get_services)):
    return DogOut.of(s.dogs.get(dog_id))


@router.post("/dogs", response_model=DogOut, status_code=201, tags=["dogs"])
def create_dog(body: DogIn, s: Services = Depends(get_services)):
    return DogOut.of(s.dogs.create(body.model_dump()))


@router.put("/dogs/{dog_id}", response_model=DogOut, tags=["dogs"])
def update_dog(dog_id: int, body: DogIn, s: Services = Depends(get_services)):
    return DogOut.of(s.dogs.update(dog_id, body.model_dump()))


@router.delete("/dogs/{dog_id}", tags=["dogs"], **NO_CONTENT)
def delete_dog(dog_id: int, s: Services = Depends(get_services)):
    s.dogs.delete(dog_id)


# --- Помощники ---

@router.get("/helpers", response_model=list[HelperOut], tags=["helpers"])
def list_helpers(s: Services = Depends(get_services)):
    return s.helpers.list()


@router.post("/helpers", response_model=HelperOut, status_code=201, tags=["helpers"])
def create_helper(body: HelperIn, s: Services = Depends(get_services)):
    return s.helpers.create(body.model_dump())


@router.put("/helpers/{helper_id}", response_model=HelperOut, tags=["helpers"])
def update_helper(helper_id: int, body: HelperIn, s: Services = Depends(get_services)):
    return s.helpers.update(helper_id, body.model_dump())


@router.delete("/helpers/{helper_id}", tags=["helpers"], **NO_CONTENT)
def delete_helper(helper_id: int, s: Services = Depends(get_services)):
    s.helpers.delete(helper_id)


# --- Прогулки ---

@router.get("/walks", response_model=list[WalkOut], tags=["walks"])
def list_walks(
    dog_id: int | None = None,
    helper_id: int | None = None,
    active: bool | None = None,
    s: Services = Depends(get_services),
):
    return s.walks.search(dog_id=dog_id, helper_id=helper_id, active=active)


@router.post("/walks", response_model=WalkOut, status_code=201, tags=["walks"])
def create_walk(body: WalkIn, s: Services = Depends(get_services)):
    return s.walks.create(body.model_dump())


@router.post("/walks/{walk_id}/finish", response_model=WalkOut, tags=["walks"])
def finish_walk(
    walk_id: int, body: WalkFinishIn | None = None, s: Services = Depends(get_services)
):
    return s.walks.finish(walk_id, body.ended_at if body else None)


@router.delete("/walks/{walk_id}", tags=["walks"], **NO_CONTENT)
def delete_walk(walk_id: int, s: Services = Depends(get_services)):
    s.walks.delete(walk_id)
