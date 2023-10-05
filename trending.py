import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify
import re
import time

app = Flask(__name__)

class Bitsearch:

    def __init__(self):
        self.BASE_URL = "https://bitsearch.to/trending"
        self.LIMIT = None

# Function to scrape quotes from a website
def scrape_quotes():
    bs = Bitsearch()
    url = bs.BASE_URL
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        my_dict = {"data": []}
        for divs in soup.find_all("li", class_="search-result"):
            info = divs.find("div", class_="info")
            name = info.find("h5", class_="title").find("a").text
            url = info.find("h5", class_="title").find("a")["href"]
            category = info.find("div").find(
                "a", class_="category").text
            if not category:
                continue
            stats = info.find("div", class_="stats").find_all("div")
            if stats:
                downloads = stats[0].text
                size = stats[1].text
                seeders = stats[2].text.strip()
                leechers = stats[3].text.strip()
                date = stats[4].text
                links = divs.find("div", class_="links").find_all("a")
                magnet = links[1]["href"]
                torrent = links[0]["href"]
                my_dict["data"].append(
                    {
                        "name": name,
                        "size": size,
                        "seeders": seeders,
                        "leechers": leechers,
                        "category": category,
                        "hash": re.search(
                            r"([{a-f\d,A-F\d}]{32,40})\b", magnet
                        ).group(0),
                        "magnet": magnet,
                        "torrent": torrent,
                        "url": bs.BASE_URL + url,
                        "date": date,
                        "downloads": downloads,
                    }
                )
            if bs.LIMIT and len(my_dict["data"]) == bs.LIMIT:
                break
        try:
            total_pages = (
                int(
                    soup.select(
                        "body > main > div.container.mt-2 > div > div:nth-child(1) > div > span > b"
                    )[0].text
                )
                / 20
            )  # 20 search results available on each page
            total_pages = (
                total_pages + 1
                if isinstance(total_pages, float)
                else total_pages
                if total_pages > 0
                else total_pages + 1
            )

            current_page = int(
                soup.find("div", class_="pagination")
                .find("a", class_="active")
                .text
            )
            my_dict["current_page"] = current_page
            my_dict["total_pages"] = int(total_pages)
        except:
            pass
        return my_dict
    else:
        return []

# API endpoint to get the scraped quotes as JSON
@app.route('/api/trending', methods=['GET'])
def get_quotes():
    my_dict = scrape_quotes()
    return jsonify(my_dict)

if __name__ == '__main__':
    app.run()
