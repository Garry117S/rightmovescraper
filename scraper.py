import requests
from bs4 import BeautifulSoup
import json
import os
import re
from hashlib import md5
from datetime import datetime
import glob

# === CONFIGURATION ===
# url = "https://www.rightmove.co.uk/property-for-sale/find.html?searchLocation=Jesmond%2C+Newcastle+Upon+Tyne&useLocationIdentifier=true&locationIdentifier=REGION%5E13653&radius=0.0&maxDaysSinceAdded=3&_includeSSTC=on"
url = "https://www.rightmove.co.uk/property-for-sale/find.html?searchLocation=Jesmond%2C+Newcastle+Upon+Tyne&useLocationIdentifier=true&locationIdentifier=REGION%5E13653&radius=0.0&maxDaysSinceAdded=7&_includeSSTC=on&index=0&sortType=2&channel=BUY&transactionType=BUY&displayLocationIdentifier=Jesmond.html"

headers = {"User-Agent": "Mozilla/5.0"}

# === FETCH PAGE ===
response = requests.get(url, headers=headers)
if response.status_code != 200:
    print(f"Failed to fetch Rightmove page. Status code: {response.status_code}")
    exit(1)

soup = BeautifulSoup(response.text, 'html.parser')
results_section = soup.find("section", class_="ResultsList_resultsSection__MVSi7 null")
property_cards = results_section.find_all("div", class_="PropertyCard_propertyCardContainerWrapper__mcK1Z") if results_section else []

properties = {}

# === PARSE PROPERTIES ===
for card in property_cards:
    a_tag = card.find("a", class_="PropertyCard_propertyCardAnchor__s2ZaP")
    if a_tag:
        href = a_tag.get("href", "")
        prop_id = a_tag.get("id") or md5(href.encode()).hexdigest()
    else:
        prop_id = "no-anchor"

    address = card.find("address")
    address = address.get_text(strip=True) if address else "No address"

    price = card.find("div", class_="PropertyPrice_price__VL65t")
    price = price.get_text(strip=True) if price else "No price"

    prop_type = card.find("span", class_="PropertyInformation_propertyType__u8e76")
    prop_type = prop_type.get_text(strip=True) if prop_type else "Unknown type"

    beds = card.find("span", class_="PropertyInformation_bedroomsCount___2b5R")
    beds = beds.get_text(strip=True) if beds else "?"

    baths = "?"
    bath_container = card.find("div", class_="PropertyInformation_bathContainer__ut8VY")
    if bath_container:
        bath_span = bath_container.find("span", attrs={"aria-label": re.compile(r"\d+ in property")})
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

# Load previously seen properties
if os.path.exists("seen.json"):
    try:
        with open("seen.json", "r", encoding="utf-8") as f:
            content = f.read().strip()
            seen_data = json.loads(content) if content else {}
    except json.JSONDecodeError:
        print("Warning: seen.json is corrupted or invalid. Starting fresh.")
        seen_data = {}
else:
    seen_data = {}


# === FIND NEW PROPERTIES ===
new_properties = {
    pid: data for pid, data in properties.items()
    if pid not in seen_data
}

# === DEBUG OUTPUT ===
if new_properties:
    print(f"{len(new_properties)} new properties found:")
    for pid, prop in new_properties.items():
        print(f"- {prop['address']} | {prop['price']} | {prop['beds']} beds | {prop['images']} images")
else:
    print("No new properties found.")

# === SAVE SEEN AND RESULTS ===
with open("seen.json", "w", encoding="utf-8") as f:
    json.dump(dict(sorted(properties.items())), f, indent=2, ensure_ascii=False)

# === SAVE SEEN AND RESULTS ONLY IF THERE ARE RESULTS ===
if properties:
    with open("seen.json", "w", encoding="utf-8") as f:
        json.dump(dict(sorted(properties.items())), f, indent=2, ensure_ascii=False)
else:
    print("No properties found. Skipping seen.json update.")

# Save new results if any
if new_properties:
    # Save latest.json (used by the viewer site)
    with open("latest.json", "w", encoding="utf-8") as f:
        json.dump(new_properties, f, indent=2, ensure_ascii=False)

    # Save to timestamped archive file
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
    filename = f"results_{timestamp}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(new_properties, f, indent=2, ensure_ascii=False)
else:
    print("No new properties. Skipping latest.json and archive write.")

archive = []
for filename in sorted(glob.glob("results_*.json"), reverse=True):
    with open(filename, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            # Add timestamp to each property
            timestamp = filename.replace("results_", "").replace(".json", "")
            for item in data.values():
                item["timestamp"] = timestamp
                archive.append(item)
        except json.JSONDecodeError:
            print(f"Warning: Skipping invalid file {filename}")

# Save to archive.json
with open("archive.json", "w", encoding="utf-8") as f:
    json.dump(archive, f, indent=2, ensure_ascii=False)
