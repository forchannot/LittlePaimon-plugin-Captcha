import asyncio
import copy
import json
import random
import string
import time
from typing import Dict, Optional

from LittlePaimon.database import PrivateCookie
from LittlePaimon.utils.api import (
    SIGN_INFO_API,
    SIGN_REWARD_API,
    get_cookie,
    md5,
    random_hex,
    random_text,
)
from LittlePaimon.utils.requests import aiorequests

from ..api.api import (
    BBS_CAPATCH,
    BBS_CAPTCHA_VERIFY,
    mihoyobbs_salt,
    mihoyobbs_salt_web,
    mihoyobbs_salt_x4,
    mihoyobbs_salt_x6,
    mihoyobbs_version,
)
from ..config.config import config
from ..utils.logger import Logger

_HEADER = {
    "x-rpc-app_version": mihoyobbs_version,
    "User-Agent": "Mozilla/5.0 (Linux; Android 12; Unspecified Device) AppleWebKit/537.36 (KHTML, like Gecko) "
    f"Version/4.0 Chrome/103.0.5060.129 Mobile Safari/537.36 miHoYoBBS/{mihoyobbs_version}",
    "x-rpc-client_type": "5",
    "Referer": "https://webstatic.mihoyo.com/",
    "Origin": "https://webstatic.mihoyo.com",
}


def mihoyo_headers(cookie, challenge, q="", b=None) -> Dict:
    return {
        "DS": get_ds_x6(q, b),
        "Origin": "https://webstatic.mihoyo.com",
        "Cookie": cookie,
        "x-rpc-app_version": mihoyobbs_version,
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS "
        f"X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/{mihoyobbs_version}",
        "x-rpc-client_type": "5",
        "Referer": "https://webstatic.mihoyo.com/",
        "x-rpc-challenge": challenge,
    }


async def get_sign_list() -> Dict:
    req = await aiorequests.get(
        url=SIGN_REWARD_API,
        headers=_HEADER,
        params={"act_id": "e202009291139501"},
    )
    data = req.json()
    return data


async def get_sign_info(user_id: str, uid: str) -> Dict:
    cookie_info = await PrivateCookie.get_or_none(user_id=user_id, uid=uid)
    server_id = "cn_qd01" if uid[0] == "5" else "cn_gf01"
    header = copy.deepcopy(_HEADER)
    header["Cookie"] = cookie_info.cookie
    req = await aiorequests.get(
        url=SIGN_INFO_API,
        headers=header,
        params={"act_id": "e202009291139501", "region": server_id, "uid": uid},
    )
    data = req.json()
    return data


# 时间戳
def timestamp() -> int:
    return int(time.time())


def get_ds2(web: bool) -> str:
    if web:
        n = mihoyobbs_salt_web
    else:
        n = mihoyobbs_salt
    i = str(timestamp())
    r = random_text(6)
    c = md5("salt=" + n + "&t=" + i + "&r=" + r)
    return f"{i},{r},{c}"


def get_ds_x6(q: str = "", b: Dict = None, sign: bool = False) -> str:
    b = json.dumps(b) if b else ""
    if sign:
        n = mihoyobbs_salt_x6
    else:
        n = mihoyobbs_salt_x4
    i = str(int(time.time()))
    r = str(random.randint(100000, 200000))
    add = f"&b={b}&q={q}"
    c = md5("salt=" + n + "&t=" + i + "&r=" + r + add)
    return f"{i},{r},{c}"


async def get_pass_challenge(uid: str, user_id: str, way: str):
    cookie_info = await get_cookie(user_id, uid, True, True)
    headers = {
        "DS": get_ds2(web=False),
        "cookie": cookie_info.stoken,
        "x-rpc-client_type": "2",
        "x-rpc-app_version": mihoyobbs_version,
        "x-rpc-sys_version": "12",
        "x-rpc-channel": "miyousheluodi",
        "x-rpc-device_id": random_hex(32),
        "x-rpc-device_name": "".join(
            random.sample(
                string.ascii_lowercase + string.digits, random.randint(1, 10)
            )
        ),
        "x-rpc-device_model": "Mi 10",
        "Referer": "https://app.mihoyo.com",
        "Host": "bbs-api.mihoyo.com",
        "User-Agent": "okhttp/4.8.0",
    }
    req = await aiorequests.get(url=BBS_CAPATCH, headers=headers)
    data = req.json()
    if data["retcode"] != 0:
        return None
    validate, _ = await get_validate(
        data["data"]["gt"],
        data["data"]["challenge"],
        "https://webstatic.mihoyo.com/bbs/event/signin-ys/index.html?bbs_auth_required=true&act_id"
        "=e202009291139501&utm_source=bbs&utm_medium=mys&utm_campaign=icon",
        way,
    )
    if validate != "j":
        check_req = await aiorequests.post(
            url=BBS_CAPTCHA_VERIFY,
            headers=headers,
            json={
                "geetest_challenge": data["data"]["challenge"],
                "geetest_seccode": validate + "|jordan",
                "geetest_validate": validate,
            },
        )
        check = check_req.json()
        if check["retcode"] == 0:
            return check["data"]["challenge"]
    return None


async def get_validate(gt: str, challenge: str, referer: str, choose: str):
    """validate,challenge"""
    if choose == "rr":
        validate, challenge = await rrocr(gt, challenge, referer)
    elif choose == "sf":
        validate, challenge = await other_api(gt, challenge)
    elif choose == "tt":
        validate, challenge = await ttocr(gt, challenge, referer)
    else:
        validate, challenge = "j", "j"
    return validate, challenge  # 失败返回'j' 成功返回validate


async def other_api(gt: str, challenge: str):
    try:
        response = await aiorequests.get(
            url=f"{config.third_api}gt={gt}&challenge={challenge}", timeout=60
        )
    except Exception as e:
        Logger.info("[第三方]", info="➤➤", result=f"请求失败{e}", result_type=False)
        return "j", "j"
    if response.status_code != 200:
        Logger.info("[第三方]", info="➤➤", result="请求失败", result_type=False)
        return "j", "j"
    data = response.json()
    if "data" in data and "validate" in data["data"]:
        Logger.info("[第三方]", info="➤➤", result="成功", result_type=True)
        validate, challenge = (
            data["data"]["validate"],
            data["data"]["challenge"],
        )
        return validate, challenge
    else:
        return "j", "j"


async def rrocr(gt: str, challenge: str, referer: str):
    ji_fen = await gain_num("rr")
    if int(ji_fen) < 10:
        Logger.info("[人人打码]", info="➤➤", result="积分不足", result_type=False)
        return "j", "j"
    params = {
        "appkey": config.rrocr_key,
        "gt": gt,
        "challenge": challenge,
        "referer": referer,
        "sharecode": "585dee4d4ef94e1cb95d5362a158ea54",
    }
    try:
        response = await aiorequests.post(
            url="http://api.rrocr.com/api/recognize.html",
            params=params,
            timeout=60,
        )
    except Exception as e:
        Logger.info("[人人打码]", info="➤➤", result=f"请求失败{e}", result_type=False)
        return "j", "j"
    if response.status_code != 200:
        Logger.info("[人人打码]", info="➤➤", result="请求失败", result_type=False)
        return "j", "j"
    data = response.json()
    if "data" in data and "validate" in data["data"]:
        Logger.info("[人人打码]", info="➤➤", result="成功", result_type=True)
        validate, challenge = (
            data["data"]["validate"],
            data["data"]["challenge"],
        )
        return validate, challenge
    else:
        Logger.info(
            "[人人打码]", info="➤➤", result=data["msg"], result_type=False
        )  # 打码失败输出错误信息,返回'j'
        return "j", "j"  # 失败返回'j' 成功返回validate


async def ttocr(gt: str, challenge: str, referer: str):
    ji_fen = await gain_num("tt")
    if int(ji_fen) < 10:
        Logger.info("[套套打码]", info="➤➤", result="积分不足", result_type=False)
        return "j", "j"
    data = {
        "appkey": config.ttocr_key,
        "gt": gt,
        "challenge": challenge,
        "itemid": 388,
        "referer": referer,
    }
    try:
        get_id = await aiorequests.post(
            url="http://api.ttocr.com/api/recognize",
            data=data,
            timeout=60,
        )
    except Exception as e:
        Logger.info("[套套打码]", info="➤➤", result=f"请求失败{e}", result_type=False)
        return "j", "j"
    if get_id.status_code != 200:
        Logger.info("[套套打码]", info="➤➤", result="验证失败", result_type=False)
        return "j", "j"
    get_id = get_id.json()
    result_id = get_id["resultid"]
    Logger.info("[套套打码]", info="➤➤", result="等待15s获取结果", result_type=True)
    await asyncio.sleep(15)
    for i in range(5):
        try:
            res = await aiorequests.post(
                url="http://api.ttocr.com/api/results",
                data={
                    "appkey": config.ttocr_key,
                    "resultid": result_id,
                },
                timeout=60,
            )
        except Exception as e:
            Logger.info(
                "[套套打码]", info="➤➤", result=f"第{1+1}请求失败{e}", result_type=False
            )
            await asyncio.sleep(1.5)
            continue
        if res.status_code == 200:
            if "msg" in res.json() and res.json()["msg"] == "等待识别结果":
                await asyncio.sleep(1.5)
                continue
            break
        else:
            Logger.info(
                "[套套打码]",
                info="➤➤",
                result=f"获取结果第{1+1}请求失败，等待1.5s后重试",
                result_type=False,
            )
            await asyncio.sleep(1.5)
    else:
        Logger.info(
            "[套套打码]", info="➤➤", result="请求失败,可能是网络原因", result_type=False
        )
        return "j", "j"
    res = res.json()
    # 失败返回'j' 成功返回validate
    if "data" in res and "validate" in res["data"]:
        Logger.info("[套套打码]", info="➤➤", result="成功", result_type=True)
        validate, challenge = res["data"]["validate"], res["data"]["challenge"]
        return validate, challenge
    else:
        Logger.info(
            "[套套打码]", info="➤➤", result=res["msg"], result_type=False
        )  # 打码失败输出错误信息,返回'j'
        return "j", "j"


async def gain_num(choice) -> Optional[str]:
    options = {
        "rr": {
            "url": f"http://api.rrocr.com/api/integral.html?appkey={config.rrocr_key}",
            "info_key": "integral",
            "success_info": ["status", 0],
        },
        "sf": {
            "url": config.third_api.replace("geetest", "token"),
            "info_key": "times",
            "success_info": ["info", "success"],
        },
        "tt": {
            "url": f"http://api.ttocr.com/api/points?appkey={config.ttocr_key}",
            "info_key": "points",
            "success_info": ["status", 1],
        },
    }
    option = options.get(choice)
    info = option.get("info_key")
    success = option.get("success_info")
    try:
        data = await aiorequests.get(option.get("url"))
    except Exception as e:
        Logger.info(
            f"[{choice}打码]查询积分", info="➤➤", result=f"请求失败{e}", result_type=False
        )
        return None
    if data.status_code != 200:
        return None
    data = data.json()
    if data.get(success[0]) == success[1]:
        key_num = data.get(info, None)
        if key_num is None:
            return None
        return str(2333 - int(key_num)) if choice == "sf" else str(key_num)
    return None
