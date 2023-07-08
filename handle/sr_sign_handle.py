import asyncio
import copy
import random
import time
from collections import defaultdict

from LittlePaimon.database import MihoyoBBSSub
from LittlePaimon.plugins.star_rail_info.data_handle import get_uid
from LittlePaimon.utils import scheduler
from LittlePaimon.utils.api import get_cookie
from LittlePaimon.utils.requests import aiorequests
from nonebot import get_bot

from ..captcha.captcha import _HEADER, get_ds2, get_validate
from ..config.config import config
from ..draw.sign_draw import SignResult, draw_result
from ..utils.logger import Logger

# 铁道签到列表
OLD_URL = "https://api-takumi.mihoyo.com"
STAR_RAIL_SIGN_LIST_URL = f"{OLD_URL}/event/luna/home"
# 获得签到信息
STAR_RAIL_SIGN_INFO_URL = f"{OLD_URL}/event/luna/info"
# 签到
STAR_RAIL_SIGN_URL = f"{OLD_URL}/event/luna/sign"


async def sr_mihoyo_bbs_sign(uid: str, ck: str, Header=None) -> dict:
    if Header is None:
        Header = {}
    HEADER = copy.deepcopy(_HEADER)
    HEADER["Cookie"] = ck
    HEADER["x-rpc-app_version"] = "2.44.1"
    HEADER["x-rpc-client_type"] = "5"
    HEADER["X_Requested_With"] = "com.mihoyo.hyperion"
    HEADER["DS"] = get_ds2(web=True)
    HEADER["Referer"] = "https://webstatic.mihoyo.com"
    HEADER.update(Header)
    data = await aiorequests.post(
        url=STAR_RAIL_SIGN_URL,
        headers=HEADER,
        json={
            "act_id": "e202304121516551",
            "region": "prod_gf_cn",
            "uid": uid,
            "lang": "zh-cn",
        },
    )
    return data.json()


async def sr_get_sign_info(uid, ck):
    HEADER = copy.deepcopy(_HEADER)
    HEADER["Cookie"] = ck
    data = await aiorequests.get(
        url=STAR_RAIL_SIGN_INFO_URL,
        headers=HEADER,
        params={
            "act_id": "e202304121516551",
            "lang": "zh-cn",
            "region": "prod_gf_cn",
            "uid": uid,
        },
    )
    return data.json()


async def sr_get_sign_list() -> dict:
    data = await aiorequests.get(
        url=STAR_RAIL_SIGN_LIST_URL,
        headers=_HEADER,
        params={
            "act_id": "e202304121516551",
            "lang": "zh-cn",
        },
    )
    return data.json()


async def sr_sign_in(
    sign_allow: bool, user_id: str, sr_uid, gs_uid
) -> tuple[SignResult, str]:
    Logger.info("星铁签到", "➤", {"用户": user_id, "UID": sr_uid}, "开始执行签到！")
    cookie = await get_cookie(user_id, gs_uid, True, True)
    if not cookie:
        return SignResult.FAIL, "未绑定私人cookies，请发送指令[原神扫码绑定]"
    # 获得签到信息
    sign_info = await sr_get_sign_info(sr_uid, cookie.cookie)
    # 获取签到列表
    sign_list = await sr_get_sign_list()
    # 初步校验数据
    if sign_info and "data" in sign_info and sign_info["data"]:
        sign_info = sign_info["data"]
    else:
        Logger.info(
            "星铁签到",
            "➤",
            {"用户": user_id, "UID": sr_uid},
            "出错, 请检查Cookies是否过期！",
            False,
        )
        return SignResult.FAIL, "签到失败...请检查Cookies是否过期！"
    # 检测是否已签到
    if sign_info["is_sign"]:
        Logger.info(
            "星铁签到", "➤", {"用户": user_id, "UID": sr_uid}, "今天已经签过了", True
        )
        getitem = sign_list["data"]["awards"][
            int(sign_info["total_sign_day"]) - 1
        ]["name"]
        getnum = sign_list["data"]["awards"][
            int(sign_info["total_sign_day"]) - 1
        ]["cnt"]
        sign_missed = sign_info["sign_cnt_missed"]
        return (
            SignResult.DONE,
            f"UID{sr_uid}今天已经签过了，"
            f"本月漏签{sign_missed}天，"
            f"获得的奖励为\n{getitem}*{getnum}",
        )
    # 实际进行签到
    Header = {}
    for index in range(4):
        # 进行一次签到
        sign_data = await sr_mihoyo_bbs_sign(
            uid=sr_uid,
            ck=cookie.cookie,
            Header=Header,
        )
        # 检测数据
        if (
            sign_data
            and "data" in sign_data
            and sign_data["data"]
            and "risk_code" in sign_data["data"]
        ):
            # 出现校验码
            if sign_data["data"]["risk_code"] == 5001:
                Logger.info(
                    "星铁签到",
                    "➤",
                    {"用户": user_id, "UID": sr_uid},
                    f"该用户出现校验码，开始尝试进行验证...，开始重试第 {index + 1} 次！",
                )
                if (
                    config.rrocr_key or config.third_api or config.ttocr_key
                ) and sign_allow:
                    gt = sign_data["data"]["gt"]
                    challenge = sign_data["data"]["challenge"]
                    validate, challeng = await get_validate(
                        gt,
                        challenge,
                        STAR_RAIL_SIGN_URL,
                        config.qd_ch,
                    )
                    if validate != "j" and challeng != "j":
                        Header["x-rpc-challenge"] = challeng
                        Header["x-rpc-validate"] = validate
                        Header["x-rpc-seccode"] = f"{validate}|jordan"
                        Logger.info(
                            "星铁签到",
                            "➤",
                            {"用户": user_id, "UID": sr_uid},
                            f"已获取验证码",
                        )
                    else:
                        delay = 100 + random.randint(1, 30)
                        Logger.info(
                            "星铁签到",
                            "➤",
                            {"用户": user_id, "UID": sr_uid},
                            f"第{index + 1}次尝试绕过验证码失败，等待{delay}秒后重试",
                            False,
                        )
                        await asyncio.sleep(delay)
                    continue
            # 成功签到!
            else:
                if index == 0:
                    Logger.info(
                        "星铁签到",
                        "➤",
                        {"用户": user_id, "UID": sr_uid},
                        f"无验证码，签到成功",
                    )
                    result = "[无验证]"
                else:
                    Logger.info(
                        "星铁签到",
                        "➤",
                        {"用户": user_id, "UID": sr_uid},
                        f"重试 {index} 次验证成功!",
                    )
                    result = "[验证]"
                break
        # 重试超过阈值
        else:
            Logger.info(
                "星铁签到",
                "➤",
                {"用户": user_id, "UID": sr_uid},
                f"超过请求阈值...",
                False,
            )
            return SignResult.FAIL, "签到失败...请求失败!\n请过段时间使用签到或手动进行签到"
    # 签到失败
    else:
        result = "签到失败!"
        Logger.info(
            "星铁签到",
            "➤",
            {"用户": user_id, "UID": sr_uid},
            f"签到失败, 结果: {result}",
            False,
        )
        return SignResult.FAIL, result
    # 获取签到列表
    status = sign_data["message"]
    getitem = sign_list["data"]["awards"][int(sign_info["total_sign_day"])][
        "name"
    ]
    getnum = sign_list["data"]["awards"][int(sign_info["total_sign_day"])][
        "cnt"
    ]
    get_im = f"本次签到获得{getitem}x{getnum}"
    new_sign_info = await sr_get_sign_info(sr_uid, cookie.cookie)
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
        "星铁签到",
        "➤",
        {"用户": user_id, "UID": sr_uid},
        f"签到完成, 结果: {mes_im}, 漏签次数: {sign_missed}",
    )
    return SignResult.SUCCESS, result


@scheduler.scheduled_job(
    "cron",
    hour=config.sr_enable_hour,
    minute=config.sr_enable_minute,
    misfire_grace_time=10,
)
async def _():
    await sr_bbs_auto_sign()


async def sr_bbs_auto_sign():
    """
    指定时间，执行所有星铁签到任务
    """
    if not config.sr_enable:
        return
    t = time.time()  # 计时用
    subs = await MihoyoBBSSub.filter(sub_event="星铁签到").all()
    if not subs:
        # 如果没有星铁原签到订阅，则不执行签到任务
        return
    Logger.info(
        "星铁签到",
        f"开始执行星铁签到，共<m>{len(subs)}</m>个任务，预计花费<m>{round(100 * len(subs) / 60, 2)}</m>分钟",
    )
    sr_sign_result_group = defaultdict(list)
    sr_sign_result_private = defaultdict(list)
    for sub in subs:
        sr_uid = get_uid(str(sub.user_id))
        if (
            sub.user_id in config.member_allow_list
            or sub.group_id in config.group_allow_list
        ):
            result, msg = await sr_sign_in(
                True, str(sub.user_id), sr_uid, sub.uid
            )  # 执行验证签到
        else:
            result, msg = await sr_sign_in(
                False, str(sub.user_id), sr_uid, sub.uid
            )  # 执行普通签到
        # 将签到结果分群或个人添加到结果列表中
        if sub.user_id != sub.group_id:
            sr_sign_result_group[sub.group_id].append(
                {
                    "user_id": sub.user_id,
                    "uid": sr_uid,
                    "result": result,
                    "reward": msg.split("\n")[-1]
                    if result in [SignResult.SUCCESS, SignResult.DONE]
                    else "",
                }
            )
        else:
            sr_sign_result_private[sub.user_id].append(
                {
                    "uid": sr_uid,
                    "result": result,
                    "reward": msg.split("\n")[-1]
                    if result in [SignResult.SUCCESS, SignResult.DONE]
                    else "",
                }
            )
        if result == SignResult.DONE:
            sleep_time = random.randint(5, 10)
            Logger.info(
                "星铁签到",
                "➤➤",
                {"用户": sub.user_id, "UID": sr_uid},
                f"签到过了,等待{sleep_time}秒执行下一个用户",
            )
            await asyncio.sleep(sleep_time)
        else:
            sleep_time = random.randint(60, 90)
            Logger.info(
                "星铁签到",
                "➤➤",
                {"用户": sub.user_id, "UID": sr_uid},
                f"执行完毕,等待{sleep_time}秒执行下一个用户",
            )
            await asyncio.sleep(sleep_time)

    Logger.info("星铁签到", "➤➤", result="全部执行完毕,开始处理群结果")
    for group_id, sign_result in sr_sign_result_group.items():
        # 发送签到结果到群
        img = await draw_result(str(group_id), sign_result, "星铁")
        try:
            await get_bot().send_group_msg(group_id=int(group_id), message=img)
        except Exception as e:
            Logger.info("星铁签到", "➤➤", {"群": group_id}, f"发送签到结果失败: {e}", False)
        await asyncio.sleep(random.randint(3, 6))

    Logger.info("星铁签到", "➤➤", result="全部执行完毕,开始处理个人结果")
    for user_id, sign_result in sr_sign_result_private.items():
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
                    "星铁签到", "➤➤", {"用户": user_id}, f"发送签到结果失败: {e}", False
                )
        await asyncio.sleep(random.randint(3, 6))
    Logger.info("星铁签到", f"签到完成，共花费<m>{round((time.time() - t) / 60, 2)}</m>分钟")
