import httpx


async def sf(third_api, gt, challenge):
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(third_api + f"gt={gt}&challenge={challenge}", timeout=60)
        return response.json()


async def sf_jifen(token):
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(f"http://api.fuckmys.tk/token?token={token}")
        return response.json()