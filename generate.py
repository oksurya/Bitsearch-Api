import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request, redirect, url_for
import re
import csv
import time
import os

app = Flask(__name__)

class Bitsearch:

    def __init__(self):
        self.BASE_URL = "https://bitsearch.to"
        self.LIMIT = None

# Function to scrape torrents from a website
def scrape_bitsearch(query, page):
    bs = Bitsearch()
    url = bs.BASE_URL + "/search?q={}&page={}".format(query, page)
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
                hash_value = re.search(
                    r"([{a-f\d,A-F\d}]{32,40})\b", magnet
                ).group(0)
                my_dict["data"].append(
                    {
                        "name": name,
                        "size": size,
                        "seeders": seeders,
                        "leechers": leechers,
                        "category": category,
                        "hash": hash_value,
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

# Function to write data to a CSV file
# Function to write data to a CSV file in a folder
def write_to_csv(data, query):
    if data and 'data' in data:
        folder_name = query.replace(' ', '_')  # Create folder name from the query
        os.makedirs(folder_name, exist_ok=True)  # Create the folder if it doesn't exist

        filename = os.path.join(folder_name, f'{query}_data.csv')
        count = 1
        while os.path.isfile(filename):
            filename = os.path.join(folder_name, f'{query}_data_{count}.csv')
            count += 1

        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ["name", "size", "seeders", "leechers", "category", "hash", "magnet", "torrent", "url", "date", "downloads"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for item in data['data']:
                writer.writerow(item)

# API endpoint to get the scraped torrents as JSON
@app.route("/search", methods=['GET'])
def get_torrents():
    query = request.args.get('q', '')
    page = int(request.args.get('page', 1))
    my_dict = scrape_bitsearch(query, page)
    
    # Write data to CSV file
    write_to_csv(my_dict, query)
    
    # Redirect to the next page if available
    if my_dict["current_page"] < my_dict["total_pages"]:
        next_page = my_dict["current_page"] + 1
        return redirect(url_for('get_torrents', q=query, page=next_page))
    else:
        return jsonify(my_dict)

if __name__ == '__main__':
    app.run()
