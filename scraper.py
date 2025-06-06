import requests
from bs4 import BeautifulSoup
import json
import os
import re

url = "https://www.rightmove.co.uk/property-for-sale/find.html?searchLocation=Jesmond%2C+Newcastle+Upon+Tyne&useLocationIdentifier=true&locationIdentifier=REGION%5E13653&radius=0.0&maxDaysSinceAdded=3&_includeSSTC=on"
headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

# Find the results section
results_section = soup.find("section", class_="ResultsList_resultsSection__MVSi7 null")
property_cards = results_section.find_all("div", class_="PropertyCard_propertyCardContainerWrapper__mcK1Z") if results_section else []

properties = {}

for card in property_cards:
    a_tag = card.find("a", class_="PropertyCard_propertyCardAnchor__s2ZaP")
    prop_id = a_tag.get("id", "no-id-found") if a_tag else "no-anchor"

    address_tag = card.find("address")
    address = address_tag.get_text(strip=True) if address_tag else "No address"

    price_tag = card.find("div", class_="PropertyPrice_price__VL65t")
    price = price_tag.get_text(strip=True) if price_tag else "No price"

    type_tag = card.find("span", class_="PropertyInformation_propertyType__u8e76")
    prop_type = type_tag.get_text(strip=True) if type_tag else "Unknown type"

    beds_tag = card.find("span", class_="PropertyInformation_bedroomsCount___2b5R")
    beds = beds_tag.get_text(strip=True) if beds_tag else "?"

    baths_tag = card.find("div", class_="PropertyInformation_bathContainer__ut8VY")
    baths = "?"  # Default
    if baths_tag:
        bath_span = baths_tag.find("span", attrs={"aria-label": re.compile(r"\d+ in property")})
        if bath_span:
            baths = bath_span.get_text(strip=True)

    image_tag = card.find("img", alt="camera icon")
    image_count = "0"
    if image_tag and image_tag.has_attr("aria-label"):
        match = re.search(r"(\d+)", image_tag["aria-label"])
        if match:
            image_count = match.group(1)

    desc_tag = card.find("p", class_="PropertyCardSummary_summary__oIv57")
    description = desc_tag.get_text(strip=True) if desc_tag else "No description"

    properties[prop_id] = {
        "address": address,
        "price": price,
        "type": prop_type,
        "beds": beds,
        "baths": baths,
        "images": image_count,
        "description": description
    }

# Load previously seen IDs
if os.path.exists("seen.json"):
    with open("seen.json", "r", encoding="utf-8") as f:
        seen_data = json.load(f)
else:
    seen_data = {}

# Find new properties only
new_properties = {
    pid: data for pid, data in properties.items()
    if pid not in seen_data
}

# Update seen.json
with open("seen.json", "w", encoding="utf-8") as f:
    json.dump(properties, f, indent=2, ensure_ascii=False)

# Save only new properties if any
if new_properties:
    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(new_properties, f, indent=2, ensure_ascii=False)
else:
    print("No new properties found.")
