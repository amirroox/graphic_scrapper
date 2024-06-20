import re
from fastapi import FastAPI, Query

from config import config
from scraperModules.flatIcon import FlatIcon

REGEX_LINK = r'https?://(www\.)?(\w+\.)+\w+(/\S*)?(\?\S*)?(\#\S*)?'
app = FastAPI()
scraper = FlatIcon()


@app.get("/")
async def root():
    return {"message": "Hello Flat Icon"}


@app.get("/flaticon")
async def get_flaticon(link: str = Query(..., title="Link")):
    if re.fullmatch(REGEX_LINK, link) is None:
        return {
            "result": False,
            "message": "Please Enter Valid Link!"
        }
    name = link.replace('//', '/').split('/')[-1].split('?')[0]
    if not scraper.search(name):
        scraper.scrape_once(link, name)
        scraper.close_driver()
    path = f"{config.PATH_DOWNLOAD}/{name}/{name}.png"
    return {
        "result": True,
        "path": f"{path}"
    }
