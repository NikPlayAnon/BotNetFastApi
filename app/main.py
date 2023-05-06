from typing import Union
from ipaddress import ip_address
from operator import inv
from tkinter.messagebox import NO
from typing import Optional
from fastapi import FastAPI, Path, Request, Form
# from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import redis
import time


app = FastAPI()
# templates = Jinja2Templates(directory="templates/")
cache = redis.Redis(host='redis', port=6379)


class Item(BaseModel):
    Python_version: str
    dist: str
    linux_distribution: str
    system: str
    machine: str
    platform: str
    uname: str
    version: str
    mac_ver: str
    ip_address: str

def get_hit_count():
    retries = 5
    while True:
        try:
            return cache.incr('hits')
        except redis.exceptions.ConnectionError as exc:
            if retries == 0:
                raise exc
            retries -= 1
            time.sleep(0.5)

def get_next_task(ipIdentifier):
    task = ""
    retries = 5
    while True:
        try:
            task = cache.get(ipIdentifier)
            cache.set(ipIdentifier, '123')
            return task
        except redis.exceptions.ConnectionError as exc:
            if retries == 0:
                raise exc
            retries -= 1
            time.sleep(0.5)


@app.get("/")
def home():
    count = get_hit_count()
    return {"Data":f"Test {count}"}

inventory = {
    }

@app.get("/get-item/{item_id}")
def get_item(item_id:int = Path(None,description="The ID of the item you want to view")):
    return inventory[item_id]


@app.get("/get-by-name")
def get_item(name: str = None):
    for item_id in inventory:
        if inventory[item_id].name == name:
            return inventory[item_id]
    return {"Data":"Not found"}

@app.post("/create-item")
def create_item(item:Item):
    inventory[inventory.__len__()] = item
    task = str(get_next_task(item.ip_address))[2:-1]
    if task == None:
        task = get_next_task(item.ip_address)
    if inventory[inventory.__len__()-1].system == "Windows":
        temp = []
        with open(f'Windows/{task}','r') as f:
            temp = f.readlines()
        return {"system":"Windows", "todo":temp}
    if inventory[inventory.__len__()-1].system == "Linux":
        temp = []
        with open(f'Linux/{task}','r') as f:
            temp = f.readlines()
        return {"system":"Linux", "todo":temp}
    return {"item_id":inventory.__len__()-1}

@app.post("/set-task-to-ip")
def assign_task_to_ip(task: str = None, ip: str = None):
    retries = 5
    try:
        cache.set(ip, task)
        return "Ok"
    except redis.exceptions.ConnectionError as exc:
        if retries == 0:
            raise exc
        retries -= 1
        time.sleep(0.5)
    return "Time out"