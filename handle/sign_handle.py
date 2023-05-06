import asyncio
import copy
import datetime
import random
import time
from collections import defaultdict
from typing import Dict, Tuple, Union

from LittlePaimon.database import LastQuery, MihoyoBBSSub, PrivateCookie
from LittlePaimon.utils import DRIVER, scheduler
from LittlePaimon.utils.api import (
    SIGN_ACTION_API,
    check_retcode,
    get_mihoyo_private_data,
    get_sign_reward_list,
    random_hex,
)
from LittlePaimon.utils.requests import aiorequests
from nonebot import get_bot

from ..captcha.captcha import (
    _HEADER,
    get_ds2,
    get_sign_info,
    get_sign_list,
    get_validate,
)
from ..config.config import config
from ..draw.sign_draw import SignResult, draw_result
from ..utils.logger import Logger

sign_reward_list: Dict = {}


async def sign_action(
    user_id: str, uid: str, Header: Dict = {}
) -> Union[Dict, str]:
    cookie_info = await PrivateCookie.get_or_none(user_id=user_id, uid=uid)
    server_id = "cn_qd01" if uid[0] == "5" else "cn_gf01"
    HEADER = copy.deepcopy(_HEADER)
    HEADER["Cookie"] = cookie_info.cookie
    HEADER["x-rpc-device_id"] = random_hex(32)
    HEADER["X_Requested_With"] = "com.mihoyo.hyperion"
    HEADER["DS"] = get_ds2(web=True)
    HEADER["Referer"] = (
        "https://webstatic.mihoyo.com/bbs/event/signin-ys/index.html"
        "?bbs_auth_required=true&act_id=e202009291139501&utm_source=bbs"
        "&utm_medium=mys&utm_campaign=icon"
    )
    HEADER.update(Header)
    req = await aiorequests.post(
        url=SIGN_ACTION_API,
        headers=HEADER,
        json={"act_id": "e202009291139501", "uid": uid, "region": server_id},
    )
    data = req.json()
    if await check_retcode(data, cookie_info, user_id, uid):
        return data
    else:
        return f"你的UID{uid}的cookie疑似失效了"


async def mhy_bbs_sign(
    sign_allow: bool, user_id: str, uid: str
) -> Tuple[SignResult, str]:
    """
    执行米游社原神签到，返回签到成功天数或失败原因
    :param sign_allow: 白名单
    :param user_id: 用户id
    :param uid: 原神uid
    :return: 签到成功天数或失败原因
    """
    await LastQuery.update_or_create(
        user_id=user_id,
        defaults={"uid": uid, "last_time": datetime.datetime.now()},
    )
    Logger.info("原神签到", "➤➤", {"用户": user_id, "UID": uid}, "开始执行签到")
    # 获得签到信息
    sign_info = await get_mihoyo_private_data(uid, user_id, "sign_info")
    if isinstance(sign_info, str):
        Logger.info(
            "原神签到", "➤➤", {"用户": user_id, "UID": uid}, "未绑定私人cookie或已失效", False
        )
        await MihoyoBBSSub.filter(user_id=user_id, uid=uid).delete()
        return SignResult.FAIL, sign_info
    elif sign_info["data"]["is_sign"]:
        signed_days = sign_info["data"]["total_sign_day"] - 1
        Logger.info("原神签到", "➤➤", {"用户": user_id, "UID": uid}, "今天已经签过了")
        if sign_reward_list:
            return (
                SignResult.DONE,
                f"UID{uid}今天已经签过了，"
                f'获得的奖励为\n{sign_reward_list[signed_days]["name"]}*{sign_reward_list[signed_days]["cnt"]}',
            )
        else:
            return SignResult.DONE, f"UID{uid}今天已经签过了"
    # 实际进行签到
    Header = {}
    for index in range(4):
        # 进行一次签到
        sign_data = await sign_action(user_id=user_id, uid=uid, Header=Header)
        # 检测数据
        if isinstance(sign_data, str):
            Logger.info(
                "米游社原神签到",
                "➤",
                {"用户": user_id, "UID": uid},
                f"获取数据失败, {sign_data}",
                False,
            )
            return SignResult.FAIL, f"{uid}签到失败，{sign_data}\n"
        if (
            sign_data
            and "data" in sign_data
            and "risk_code" in sign_data["data"]
        ):
            # 出现校验码
            if sign_data["data"]["risk_code"] == 375:
                Logger.info(
                    "原神签到",
                    "➤➤",
                    {"用户": user_id, "UID": uid},
                    f"出现验证码，开始进行第{index + 1}次尝试绕过",
                    False,
                )
                if (
                    config.rrocr_key or config.third_api or config.ttocr_key
                ) and sign_allow:
                    gt = sign_data["data"]["gt"]
                    challenge = sign_data["data"]["challenge"]
                    validate, challeng = await get_validate(
                        gt, challenge, SIGN_ACTION_API, config.qd_ch
                    )
                    if validate != "j" and challeng != "j":
                        # delay = random.randint(5, 15)
                        Header["x-rpc-challenge"] = challeng
                        Header["x-rpc-validate"] = validate
                        Header["x-rpc-seccode"] = f"{validate}|jordan"
                    else:
                        delay = 300 + random.randint(1, 30)
                        Logger.info(
                            "原神签到",
                            "➤➤",
                            {"用户": user_id, "UID": uid},
                            f"第{index + 1}次尝试绕过验证码失败，等待{delay}秒后重试",
                            False,
                        )
                        await asyncio.sleep(delay)
                    continue
                else:
                    continue
            # 成功签到!
            else:
                if index == 0:
                    Logger.info(
                        "原神签到", "➤➤", {"用户": user_id, "UID": uid}, "无验证码，签到成功"
                    )
                    result = "[无验证]"
                else:
                    Logger.info(
                        "原神签到",
                        "➤➤",
                        {"用户": user_id, "UID": uid},
                        f"重试{index}次签到成功",
                    )
                    result = "[验证]"
                break
        else:
            Logger.info(
                "米游社原神签到",
                "➤",
                {"用户": user_id, "UID": uid},
                f"获取数据失败, {sign_data}",
                False,
            )
            return SignResult.FAIL, "签到失败...未知错误!"
    # 重试超过阈值
    else:
        result = "签到失败...请求失败!" + "\n" + "无法绕过验证码"
        Logger.info(
            "原神签到", "➤➤", {"用户": user_id, "UID": uid}, "重试超过阈值，签到失败", False
        )
        return SignResult.FAIL, result
    sign_info = sign_info["data"]
    sign_list = await get_sign_list()
    status = sign_data["message"]
    getitem = sign_list["data"]["awards"][int(sign_info["total_sign_day"])][
        "name"
    ]
    getnum = sign_list["data"]["awards"][int(sign_info["total_sign_day"])][
        "cnt"
    ]
    get_im = f"本次签到获得{getitem}x{getnum}"
    new_sign_info = await get_sign_info(user_id, uid)
    new_sign_info = new_sign_info["data"]
    if new_sign_info["is_sign"]:
        mes_im = "签到成功"
    else:
        result = f"签到失败, 状态为:{status}"
        return SignResult.FAIL, result
    sign_missed = sign_info["sign_cnt_missed"]
    result = (
        mes_im + result + "!" + "\n" + f"本月漏签次数：{sign_missed}" + "\n" + get_im
    )
    Logger.info(
        "原神签到",
        "➤➤",
        {"用户": user_id, "UID": uid},
        f"签到成功，结果：{mes_im}，漏签次数：{sign_missed}",
    )
    return SignResult.SUCCESS, result


@scheduler.scheduled_job(
    "cron",
    hour=config.auto_sign_hour,
    minute=config.auto_sign_minute,
    misfire_grace_time=10,
)
async def _():
    await bbs_auto_sign()


async def bbs_auto_sign():
    """
    指定时间，执行所有米游社原神签到任务， 并将结果分群绘图发送
    """
    if not config.auto_sign_enable:
        return
    t = time.time()  # 计时用
    subs = await MihoyoBBSSub.filter(sub_event="米游社原神签到").all()
    if not subs:
        # 如果没有米游社原神签到订阅，则不执行签到任务
        return
    Logger.info(
        "原神签到",
        "➤➤",
        result=f"开始执行米游社自动签到，共<m>{len(subs)}</m>个任务，预计花费<m>{len(subs) * 2}</m>分钟",
    )
    sign_result_group = defaultdict(list)
    sign_result_private = defaultdict(list)
    for sub in subs:
        if (
            sub.user_id in config.member_allow_list
            or sub.group_id in config.group_allow_list
        ):
            result, msg = await mhy_bbs_sign(
                True, str(sub.user_id), sub.uid
            )  # 执行验证签到
        else:
            result, msg = await mhy_bbs_sign(
                False, str(sub.user_id), sub.uid
            )  # 执行普通签到
        # 将签到结果分群或个人添加到结果列表中
        if sub.user_id != sub.group_id:
            sign_result_group[sub.group_id].append(
                {
                    "user_id": sub.user_id,
                    "uid": sub.uid,
                    "result": result,
                    "reward": msg.split("\n")[-1]
                    if result in [SignResult.SUCCESS, SignResult.DONE]
                    else "",
                }
            )
        else:
            sign_result_private[sub.user_id].append(
                {
                    "uid": sub.uid,
                    "result": result,
                    "reward": msg.split("\n")[-1]
                    if result in [SignResult.SUCCESS, SignResult.DONE]
                    else "",
                }
            )
        if result == SignResult.DONE:
            sleep_time = random.randint(5, 10)
            Logger.info(
                "原神签到",
                "➤➤",
                {"用户": sub.user_id, "UID": sub.uid},
                f"签到过了,等待{sleep_time}秒执行下一个用户",
            )
            await asyncio.sleep(sleep_time)
        else:
            sleep_time = random.randint(60, 90)
            Logger.info(
                "原神签到",
                "➤➤",
                {"用户": sub.user_id, "UID": sub.uid},
                f"执行完毕,等待{sleep_time}秒执行下一个用户",
            )
            await asyncio.sleep(sleep_time)

    Logger.info("原神签到", "➤➤", result="全部执行完毕,开始处理群结果")
    for group_id, sign_result in sign_result_group.items():
        # 发送签到结果到群
        img = await draw_result(group_id, sign_result)
        try:
            await get_bot().send_group_msg(group_id=int(group_id), message=img)
        except Exception as e:
            Logger.info("原神签到", "➤➤", {"群": group_id}, f"发送签到结果失败: {e}", False)
        await asyncio.sleep(random.randint(3, 6))

    Logger.info("原神签到", "➤➤", result="全部执行完毕,开始处理个人结果")
    for user_id, sign_result in sign_result_private.items():
        for result in sign_result:
            try:
                await get_bot().send_private_msg(
                    user_id=int(user_id),
                    message=f'你的UID{result["uid"]}签到'
                    f'{"成功" if result["result"] != SignResult.FAIL else "失败"}'
                    f'{"" if result["result"] == SignResult.FAIL else "，获得奖励：" + result["reward"]}',
                )
            except Exception as e:
                Logger.info(
                    "原神签到", "➤➤", {"用户": user_id}, f"发送签到结果失败: {e}", False
                )
        await asyncio.sleep(random.randint(3, 6))
    Logger.info("原神签到", f"签到完成，共花费<m>{round((time.time() - t) / 60, 2)}</m>分钟")


@DRIVER.on_startup
async def init_reward_list():
    """
    初始化签到奖励列表
    """
    global sign_reward_list
    try:
        sign_reward_list = await get_sign_reward_list()
        sign_reward_list = sign_reward_list["data"]["awards"]
    except Exception as e:
        Logger.info("原神签到", f"初始化签到奖励列表<r>失败</r>{e}")
