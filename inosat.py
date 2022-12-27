import csv
from typing import Any

import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
from aiohttp_retry import RetryClient, ExponentialRetry
from codetiming import Timer
from fake_useragent import UserAgent

pages_list = []
URL = "https://www.i-a.by/katalog-produkcii/cifrovoe-proizvodstvo"
DOMAIN = "https://www.i-a.by"
UA = UserAgent()
FAKE_UA = {"user-agent": UA.random}


def get_soup(url: str) -> BeautifulSoup:
    """Create soup from request"""
    resp = requests.get(url=url, headers=FAKE_UA)
    return BeautifulSoup(resp.text, "html5lib")


def get_urls_pages(soup: BeautifulSoup) -> None:
    """Form a list of pages"""
    start_page = soup.find("ul", class_="pagination").find("a").text
    end_page = soup.find("li", class_="pager-last").find("a")
    pages_list.append(URL)
    for page in range(int(start_page), int(end_page["href"].split("=")[-1]) + 1):
        pages_list.append(URL + "?page=" + str(page))


def write_file(no_image_list: list) -> csv:
    """Save into csv file"""
    with open("../no_images.csv", mode="a", newline="\n", encoding="UTF-8") as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerows(no_image_list)


async def get_data_with_sem(sem: Any, session: Any, link: str) -> callable:
    """Semaphore function"""
    async with sem:
        return await get_data(session, link)


async def get_data(session: Any, link: str) -> None:
    """
    Filter a page on "no_image" or "noimage" phrase.
    Put it to the list and call a write function.
    """
    retry_options = ExponentialRetry(attempts=5)
    retry_client = RetryClient(
        raise_for_status=False,
        retry_options=retry_options,
        client_session=session,
        start_timeout=3,
    )
    async with retry_client.get(link) as response:
        print(response.status, link)
        if response.ok:
            filtered_list = []
            resp = await response.text()
            soup2 = BeautifulSoup(resp, "html5lib")
            articles = soup2.find_all("td", class_="views-field views-field-title")
            images = soup2.select("img[class=img-responsive]")

            for article, image in zip(articles, images):
                if "no_image" in image["src"] or "noimage" in image["src"]:
                    filtered_list.append(
                        [article.text, DOMAIN + article.find("a")["href"]]
                    )
            write_file(filtered_list)
        else:
            print(response.status, link)


async def main():
    """
    Create a session and form a list of asyncio tasks.
    Task is created based on function call with parameters:
        sem : asyncio.Semaphore
        session : aiohttp.ClientSession
        link : str
            image link
    """
    connector = aiohttp.TCPConnector(force_close=True, limit=30)
    sem = asyncio.Semaphore(30)
    async with aiohttp.ClientSession(
        headers=FAKE_UA, trust_env=True, connector=connector
    ) as session:
        tasks = [
            asyncio.create_task(get_data_with_sem(sem, session, link))
            for link in pages_list
        ]
        await asyncio.gather(*tasks)


get_urls_pages(get_soup(URL))
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
with Timer(text=f"Затрачено времени на запрос: {{:.3f}} сек"):
    asyncio.run(main())
