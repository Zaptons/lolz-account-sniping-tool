import re
from typing import Optional, Tuple

# Assuming this import is correct, relative to the current file's location
from .base import BaseMarketAPI


class MarketAPI(BaseMarketAPI):
    def search(self, category: str, search_params: str) -> dict:
        response = self.api_request(f"{category}/{search_params}")
        return response


def parse_search_data(search_url: str) -> Optional[Tuple[str, str]]:
    parse = re.search(r"https://lzt\.market/([\w\-]+)/?\??(.+)?", search_url)
    if not parse:
        return None
    category, search_params = parse.groups()
    return category, search_params if search_params else ""


if __name__ == "__main__":
    # Given search URLs
    search_urls = "https://lzt.market/steam/rust?currency=eur&pmax=3&mm_ban=nomatter&order_by=price_to_up,https://lzt.market/valorant/?currency=eur&pmax=20&weaponSkin[]=84d840c5-4479-4395-d823-e7acbe634c5e&region[]=EU,https://lzt.market/valorant/?currency=eur&pmax=20&weaponSkin[]=1ea64c8d-43c4-fce8-7354-01bdd6c0ee17&region[]=EU,https://lzt.market/valorant/?currency=eur&pmax=15&buddy[]=6fd8192b-4045-a7c2-057f-6180c39b2545&region[]=EU,https://lzt.market/valorant/?currency=eur&pmax=15&buddy[]=a0d5de55-4f72-f0cf-046f-d8a872f631b3&region[]=EU,https://lzt.market/valorant/?currency=eur&pmax=15&buddy[]=46d903ab-463a-51c3-43d6-0b819579c32f&region[]=EU,https://lzt.market/valorant/?currency=eur&pmax=15&buddy[]=9d803f91-483f-eefb-eddc-bbb0283a2b5e&region[]=EU,https://lzt.market/valorant/?currency=eur&pmax=50&weaponSkin[]=84d840c5-4479-4395-d823-e7acbe634c5e&weaponSkin[]=1ea64c8d-43c4-fce8-7354-01bdd6c0ee17&region[]=EU,https://lzt.market/valorant/?currency=eur&pmax=30&buddy[]=ad508aeb-44b7-46bf-f923-959267483e78&region[]=EU"

    # Parse the search URLs to extract category and search_params
    result = parse_search_data(search_urls)

    if result is None:
        print("Invalid search URL format.")
    else:
        for category, search_params in result:
            # Create an instance of the MarketAPI class
            market_api = MarketAPI()

            # Perform the search using the extracted category and search_params
            response = market_api.search(category, search_params)

            # Print the search result
            print(response)