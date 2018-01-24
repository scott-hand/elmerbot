import arrow
import csv
import io
import json
import logging
import os
import requests
import statistics
from collections import defaultdict
from fuzzywuzzy import process


SPREADSHEET_URL = "https://docs.google.com/spreadsheets/export?format=csv&id=1X1HTxkI6SqsdpNSkSSivMzpxNT-oeTbjFFDdEkXD30o"


def parse_date(date):
    # The dates are inconsistent but are approximately MM/DD/YY
    # Some of them also have repeated slashes (11//29/15)
    # Others use . or - as dividers
    # For the ones that are completely unsalvageable, just put 1 Jan 2000
    try:
        divider = "/"
        if "-" in date:
            divider = "-"
        elif "." in date:
            divider = "."
        divider = "/" if "/" in date else "-"
        m, d, y = [int(f) for f in date.replace(divider * 2, divider).split(divider)]
        if y < 2000:
            y += 2000
        clean_str = "{}/{}/{}".format(str(m).zfill(2), str(d).zfill(2), y)
        return arrow.get(clean_str).format("YYYY-MM-DD")
    except:
        return "2000-01-01"



class ReviewData(object):
    def __init__(self):
        self._cache = None
        self._expires = None
        self._id_idx = {}
        self._rev_id_idx = {}
        self.avg = 0
        self.stddev = 0
        self._logger = logging.getLogger("elmerbot.scraper")

    def _build_id_index(self):
        for idx, wname in enumerate(self._cache):
            self._id_idx[wname] = idx + 1 
            self._rev_id_idx[idx + 1] = wname

    def _compute_stats(self):
        scores = []
        for reviews in self._cache.values():
            for review in reviews:
                if review["rating"]:
                    scores.append(review["rating"])
        self.avg = round(statistics.mean(scores), 2)
        self.stddev = round(statistics.stdev(scores), 2)

    def _reload(self):
        self._logger.info("Reloading review data...")

        # Try from cached file
        if os.path.exists("/tmp/review_cache.json"):
            self._logger.info("Loading from file cache...")
            data = json.load(open("/tmp/review_cache.json"))
            if arrow.get().timestamp < data["expiration"]:
                self._cache = data["cache"]
                self._expires = data["expiration"]
                self._build_id_index()
                self._compute_stats()
                return

        response = requests.get(SPREADSHEET_URL)
        if response.status_code != 200:
            return

        buff = io.StringIO(response.text)
        reader = csv.DictReader(buff, delimiter=",", quotechar="\"")

        self._cache = defaultdict(list)
        self._expires = arrow.get().replace(hours=1).timestamp

        total = 0
        for idx, row in enumerate(reader):
            total += 1
            entry = {"name": row["Whisky Name"].strip(),
                     "username": row["Reviewer's Reddit Username"].strip(),
                     "link": row["Link To Reddit Review"].strip(),
                     "price": row["Full Bottle Price Paid"],
                     "date": parse_date(row["Date of Review"]), "id": idx}
            try:
                entry["rating"] = int(row["Reviewer Rating"].strip())
            except:
                entry["rating"] = None
            self._cache[row["Whisky Name"].strip()].append(entry)

        self._build_id_index()
        self._compute_stats()

        with open("/tmp/review_cache.json", "w") as fout:
            fout.write(json.dumps({"expiration": self._expires, "cache": self._cache}))
        self._logger.info("Finished. {} reviews indexed".format(total))

    @property
    def stale(self):
        return not self._cache or arrow.get().timestamp >= self._expires

    @property
    def reviews(self):
        if self.stale:
            self._reload()
        return self._cache

    def search(self, pattern, matches=5):
        results = process.extractBests(pattern, self.reviews.keys(), processor=lambda x: x, limit=matches, score_cutoff=70)
        return [(result, self._id_idx[result], conf) for result, conf in results]

    def find(self, whisky_id):
        name = self._rev_id_idx.get(whisky_id)
        return self._cache.get(name, [])

    def most_recent(self, name=None, whisky_id=None, limit=5):
        if not name:
            name = self._rev_id_idx.get(whisky_id)
        reviews = self._cache.get(name, [])
        reviews.sort(key=lambda review: review["date"])
        return reviews[::-1][:limit] if limit else reviews
