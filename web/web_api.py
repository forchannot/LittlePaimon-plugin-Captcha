import datetime
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..config.config import ConfigManager

from LittlePaimon.web.api import BaseApiRouter
from LittlePaimon.web.api.utils import authentication

route = APIRouter()


@route.get(
    "/abyss_config_g", response_class=JSONResponse, dependencies=[authentication()]
)
async def abyss_config_g():
    config = ConfigManager.config.dict(by_alias=True)
    config["米游社验证签到开始时间"] = datetime.datetime(
        1970, 1, 1, hour=config["米游社验证签到开始时间(小时)"], minute=config["米游社验证签到开始时间(分钟)"]
    ).strftime("%H:%M")
    config["米游币验证开始执行时间"] = datetime.datetime(
        1970, 1, 1, hour=config["米游币验证开始执行时间(小时)"], minute=config["米游币验证开始执行时间(分钟)"]
    ).strftime("%H:%M")
    return {"status": 0, "msg": "ok", "data": config}


@route.post(
    "/abyss_config", response_class=JSONResponse, dependencies=[authentication()]
)
async def abyss_config(data: dict):
    if "米游社验证签到开始时间" in data:
        temp_time = datetime.datetime.strptime(data["米游社验证签到开始时间"], "%H:%M")
        data["米游社验证签到开始时间(小时)"] = temp_time.hour
        data["米游社验证签到开始时间(分钟)"] = temp_time.minute
    if "米游币验证开始执行时间" in data:
        temp_time = datetime.datetime.strptime(data["米游币验证开始执行时间"], "%H:%M")
        data["米游币验证开始执行时间(小时)"] = temp_time.hour
        data["米游币验证开始执行时间(分钟)"] = temp_time.minute
    if "实时便签验证停止检查时间段" in data:
        temp_time_split = data["实时便签验证停止检查时间段"].split(",")
        data["实时便签验证停止检查开始时间"] = int(temp_time_split[0][:2])
        data["实时便签验证停止检查结束时间"] = int(temp_time_split[1][:2])
    ConfigManager.config.update(**data)
    ConfigManager.save()
    return {"status": 0, "msg": "保存成功"}


BaseApiRouter.include_router(route)
