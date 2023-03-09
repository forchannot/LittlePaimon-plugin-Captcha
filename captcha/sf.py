from LittlePaimon.utils.requests import aiorequests


async def sf(third_api, gt, challenge):
    response = await aiorequests.get(
        url=f"{third_api}gt={gt}&challenge={challenge}", timeout=60
    )
    return response.json()


async def sf_jifen(token):
    response = await aiorequests.get(url=f"http://api.fuckmys.tk/token?token={token}")
    return response.json()
