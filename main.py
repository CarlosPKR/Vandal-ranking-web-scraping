from source.scraper import scrape_vandal_games
import pandas as pd

if __name__ == "__main__":
    data = scrape_vandal_games(limit = 1)
    df = pd.DataFrame(data)
    df.to_csv("dataset/dataset_vandal.csv", index=False, sep=";", encoding="utf-8-sig")

    print("¡Scraping finalizado!")