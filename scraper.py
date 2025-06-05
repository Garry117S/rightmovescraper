import requests
from bs4 import BeautifulSoup
import json

url = "https://www.rightmove.co.uk/property-for-sale/find.html?searchLocation=Jesmond%2C+Newcastle+Upon+Tyne&useLocationIdentifier=true&locationIdentifier=REGION%5E13653&radius=0.0&maxDaysSinceAdded=3&_includeSSTC=on"
headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

# Find all property containers
property_cards = soup.find_all("div", class_="PropertyCard_propertyCardContainerWrapper__mcK1Z")

properties = {}

for card in property_cards:
    a_tag = card.find("a", class_="PropertyCard_propertyCardAnchor__s2ZaP")
    prop_id = a_tag.get("id", "no-id-found") if a_tag else "no-anchor"
    card_text = card.get_text(separator=' ', strip=True)
    properties[prop_id] = card_text

# Save to file
with open("results.json", "w", encoding="utf-8") as f:
    json.dump(properties, f, indent=2, ensure_ascii=False)
