import copy
import random
import re
import string
import time
from typing import Union
import httpx

from LittlePaimon.database import PrivateCookie
from LittlePaimon.utils.api import (
    SIGN_INFO_API,
    get_cookie,
    random_hex,
    get_ds,
    md5,
    SIGN_REWARD_API,
)

from nonebot import logger

from ..api.api import BBS_CAPATCH, BBS_CAPTCHA_VERIFY
from ..config.config import config

http = httpx.Client(timeout=20, transport=httpx.HTTPTransport(retries=10))

_HEADER = {
    "x-rpc-app_version": "2.11.1",
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.11.1"
    ),
    "x-rpc-client_type": "5",
    "Referer": "https://webstatic.mihoyo.com/",
    "Origin": "https://webstatic.mihoyo.com",
}


def mihoyo_headers(cookie, challenge, q="", b=None) -> dict:
    return {
        "DS": get_ds(q, b),
        "Origin": "https://webstatic.mihoyo.com",
        "Cookie": cookie,
        "x-rpc-app_version": "2.11.1",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS "
        "X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.11.1",
        "x-rpc-client_type": "5",
        "Referer": "https://webstatic.mihoyo.com/",
        "x-rpc-challenge": challenge,
    }


def query_score():
    response = http.get(
        "http://api.rrocr.com/api/integral.html?appkey=" + config.rrocr_key
    )
    data = response.json()
    if data["status"] == -1:
        logger.info("查询积分失败")
        return True, "查询积分失败"
    integral = data["integral"]
    if int(integral) < 10:
        logger.info("积分不足")
        return True, f"积分还剩{integral}"
    logger.info("积分还剩" + integral)
    return False, f"积分还剩{integral}"


async def get_sign_list() -> dict:
    req = http.get(
        url=SIGN_REWARD_API, headers=_HEADER, params={"act_id": "e202009291139501"}
    )
    data = req.json()
    return data


async def get_sign_info(user_id: str, uid: str) -> Union[dict, str]:
    cookie_info = await PrivateCookie.get_or_none(user_id=user_id, uid=uid)
    server_id = "cn_qd01" if uid[0] == "5" else "cn_gf01"
    header = copy.deepcopy(_HEADER)
    header["Cookie"] = cookie_info.cookie
    req = http.get(
        url=SIGN_INFO_API,
        headers=header,
        params={"act_id": "e202009291139501", "region": server_id, "uid": uid},
    )
    data = req.json()
    return data


# 时间戳
def timestamp() -> int:
    return int(time.time())


# 随机文本
def random_text(num: int) -> str:
    return "".join(random.sample(string.ascii_lowercase + string.digits, num))


def get_ds2(web: bool) -> str:
    if web:
        n = "yUZ3s0Sna1IrSNfk29Vo6vRapdOyqyhB"
    else:
        n = "PVeGWIZACpxXZ1ibMVJPi9inCY4Nd4y2"
    i = str(timestamp())
    r = random_text(6)
    c = md5("salt=" + n + "&t=" + i + "&r=" + r)
    return f"{i},{r},{c}"


async def get_pass_challenge(uid: str, user_id: str, way: bool):
    cookie_info = await get_cookie(user_id, uid, True, True)
    headers = {
        "DS": get_ds2(web=False),
        "cookie": cookie_info.stoken,
        "x-rpc-client_type": "2",
        "x-rpc-app_version": "2.38.1",
        "x-rpc-sys_version": "12",
        "x-rpc-channel": "miyousheluodi",
        "x-rpc-device_id": random_hex(32),
        "x-rpc-device_name": "".join(
            random.sample(string.ascii_lowercase + string.digits, random.randint(1, 10))
        ),
        "x-rpc-device_model": "Mi 10",
        "Referer": "https://app.mihoyo.com",
        "Host": "bbs-api.mihoyo.com",
        "User-Agent": "okhttp/4.8.0",
    }
    req = http.get(url=BBS_CAPATCH, headers=headers)
    data = req.json()
    if data["retcode"] != 0:
        return None
    validate, _ = get_validate(
        data["data"]["gt"],
        data["data"]["challenge"],
        "https://webstatic.mihoyo.com/bbs/event/signin-ys/index.html?bbs_auth_required=true&act_id"
        "=e202009291139501&utm_source=bbs&utm_medium=mys&utm_campaign=icon",
        way
    )
    if validate != "j":
        check_req = http.post(
            url=BBS_CAPTCHA_VERIFY,
            headers=headers,
            json={
                "geetest_challenge": data["data"]["challenge"],
                "geetest_seccode": validate + "|jordan",
                "geetest_validate": validate,
            },
        )
        check = check_req.json()
        logger.info(f"check{check}")
        if check["retcode"] == 0:
            return check["data"]["challenge"]
    return None


def get_validate(gt: str, challenge: str, referer: str, choose: bool):
    """validate,challenge"""
    if choose:
        validate, challenge = rrocr(gt, challenge, referer)
    else:
        validate, challenge = other_api(gt, challenge)
    return validate, challenge  # 失败返回'j' 成功返回validate


def other_api(gt: str, challenge: str):
    response = http.get(config.third_api + f"gt={gt}&challenge={challenge}", timeout=60)
    data = response.json()
    if "data" in data and "validate" in data["data"]:
        logger.info("[第三方]成功")
        validate = data["data"]["validate"]
        challenge = data["data"]["challenge"]
        return validate, challenge
    else:
        validate = "j"
        challenge = "j"  # 失败返回'j' 成功返回validate
        return validate, challenge


def rrocr(gt: str, challenge: str, referer: str):
    jifen, _ = query_score()
    if jifen:
        validate = "j"
        challenge = "j"
        return validate, challenge
    response = http.post(
        "http://api.rrocr.com/api/recognize.html",
        params={
            "appkey": config.rrocr_key,
            "gt": gt,
            "challenge": challenge,
            "referer": referer,
            "sharecode": "585dee4d4ef94e1cb95d5362a158ea54",
        },
        timeout=60,
    )
    data = response.json()
    if "data" in data and "validate" in data["data"]:
        # logger.info(data["msg"])
        validate = data["data"]["validate"]
        challenge = data["data"]["challenge"]
        return validate, challenge
    else:
        # logger.info(data["msg"])  # 打码失败输出错误信息,返回'j'
        validate = "j"
        challenge = "j"
        return validate, challenge  # 失败返回'j' 成功返回validate


def gain_num(choice):
    if choice == "rr" and config.rrocr_key:
        data = http.get(
            f"http://api.rrocr.com/api/integral.html?appkey={config.rrocr_key}"
        ).json()
        if data["status"] == 0:
            key_num = data["integral"]
            return f"你剩余积分为{key_num}"
    elif choice == "ll" and config.third_api:
        url = config.third_api
        match = re.search(r"token=([^&]+)", url)
        if match:
            token = match.group(1)
            data = http.get(f"http://api.fuckmys.tk/token?token={token}").json()
            if data["info"] == "success":
                key_num = data["times"]
                return f"你已经使用了为{key_num}次，剩余{2333-key_num}次"
    elif choice == "other":
        return "暂不支持查询其他平台剩余次数，请前往（https://github.com/forchannot/LittlePaimon-plugin-Captchapr）pr或者自行修改源码"
    return None
