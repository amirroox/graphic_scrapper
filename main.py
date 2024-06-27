import re

import requests
from fastapi import FastAPI, Query

from config import config
from scraperModules.flatIcon import FlatIcon
from scraperModules.freepik import FreePik

REGEX_LINK = r'https?://(www\.)?(\w+\.)+\w+(/\S*)?(\?\S*)?(\#\S*)?'
app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello Man"}


@app.get("/freepik")
async def get_freepic(model: str = Query(title="vector", default='vector'),
                      link: str = Query(title="link", default=None),
                      title: str = Query(title="title", default=None),
                      size: str = Query(title="size", default=None),
                      formats: str = Query(title="formats", default=None),
                      license_: str = Query(title="license", default=None),
                      tags: str = Query(title="tags", default=None),
                      transfer: str = Query(title="transfer", default=None),
                      max_limit: int = Query(title="transfer", default=25),):
    scraper = FreePik()
    if link and ('?' in link or '#' in link):
        link = link.split('?')[0].split('#')[0]
    result = None
    if model == 'vector':
        result = scraper.search_vector(link, title, size, formats, license_, tags, transfer, max_limit)
    else:
        return {
            "message": "Model Not Found!",
            'result': False,
            'Models': [
                'vector', 'photo', 'ai'
            ]
        }
    if result:
        return {
            "message": "Found It!",
            'result': result
        }
    if link:
        try:
            response = requests.get(link)
            if response.status_code == 404:
                return {
                    "message": "Link Not Valid!",
                    "result": False
                }
            elif response.status_code == requests.codes.ok:
                try:
                    result = scraper.scrape_vector(link, True)
                    return {
                        "message": "Scrap Done!",
                        "result": result
                    }
                except Exception as ex:
                    print(ex)
                    return {
                        "message": "Scrap Failed",
                        "result": False
                    }
            else:
                return {
                    "result": False
                }

        except Exception as ex:
            print(ex)
            return {
                "message": "Link Not Valid!",
                "result": False
            }
    return {
        "message": "Please Enter Link!",
        "result": False
    }


@app.get("/flaticon")
async def get_flaticon(link: str = Query(..., title="Link")):
    if re.fullmatch(REGEX_LINK, link) is None:
        return {
            "result": False,
            "message": "Please Enter Valid Link!"
        }
    scraper = FlatIcon()
    name = link.replace('//', '/').split('/')[-1].split('?')[0]
    if not scraper.search(name):
        scraper.scrape_once(link, name)
        scraper.close_driver()
    path = f"{config.PATH_DOWNLOAD}/{name}/{name}.png"
    return {
        "result": True,
        "path": f"{path}"
    }
