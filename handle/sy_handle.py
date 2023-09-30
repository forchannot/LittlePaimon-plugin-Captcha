from typing import Optional

from LittlePaimon.database import AbyssInfo
from LittlePaimon.plugins.Paimon_Abyss import draw_abyss_card
from LittlePaimon.utils.api import ABYSS_API, get_cookie, mihoyo_headers
from LittlePaimon.utils.message import CommandPlayer
from LittlePaimon.utils.requests import aiorequests
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message, MessageEvent
from nonebot.params import CommandArg

from ..captcha.captcha import get_pass_challenge
from ..config.config import config
from ..utils.logger import Logger

sy = on_command(
    "sy",
    aliases={"深渊战报", "深渊信息"},
    priority=9,
    block=True,
    state={
        "pm_name": "sy",
        "pm_description": "查看本期|上期的深渊战报",
        "pm_usage": "sy(uid)(本期|上期)",
        "pm_priority": 1,
    },
)


async def get_abyss_info(
    uid: str,
    user_id: Optional[str],
    schedule_type: Optional[str] = "1",
):
    server_id = "cn_qd01" if uid[0] == "5" else "cn_gf01"
    cookie_info = await get_cookie(user_id, uid, True)
    headers = mihoyo_headers(
        q=f"role_id={uid}&schedule_type={schedule_type}&server={server_id}",
        cookie=cookie_info.cookie,
    )
    k = 0
    for i in range(2):
        data: dict = (
            await aiorequests.get(
                url=ABYSS_API,
                headers=headers,
                params={
                    "schedule_type": schedule_type,
                    "role_id": uid,
                    "server": server_id,
                },
            )
        ).json()
        if data["retcode"] == 1034 and k < 2:
            k += 1
            Logger.info(
                "原神深渊战报",
                "➤➤",
                {},
                f"遇到验证码，开始尝试过码",
                True,
            )
            challenge = await get_pass_challenge(uid, user_id, config.ssbq_ch)
            if challenge is not None:
                headers.update({"challenge": challenge})
                continue
            else:
                Logger.info(
                    "原神深渊战报",
                    "➤➤",
                    {},
                    f"过码失败",
                    False,
                )
                return "遇到验证码，但是过码失败"
        else:
            if data["retcode"] != 1034 and k != 0:
                Logger.info(
                    "原神深渊战报",
                    "➤➤",
                    {},
                    f"过码成功",
                )
            return "遇到验证码，请手动去解决" if data["retcode"] == 1034 else data


async def update_abyss_info(uid, user_id, abyss_index: str):
    data = await get_abyss_info(uid, user_id, schedule_type=abyss_index)
    if not isinstance(data, dict):
        return data
    elif data["retcode"] != 0:
        Logger.info(
            "原神信息", f'更新<m>{uid}</m>的玩家数据时出错，消息为<r>{data["message"]}</r>'
        )
        return data["message"]
    await AbyssInfo.update_info(user_id, uid, data["data"])
    Logger.info("原神信息", f"➤UID<m>{uid}</m><g>更新深渊信息成功</g>")
    return await AbyssInfo.get_or_none(user_id=user_id, uid=uid)


@sy.handle()
async def _(
    event: MessageEvent, players=CommandPlayer(), msg: Message = CommandArg()
):
    Logger.info("原神深渊战报", "开始执行")
    abyss_index = (
        2 if any(i in msg.extract_plain_text() for i in ["上", "last"]) else 1
    )
    msg = Message()
    for player in players:
        Logger.info(
            "原神深渊战报", "➤ ", {"用户": players[0].user_id, "UID": players[0].uid}
        )
        abyss_info = await update_abyss_info(
            player.uid, player.user_id, str(abyss_index)
        )
        if isinstance(abyss_info, str):
            Logger.info("原神深渊战报", "➤➤", {}, abyss_info, False)
            msg += f"UID{player.uid}{abyss_info}\n"
        else:
            Logger.info("原神深渊战报", "➤➤", {}, "数据获取成功", True)
            try:
                img = await draw_abyss_card(abyss_info)
                Logger.info("原神深渊战报", "➤➤➤", {}, "制图完成", True)
                msg += img
            except Exception as e:
                Logger.info("原神深渊战报", "➤➤➤", {}, f"制图出错:{e}", False)
                msg += f"UID{player.uid}制图时出错：{e}\n"
    await sy.finish(msg, at_sender=True)