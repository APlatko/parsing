from fake_useragent import UserAgent
from time import perf_counter
import time
import aiofiles
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import os
import requests


UA = UserAgent()
FAKE_UA = {"user-agent": UA.random}
URL = "https://itvendor.by/brands/"


def get_src_list() -> list:
    """Make a request to the site URL and form a list of images links."""
    response = requests.get(url=URL, headers=FAKE_UA)
    response.encoding = "utf-8"
    soup = BeautifulSoup(response.text, "html5lib")
    pictures_url = soup.find("table").find_all("img")
    pictures_list = [x["src"] for x in pictures_url]
    return pictures_list


async def write_file(session, url: str, name_img: str, image_number) -> None:
    """Download and save images"""
    path = fr"itvendor_images\image{image_number}.{name_img}"
    async with aiofiles.open(path, mode="wb") as image:
        async with session.get(url) as response:
            async for chunk in response.content.iter_chunked(2048):
                await image.write(chunk)


async def main(pictures_list: list) -> None:
    """
    Create a session and form a list of asyncio tasks.
    Task is created based on function call with parameters:
        session : aiohttp.ClientSession
        link : str
            image link
        ext_img : str
            extension of the file, based on the image link ending
        num: int
            number of image, start from 1
    """
    tasks = []
    async with aiohttp.ClientSession(headers=FAKE_UA, trust_env=True) as session:
        for num, link in enumerate(pictures_list, 1):
            ext_img = link.rsplit(".")[-1]
            task = asyncio.create_task(write_file(session, link, ext_img, num))
            tasks.append(task)
            await asyncio.gather(*tasks)


start = perf_counter()
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main(get_src_list()))
print(
    f'Saved {len(os.listdir("../itvendor_images/"))} images in {round(time.perf_counter() - start, 3)} seconds.'
)
