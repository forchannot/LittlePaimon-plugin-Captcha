import asyncio
import copy
import datetime
import random
import time
from collections import defaultdict
from typing import Tuple, Union

from LittlePaimon.database import MihoyoBBSSub, PrivateCookie, LastQuery
from LittlePaimon.utils import logger, scheduler, DRIVER
from LittlePaimon.utils.api import (
    get_sign_reward_list,
    SIGN_ACTION_API,
    random_hex,
    check_retcode,
    get_mihoyo_private_data,
)
from LittlePaimon.utils.requests import aiorequests
from nonebot import get_bot

from ..captcha.captcha import (
    _HEADER,
    get_validate,
    get_sign_info,
    get_sign_list,
    get_ds2,
)
from ..config.config import config
from ..draw.sign_draw import SignResult, draw_result

sign_reward_list: dict = {}


async def sign_action(user_id: str, uid: str, Header={}) -> Union[dict, str]:
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
        user_id=user_id, defaults={"uid": uid, "last_time": datetime.datetime.now()}
    )
    logger.info(f"[签到] {uid} 开始执行签到")
    # 获得签到信息
    sign_info = await get_mihoyo_private_data(uid, user_id, "sign_info")
    if isinstance(sign_info, str):
        logger.info(
            "米游社原神签到", "➤", {"用户": user_id, "UID": uid}, "未绑定私人cookie或已失效", False
        )
        await MihoyoBBSSub.filter(user_id=user_id, uid=uid).delete()
        return SignResult.FAIL, sign_info
    elif sign_info["data"]["is_sign"]:
        signed_days = sign_info["data"]["total_sign_day"] - 1
        logger.info("米游社原神签到", "➤", {"用户": user_id, "UID": uid}, "今天已经签过了", True)
        if sign_reward_list:
            return (
                SignResult.DONE,
                f'UID{uid}今天已经签过了，获得的奖励为\n{sign_reward_list[signed_days]["name"]}*{sign_reward_list[signed_days]["cnt"]}',
            )
        else:
            return SignResult.DONE, f"UID{uid}今天已经签过了"
    # 实际进行签到
    Header = {}
    for index in range(4):
        # 进行一次签到
        sign_data = await sign_action(user_id=user_id, uid=uid, Header=Header)
        # 检测数据
        if (
            sign_data
            and "data" in sign_data
            and sign_data["data"]
            and "risk_code" in sign_data["data"]
        ):
            # 出现校验码
            if sign_data["data"]["risk_code"] == 375:
                logger.info(
                    "米游社原神签到",
                    "➤",
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
                        # logger.info(
                        #    f"米游社[验证]签到,用户{user_id},UID:{uid}已获取验证码，等待时间{delay}秒", True
                        # )
                        # await asyncio.sleep(delay)
                    else:
                        delay = 300 + random.randint(1, 30)
                        logger.info(
                            f"米游社[验证]签到,用户{user_id},UID:{uid}未获取验证码，等待时间{delay}秒",
                            result_type=False,
                        )
                        await asyncio.sleep(delay)
                    continue
                else:
                    continue
            # 成功签到!
            else:
                if index == 0:
                    logger.info(f"米游社签到,用户{user_id},UID:{uid}无验证码", result_type=True)
                    result = "[无验证]"
                else:
                    logger.info(
                        f"米游社[验证]签到,用户{user_id},UID:{uid}重试{index} 次验证成功",
                        result_type=True,
                    )
                    result = "[验证]"
                break
        # 重试超过阈值
        else:
            result = "签到失败...请求失败!" + "\n" + "无法绕过验证码"
            logger.info(f"米游社[验证]签到,用户{user_id},UID:{uid}超过请求阈值", result_type=False)
            return SignResult.FAIL, result
    # 签到失败
    else:
        result = "签到失败!"
        logger.info(
            f"米游社[验证]签到,用户{user_id},UID:{uid}签到失败, 结果: {result}", result_type=False
        )
        return SignResult.FAIL, result
    sign_info = sign_info["data"]
    sign_list = await get_sign_list()
    status = sign_data["message"]
    getitem = sign_list["data"]["awards"][int(sign_info["total_sign_day"])]["name"]
    getnum = sign_list["data"]["awards"][int(sign_info["total_sign_day"])]["cnt"]
    get_im = f"本次签到获得{getitem}x{getnum}"
    new_sign_info = await get_sign_info(user_id, uid)
    new_sign_info = new_sign_info["data"]
    if new_sign_info["is_sign"]:
        mes_im = "签到成功"
    else:
        result = f"签到失败, 状态为:{status}"
        return SignResult.FAIL, result
    sign_missed = sign_info["sign_cnt_missed"]
    result = mes_im + result + "!" + "\n" + f"本月漏签次数：{sign_missed}" + "\n" + get_im
    logger.info(
        f"米游社[验证]签到,用户{user_id},UID:{uid}签到完成, 结果: {mes_im}, 漏签次数: {sign_missed}",
        result_type=True,
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
    logger.info(
        "米游社原神签到", f"开始执行米游社自动签到，共<m>{len(subs)}</m>个任务，预计花费<m>{len(subs) * 2}</m>分钟"
    )
    sign_result_group = defaultdict(list)
    sign_result_private = defaultdict(list)
    for sub in subs:
        if (
            sub.user_id in config.member_allow_list
            or sub.group_id in config.group_allow_list
        ):
            result, msg = await mhy_bbs_sign(True, str(sub.user_id), sub.uid)  # 执行验证签到
        else:
            result, msg = await mhy_bbs_sign(False, str(sub.user_id), sub.uid)  # 执行普通签到
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
            await asyncio.sleep(random.randint(5, 10))
        else:
            await asyncio.sleep(random.randint(60, 90))

    logger.info("米游社原神签到", "➤➤", result="全部执行完毕,开始处理群结果")
    for group_id, sign_result in sign_result_group.items():
        # 发送签到结果到群
        img = await draw_result(group_id, sign_result)
        try:
            await get_bot().send_group_msg(group_id=int(group_id), message=img)
        except Exception as e:
            logger.info("米游社原神签到", "➤➤", {"群": group_id}, f"发送签到结果失败: {e}", False)
        await asyncio.sleep(random.randint(3, 6))

    logger.info("米游社原神签到", "➤➤", result="全部执行完毕,开始处理个人结果")
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
                logger.info("米游社原神签到", "➤➤", {"用户": user_id}, f"发送签到结果失败: {e}", False)
        await asyncio.sleep(random.randint(3, 6))

    logger.info("米游社原神签到", f"签到完成，共花费<m>{round((time.time() - t) / 60, 2)}</m>分钟")


@DRIVER.on_startup
async def init_reward_list():
    """
    初始化签到奖励列表
    """
    global sign_reward_list
    try:
        sign_reward_list = await get_sign_reward_list()
        sign_reward_list = sign_reward_list["data"]["awards"]
    except Exception:
        logger.info("米游社原神签到", "初始化签到奖励列表<r>失败</r>")
