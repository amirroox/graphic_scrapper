from scraperModules import freepik

# Scrap Script
scraper = freepik.FreePik()  # Initial
scraper.scrape_vectors(account=True)  # Main scrapper
scraper.close_driver()  # Close
