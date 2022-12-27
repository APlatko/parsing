# parsing

inosat.py

goal : determine which catalog pages do not have images. put article and link into csv.
libraries : requests for making list of all pages; use asyncio, aiohttp for numerous requests; beautifulsoup for gathering necessary information.
info : site has 5400+ catalog pages. every page has 30 items. Check every item image link, if it includes "no_image" or "noimage" phrase - put the information about this item into csv.
