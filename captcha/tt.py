from LittlePaimon.utils.requests import aiorequests

from ..config.config import config


async def tt(gt, challenge, referer):
    response = await aiorequests.post(
        "http://api.ttocr.com/api/recognize",
        data={
            "appkey": config.ttocr_key,
            "gt": gt,
            "challenge": challenge,
            "itemid": 388,
            "referer": referer,
        },
        timeout=60,
    )
    return response.json()


async def tt_result(result_id):
    res = await aiorequests.post(
        url="http://api.ttocr.com/api/results",
        data={
            "appkey": config.ttocr_key,
            "resultid": result_id,
        },
        timeout=60,
    )
    return res.json()


async def tt_jifen():
    res = await aiorequests.get(
        url=f"http://api.ttocr.com/api/points?appkey={config.ttocr_key}"
    )
    return res.json()
