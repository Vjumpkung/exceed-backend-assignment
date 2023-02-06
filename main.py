from fastapi import FastAPI, HTTPException, Body
from datetime import date
from pymongo import MongoClient
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import urllib

DATABASE_NAME = "exceed06"
COLLECTION_NAME = "reservation_vjump"
MONGO_DB_URL = "mongodb://localhost"
MONGO_DB_PORT = 27017


class Reservation(BaseModel):
    name: str
    start_date: date
    end_date: date
    room_id: int


load_dotenv(".env")
_username = urllib.parse.quote(os.getenv("user"))
_password = urllib.parse.quote(os.getenv("pass"))

# client = MongoClient(f"{MONGO_DB_URL}:{MONGO_DB_PORT}")
client = MongoClient(
    "mongo.exceed19.online", port=8443, username=_username, password=_password
)

db = client[DATABASE_NAME]

collection = db[COLLECTION_NAME]

app = FastAPI()


def room_avaliable(room_id: int, start_date: str, end_date: str):
    query = {
        "room_id": room_id,
        "$or": [
            {
                "$and": [
                    {"start_date": {"$lte": start_date}},
                    {"end_date": {"$gte": start_date}},
                ]
            },
            {
                "$and": [
                    {"start_date": {"$lte": end_date}},
                    {"end_date": {"$gte": end_date}},
                ]
            },
            {
                "$and": [
                    {"start_date": {"$gte": start_date}},
                    {"end_date": {"$lte": end_date}},
                ]
            },
        ],
    }

    result = collection.find(query, {"_id": 0})
    list_cursor = list(result)

    return not len(list_cursor) > 0


@app.get("/reservation/by-name/{name}")
def get_reservation_by_name(name: str):
    query = {"name": name}
    filter = {"_id": 0}
    result = collection.find(query, filter)
    return {"result": list(result)}


@app.get("/reservation/by-room/{room_id}")
def get_reservation_by_room(room_id: int):
    query = {"room_id": room_id}
    filter = {"_id": 0}
    result = collection.find(query, filter)
    return {"result": list(result)}


@app.post("/reservation")
def reserve(reservation: Reservation):
    if reservation.start_date > reservation.end_date:
        raise HTTPException(400)
    elif reservation.room_id > 10 or reservation.room_id < 1:
        raise HTTPException(400)
    elif not room_avaliable(
        reservation.room_id, str(reservation.start_date), str(reservation.end_date)
    ):
        raise HTTPException(400)
    collection.insert_one(
        {
            "name": reservation.name,
            "start_date": str(reservation.start_date),
            "end_date": str(reservation.end_date),
            "room_id": reservation.room_id,
        }
    )
    return list(
        collection.find(
            {
                "name": reservation.name,
                "start_date": str(reservation.start_date),
                "end_date": str(reservation.end_date),
                "room_id": reservation.room_id,
            },
            {"_id": 0},
        )
    )


@app.put("/reservation/update")
def update_reservation(
    reservation: Reservation, new_start_date: date = Body(), new_end_date: date = Body()
):
    if new_start_date > new_end_date:
        raise HTTPException(400)
    elif not room_avaliable(
        reservation.room_id, str(new_start_date), str(new_end_date)
    ):
        raise HTTPException(400)
    collection.update_one(
        {
            "name": reservation.name,
            "start_date": str(reservation.start_date),
            "end_date": str(reservation.end_date),
            "room_id": reservation.room_id,
        },
        {
            "$set": {
                "start_date": str(new_start_date),
                "end_date": str(new_end_date),
            }
        },
    )
    return list(
        collection.find(
            {
                "name": reservation.name,
                "start_date": str(new_start_date),
                "end_date": str(new_end_date),
                "room_id": reservation.room_id,
            },
            {"_id": 0},
        )
    )


@app.delete("/reservation/delete")
def cancel_reservation(reservation: Reservation):
    collection.delete_one(
        {
            "name": reservation.name,
            "start_date": str(reservation.start_date),
            "end_date": str(reservation.end_date),
            "room_id": reservation.room_id,
        }
    )
    return [reservation]
