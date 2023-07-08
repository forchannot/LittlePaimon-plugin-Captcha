from typing import Union

from nonebot.internal.matcher import Matcher
from nonebot.params import CommandArg

from .captcha.captcha import gain_num
from .handle.ssbq_handler import handle_ssbq, sub_list, get_subs
from .handle.coin_handle import mhy_bbs_coin, bbs_auto_coin
from .handle.sign_handle import mhy_bbs_sign, bbs_auto_sign
from .handle.sr_sign_handle import sr_bbs_auto_sign
from .config.config import config
from .utils.logger import Logger
from .web import web_api, web_page  # noqa

from LittlePaimon.database import MihoyoBBSSub, PrivateCookie, DailyNoteSub
from LittlePaimon.utils.message import CommandPlayer, CommandUID, CommandSwitch

from nonebot import on_command, Bot
from nonebot.typing import T_State
from nonebot.adapters.onebot.v11 import (
    Message,
    GroupMessageEvent,
    PrivateMessageEvent,
)
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata
from nonebot.rule import to_me


__plugin_meta__ = PluginMetadata(
    name="加强小派蒙验证",
    description="为签到，米游币，体力提供验证",
    usage="加强小派蒙验证",
    extra={
        "author": "forchannot",
        "version": "2.0",
        "priority": 7,
    },
)


sign = on_command(
    "mys签到",
    aliases={"米游社签到", "mys自动签到", "米游社自动签到", "原神签到"},
    priority=2,
    block=True,
    state={
        "pm_name": "米游社签到",
        "pm_description": "*执行米游社签到操作，或开启每日自动签到",
        "pm_usage": "米游社签到(uid)[on|off]",
        "pm_priority": 1,
    },
)
all_sign = on_command(
    "全部重签",
    aliases={"mys全部重签", "米游社全部重签", "原神全部重签"},
    priority=2,
    block=True,
    permission=SUPERUSER,
    rule=to_me(),
    state={
        "pm_name": "米游社全部重签",
        "pm_description": "重签全部米游社签到任务，需超级用户权限",
        "pm_usage": "@Bot 全部重签",
        "pm_priority": 3,
    },
)
get_coin = on_command(
    "myb获取",
    aliases={"米游币获取", "myb自动获取", "米游币自动获取", "米游币任务"},
    priority=2,
    block=True,
    state={
        "pm_name": "米游币获取",
        "pm_description": "*执行米游币任务操作，或开启每日自动获取米游币",
        "pm_usage": "米游币获取(uid)[on|off]",
        "pm_priority": 2,
    },
)
all_coin = on_command(
    "myb全部重做",
    aliases={"米游币全部重做"},
    priority=2,
    block=True,
    permission=SUPERUSER,
    rule=to_me(),
    state={
        "pm_name": "米游币获取全部重做",
        "pm_description": "重做全部米游币获取任务，需超级用户权限",
        "pm_usage": "@Bot myb全部重做",
        "pm_priority": 4,
    },
)
ssbq = on_command(
    "ssbq",
    aliases={"实时便笺", "实时便签", "当前树脂", "体力", "查询体力"},
    priority=2,
    block=True,
    state={
        "pm_name": "ssbq",
        "pm_description": "*查看原神实时便笺(树脂情况)",
        "pm_usage": "ssbq(uid)",
        "pm_priority": 1,
    },
)
ssbq_sub = on_command(
    "ssbq提醒",
    aliases={"实时便笺提醒", "实时便签提醒", "当前树脂提醒"},
    priority=2,
    block=True,
    state={
        "pm_name": "ssbq提醒",
        "pm_description": "*开启|关闭ssbq提醒，可订阅树脂以及尘歌壶钱币提醒",
        "pm_usage": "ssbq提醒<开|关>[树脂|钱币]",
        "pm_priority": 1,
    },
)
get_num = on_command("查询积分", aliases={"查询剩余", "查询剩余积分"}, permission=SUPERUSER)
sr_sign = on_command(
    "星铁签到",
    aliases={"星穹铁道签到", "铁道签到"},
    priority=2,
    block=True,
    state={
        "pm_name": "星铁签到",
        "pm_description": "*执行星铁签到操作，或开启每日自动签到",
        "pm_usage": "星铁签到[on|off]",
        "pm_priority": 1,
    },
)
all_sr_sign = on_command(
    "星铁全部重签",
    aliases={"铁道全部重签"},
    priority=2,
    block=True,
    permission=SUPERUSER,
    rule=to_me(),
    state={
        "pm_name": "星铁全部重签",
        "pm_description": "重签全部星铁签到任务，需超级用户权限",
        "pm_usage": "全部星铁重签",
        "pm_priority": 3,
    },
)

signing_list = []
coin_getting_list = []
ssbq_list = []
sr_list = []


@sign.handle()
async def _(
    bot: Bot,
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    uid=CommandUID(),
    switch=CommandSwitch(),
):
    if switch is None:
        # 没有开关参数，手动执行米游社签到
        if f"{event.user_id}-{uid}" in signing_list:
            await sign.finish("你已经在执行签到任务中，请勿重复发送", at_sender=True)
        else:
            await sign.send(f"开始为UID{uid}执行米游社签到，耗时较长，请稍等...", at_sender=True)
            Logger.info(
                "原神签到", "开始为", {"用户": event.user_id, "uid": uid, "签到": ""}
            )
            signing_list.append(f"{event.user_id}-{uid}")
            judgment = isinstance(event, GroupMessageEvent)
            if judgment and event.group_id in config.group_allow_list:
                Logger.info(f"群聊{event.group_id}在白名单内,开始执行验证签到")
                _, result = await mhy_bbs_sign(True, str(event.user_id), uid)
            elif event.user_id in config.member_allow_list:
                Logger.info(f"用户{event.user_id}在白名单内,开始执行验证签到")
                _, result = await mhy_bbs_sign(True, str(event.user_id), uid)
            else:
                Logger.info(f"用户{event.user_id}不在白名单内,开始执行普通签到")
                _, result = await mhy_bbs_sign(False, str(event.user_id), uid)
            signing_list.remove(f"{event.user_id}-{uid}")
            await sign.finish(result, at_sender=True)
    else:
        sub_data = {
            "user_id": event.user_id,
            "uid": uid,
            "sub_event": "米游社原神签到",
        }
        if switch:
            # switch为开启，则添加订阅
            if await PrivateCookie.get_or_none(
                user_id=str(event.user_id), uid=uid
            ):
                await MihoyoBBSSub.update_or_create(
                    **sub_data,
                    defaults={
                        "group_id": event.group_id
                        if isinstance(event, GroupMessageEvent)
                        else event.user_id
                    },
                )
                Logger.info(
                    "米游社原神签到",
                    "",
                    {"user_id": event.user_id, "uid": uid},
                    "开启成功",
                )
                await sign.finish(f"UID{uid}开启米游社原神自动签到成功", at_sender=True)
            else:
                await sign.finish(
                    f"UID{uid}尚未绑定Cookie！请先使用<原神扫码绑定>指令绑定吧！", at_sender=True
                )
        else:
            # switch为关闭，则取消订阅
            if sub := await MihoyoBBSSub.get_or_none(**sub_data):
                await sub.delete()
                Logger.info(
                    "米游社原神签到",
                    "",
                    {"user_id": event.user_id, "uid": uid},
                    "关闭成功",
                )
                await sign.finish(f"UID{uid}关闭米游社原神自动签到成功", at_sender=True)
            else:
                await sign.finish(
                    f"UID{uid}尚未开启米游社原神自动签到，无需关闭！", at_sender=True
                )


@all_sign.handle()
@all_sr_sign.handle()
async def _(event: Union[GroupMessageEvent, PrivateMessageEvent], matcher: Matcher):
    if isinstance(matcher, all_sign) and config.auto_sign_enable:
        await all_sign.send("开始执行全部原神重签，需要一定时间...")
        await bbs_auto_sign()
    elif isinstance(matcher, all_sr_sign) and config.sr_enable:
        await all_sr_sign.send("开始执行全部星铁重签，需要一定时间...")
        await sr_bbs_auto_sign()
    else:
        await all_sr_sign.finish("自动签到功能尚未开启", at_sender=True)


@get_coin.handle()
async def _(
    bot: Bot,
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    uid=CommandUID(),
    switch=CommandSwitch(),
):
    if switch is None:
        # 没有开关参数，手动执行米游币获取
        if f"{event.user_id}-{uid}" in coin_getting_list:
            await get_coin.finish("你已经在执行米游币获取任务中，请勿重复发送", at_sender=True)
        else:
            await get_coin.send(
                f"开始为UID{uid}执行米游币获取，耗时较久，请稍等...", at_sender=True
            )
            Logger.info(
                "米游币自动获取", "开始为", {"用户": event.user_id, "uid": uid, "执行获取": ""}
            )
            coin_getting_list.append(f"{event.user_id}-{uid}")
            judgment = isinstance(event, GroupMessageEvent)
            if judgment and event.group_id in config.group_allow_list:
                Logger.info(f"群聊{event.group_id}在白名单内,开始执行验证获取")
                result = await mhy_bbs_coin(True, str(event.user_id), uid)
            elif event.user_id in config.member_allow_list:
                Logger.info(f"用户{event.user_id}在白名单内,开始执行验证获取")
                result = await mhy_bbs_coin(True, str(event.user_id), uid)
            else:
                Logger.info(f"用户{event.user_id}不在白名单内,开始执行普通获取")
                result = await mhy_bbs_coin(False, str(event.user_id), uid)
            coin_getting_list.remove(f"{event.user_id}-{uid}")
            await get_coin.finish(result, at_sender=True)
    else:
        sub_data = {
            "user_id": event.user_id,
            "uid": uid,
            "sub_event": "米游币自动获取",
        }
        if switch:
            # switch为开启，则添加订阅
            if (
                ck := await PrivateCookie.get_or_none(
                    user_id=str(event.user_id), uid=uid
                )
            ) and ck.stoken is not None:
                await MihoyoBBSSub.update_or_create(
                    **sub_data,
                    defaults={
                        "group_id": event.group_id
                        if isinstance(event, GroupMessageEvent)
                        else event.user_id
                    },
                )
                Logger.info(
                    "米游币自动获取",
                    "",
                    {"user_id": event.user_id, "uid": uid},
                    "开启成功",
                )
                await sign.finish(f"UID{uid}开启米游币自动获取成功", at_sender=True)
            else:
                await get_coin.finish(
                    f"UID{uid}尚未绑定Cookie或Cookie中没有login_ticket！请先使用ysb指令绑定吧！",
                    at_sender=True,
                )
        else:
            # switch为关闭，则取消订阅
            if sub := await MihoyoBBSSub.get_or_none(**sub_data):
                await sub.delete()
                Logger.info(
                    "米游币自动获取",
                    "",
                    {"user_id": event.user_id, "uid": uid},
                    "关闭成功",
                )
                await sign.finish(f"UID{uid}关闭米游币自动获取成功", at_sender=True)
            else:
                await sign.finish(f"UID{uid}尚未开启米游币自动获取，无需关闭！", at_sender=True)


@all_coin.handle()
async def _(event: Union[GroupMessageEvent, PrivateMessageEvent]):
    if config.auto_myb_enable:
        await all_coin.send("开始执行myb全部重做，需要一定时间...")
        await bbs_auto_coin()
    else:
        await all_coin.send("没有开启米游币自动获取")


@ssbq.handle()
async def _(
    bot: Bot,
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    state: T_State,
    players=CommandPlayer(),  # noqa
):
    if state.get("clear_msg"):
        await ssbq.finish("开启提醒请用[ssbq提醒开启|关闭 提醒内容+数量]指令，比如[ssbq提醒开启树脂150]")
    for player in players:
        if f"{event.user_id}-{player.uid}" in ssbq_list:
            await ssbq.finish("你已经在查询体力任务中，请勿重复发送", at_sender=True)
        else:
            Logger.info("原神实时便签", "开始执行查询")
            ssbq_list.append(f"{event.user_id}-{player.uid}")
            judgment = isinstance(event, GroupMessageEvent)
            if judgment and event.group_id in config.group_allow_list:
                result = Message()
                result += await handle_ssbq(player, True)
            elif event.user_id in config.member_allow_list:
                result = Message()
                result += await handle_ssbq(player, True)
            else:
                result = Message()
                result += await handle_ssbq(player, False)
            ssbq_list.remove(f"{event.user_id}-{player.uid}")
        await ssbq.finish(result, at_sender=True)  # noqa


@ssbq_sub.handle()
async def _(
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    uid=CommandUID(),
    switch=CommandSwitch(),
    subs=sub_list(),  # noqa
):
    sub_data = {
        "user_id": event.user_id,
        "uid": uid,
        "remind_type": event.message_type,
    }
    if isinstance(event, GroupMessageEvent):
        sub_data["group_id"] = event.group_id
    if switch is None or switch:
        await DailyNoteSub.update_or_create(**sub_data, defaults=subs)
        Logger.info("原神实时便笺", "", sub_data.update(subs), "添加提醒成功")
        subs_info = await get_subs(**sub_data)
        await ssbq_sub.finish(f"开启提醒成功，{subs_info}", at_sender=True)
    else:
        s = await DailyNoteSub.get_or_none(**sub_data)
        if not s:
            await ssbq_sub.finish("你在当前会话尚未开启任何订阅", at_sender=True)
        else:
            if "resin_num" in subs:
                s.resin_num = None
            if "coin_num" in subs:
                s.coin_num = None
            if s.resin_num is None and s.coin_num is None:
                await s.delete()
            else:
                await s.save()
            await ssbq_sub.finish("已关闭当前会话的对应提醒", at_sender=True)


@get_num.handle()
async def _(event: PrivateMessageEvent, arg: Message = CommandArg()):
    url_to_key = {
        "人人": "rr",
        "rr": "rr",
        "sf": "sf",
        "三方": "sf",
        "tt": "tt",
        "套套": "tt",
    }
    url_choice = arg.extract_plain_text().strip()
    if not url_choice:
        return await get_num.finish("请在后面加上你要查询积分的平台", at_sender=True)
    key = url_to_key.get(url_choice, "other")
    if key == "other":
        return await get_num.finish("没有这种平台", at_sender=True)
    result = await gain_num(key)
    if result is None:
        return await get_num.finish(
            "请求失败，请检查key是否失效或填写错误或网络问题，详细查看后台", at_sender=True
        )
    await get_num.finish(f"剩余{result}", at_sender=True)


@sr_sign.handle()
async def _(
    bot: Bot,
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    switch=CommandSwitch(),
):
    from LittlePaimon.plugins.star_rail_info.data_handle import (
        get_uid as get_sr_uid,
    )

    sr_uid = get_sr_uid(str(event.user_id))  # 星铁uid
    from LittlePaimon.utils.message import (
        get_uid as get_gs_uid,
    )  # 原神uid 用于获取ck

    uid = await get_gs_uid(event=event)
    if not sr_uid:
        await sr_sign.finish("请先使用命令[星铁绑定uid]来绑定星穹铁道UID")
    if not uid:
        await sr_sign.finish("请先使用命令[ysb uid]来绑定原神UID")
    if switch is None:
        if f"{event.user_id}-{sr_uid}" in sr_list:
            await sr_sign.finish(f"你已经在执行签到任务中，请勿重复发送", at_sender=True)
        else:
            from .handle.sr_sign_handle import sr_sign_in
            await sr_sign.send(f"开始为UID{sr_uid}执行星铁签到", at_sender=True)
            Logger.info(
                "星铁签到",
                "➤",
                {"用户": str(event.user_id), "uid": sr_uid},
                "执行签到",
                True,
            )
            sr_list.append(f"{event.user_id}-{sr_uid}")
            judgment = isinstance(event, GroupMessageEvent)
            if judgment and event.group_id in config.group_allow_list:
                Logger.info(f"群聊{event.group_id}在白名单内,开始执行验证签到")
                _, result = await sr_sign_in(True, str(event.user_id), sr_uid, uid)
            elif event.user_id in config.member_allow_list:
                Logger.info(f"用户{event.user_id}在白名单内,开始执行验证签到")
                _, result = await sr_sign_in(True, str(event.user_id), sr_uid, uid)
            else:
                Logger.info(f"用户{event.user_id}不在白名单内,开始执行普通签到")
                _, result = await sr_sign_in(False, str(event.user_id), sr_uid, uid)
            sr_list.remove(f"{event.user_id}-{sr_uid}")
            await sr_sign.finish(result, at_sender=True)
    else:
        sub_data = {
            "user_id": event.user_id,
            "uid": uid,
            "sub_event": "星铁签到",
        }
        if switch:
            # switch为开启，则添加订阅
            if await PrivateCookie.get_or_none(
                user_id=str(event.user_id), uid=uid
            ):
                await MihoyoBBSSub.update_or_create(
                    **sub_data,
                    defaults={
                        "group_id": event.group_id
                        if isinstance(event, GroupMessageEvent)
                        else event.user_id
                    },
                )
                Logger.info(
                    "星铁自动签到",
                    "➤",
                    {"用户": str(event.user_id), "uid": sr_uid},
                    "开启成功",
                )
                await sr_sign.finish(f"UID{sr_uid}开启星铁签到成功", at_sender=True)
            else:
                await sr_sign.finish(
                    f"UID{sr_uid}尚未绑定Cookie！请先使用<原神扫码绑定>指令绑定吧！", at_sender=True
                )
        else:
            # switch为关闭，则取消订阅
            if sub := await MihoyoBBSSub.get_or_none(**sub_data):
                await sub.delete()
                Logger.info(
                    "星铁自动签到",
                    "➤",
                    {"用户": str(event.user_id), "uid": sr_uid},
                    "关闭成功",
                )
                await sr_sign.finish(f"UID{sr_uid}关闭星铁自动签到成功", at_sender=True)
            else:
                await sr_sign.finish(
                    f"UID{sr_uid}尚未开启星铁自动签到，无需关闭！", at_sender=True
                )
    await sr_sign.finish(config.hfu, at_sender=True)
