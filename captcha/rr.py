from LittlePaimon.utils.requests import aiorequests

from ..config.config import config


async def rr(gt, challenge, referer):
    response = await aiorequests.post(
        url="http://api.rrocr.com/api/recognize.html",
        params={
            "appkey": config.rrocr_key,
            "gt": gt,
            "challenge": challenge,
            "referer": referer,
            "sharecode": "585dee4d4ef94e1cb95d5362a158ea54",
        },
        timeout=60,
    )
    return response.json()


async def rr_jifen():
    jf = await aiorequests.get(
        f"http://api.rrocr.com/api/integral.html?appkey={config.rrocr_key}"
    )
    return jf.json()
