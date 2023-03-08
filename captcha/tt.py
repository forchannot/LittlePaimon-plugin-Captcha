import httpx

from ..config.config import config


async def tt(gt, challenge, referer):
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.post(
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
    async with httpx.AsyncClient(follow_redirects=True) as client:
        res = await client.post(
            "http://api.ttocr.com/api/results",
            data={
                "appkey": config.ttocr_key,
                "resultid": result_id,
            },
            timeout=60,
        )
        return res.json()


async def tt_jifen():
    async with httpx.AsyncClient(follow_redirects=True) as client:
        res = await client.get(
            f'http://api.ttocr.com/api/points?appkey={config.ttocr_key}'
        )
        return res.json()
