
import requests
import csv
import os
import time

API_URL = "https://steamspy.com/api.php"
CSV_FILE = os.path.join(os.path.dirname(__file__), "games.csv")

FIELDS = [
    "Game Title",
    "Platform",
    "Positive Reviews",
    "Negative Reviews",
    "Publisher",
    "Developer",
    "Rating",
    "Price"
]


def scrape_games(
    progress_callback=None,
    status_callback=None,
    pause_event=None,
    stop_event=None,
    total_pages=20,
    delay=60
):
    def stopped():
        return stop_event is not None and stop_event.is_set()

    def wait_if_paused():
        while pause_event is not None and pause_event.is_set():
            if stopped():
                return False
            time.sleep(0.2)
        return not stopped()

    def report_status(message):
        print(message)
        if status_callback:
            status_callback(message)

    def save_games(games):
        with open(CSV_FILE, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(games.values())

    existing_games = {}

    # Load existing games so that data is not lost
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r", newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            for row in reader:
                title = (row.get("Game Title") or "").strip()
                if title:
                    existing_games[title.lower()] = row

    report_status(f"Starting with {len(existing_games)} existing games.")

    for page in range(total_pages):
        if not wait_if_paused():
            break

        report_status(f"Fetching page {page + 1}/{total_pages}...")

        try:
            response = requests.get(
                API_URL,
                params={"request": "all", "page": page},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

        except (requests.RequestException, ValueError) as error:
            report_status(f"Page {page + 1} failed: {error}")
            if progress_callback:
                progress_callback(page + 1, total_pages, len(existing_games))
            continue

        if isinstance(data, dict):
            for game in data.values():
                if stopped():
                    break

                title = str(game.get("name") or "").strip()
                if not title:
                    continue

                try:
                    positive = int(game.get("positive", 0) or 0)
                    negative = int(game.get("negative", 0) or 0)
                    votes = positive + negative
                    rating = round(positive / votes * 100, 2) if votes else ""
                except (TypeError, ValueError, ZeroDivisionError):
                    positive = 0
                    negative = 0
                    rating = ""

                existing_games[title.lower()] = {
                    "Game Title": title,
                    "Platform": "PC (Steam)",
                    "Positive Reviews": positive,
                    "Negative Reviews": negative,
                    "Publisher": game.get("publisher", "") or "",
                    "Developer": game.get("developer", "") or "",
                    "Rating": rating,
                    "Price": game.get("price", "") or ""
                }

        # Save after every page so partial work is preserved
        save_games(existing_games)

        if progress_callback:
            progress_callback(page + 1, total_pages, len(existing_games))

        report_status(f"Unique games collected: {len(existing_games)}")

        if stopped():
            break

        # Wait between pages, while still allowing pause and stop
        if page < total_pages - 1:
            waited = 0
            while waited < delay:
                if not wait_if_paused():
                    break
                if stopped():
                    break
                time.sleep(0.2)
                waited += 0.2

        if stopped():
            break

    save_games(existing_games)

    if stopped():
        report_status(f"Stopped. Saved {len(existing_games)} games.")
    else:
        report_status(f"Finished! Saved {len(existing_games)} unique games.")

    return len(existing_games)


if __name__ == "__main__":
    scrape_games()
