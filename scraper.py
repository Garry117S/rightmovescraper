import requests
from bs4 import BeautifulSoup
import json
import re


url = "https://www.rightmove.co.uk/property-for-sale/find.html?searchLocation=Jesmond%2C+Newcastle+Upon+Tyne&useLocationIdentifier=true&locationIdentifier=REGION%5E13653&radius=0.0&maxDaysSinceAdded=3&_includeSSTC=on"
headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

# Find the results section
results_section = soup.find("section", class_="ResultsList_resultsSection__MVSi7")
property_cards = results_section.find_all("div", class_="PropertyCard_propertyCardContainerWrapper__mcK1Z") if results_section else []

properties = []

for card in property_cards:
    data = {}
    
    # ID
    a_tag = card.find("a", class_="PropertyCard_propertyCardAnchor__s2ZaP")
    data["id"] = a_tag.get("id") if a_tag else "N/A"

    # Address
    address = card.find("address", class_="PropertyAddress_address__LYRPq")
    data["address"] = address.get_text(strip=True) if address else "N/A"

    # Price
    price = card.find("div", class_="PropertyPrice_price__VL65t")
    data["price"] = price.get_text(strip=True) if price else "N/A"

    # Price qualifier (e.g., "Offers Over")
    qualifier = card.find("div", class_="PropertyPrice_priceQualifier__U1Qu7")
    data["price_qualifier"] = qualifier.get_text(strip=True) if qualifier else "N/A"

    # Property type
    prop_type = card.find("span", class_="PropertyInformation_propertyType__u8e76")
    data["property_type"] = prop_type.get_text(strip=True) if prop_type else "N/A"

    # Bedrooms
    bedrooms = card.find("span", class_="PropertyInformation_bedroomsCount___2b5R")
    data["bedrooms"] = bedrooms.get_text(strip=True) if bedrooms else "N/A"

    # Bathrooms
    bathrooms = card.find("div", class_="PropertyInformation_bathContainer__ut8VY")
    if bathrooms:
        bath_count = bathrooms.find("span")
        data["bathrooms"] = bath_count.get_text(strip=True) if bath_count else "N/A"
    else:
        data["bathrooms"] = "N/A"

    # Description
    desc = card.find("p", class_="PropertyCardSummary_summary__oIv57")
    data["description"] = desc.get_text(strip=True) if desc else "N/A"


    # Find <img> with alt="camera icon"
    camera_img = card.find("img", alt="camera icon")
    image_count = "N/A"

    if camera_img and camera_img.has_attr("aria-label"):
        match = re.search(r"Property has (\d+) images", camera_img["aria-label"])
        if match:
            image_count = int(match.group(1))

    data["image_count"] = image_count

    # Link
    link = card.find("a", attrs={"aria-label": lambda x: x and "Link to property details page" in x})
    if link and link.get("href"):
        data["link"] = "https://www.rightmove.co.uk" + link["href"]
    else:
        data["link"] = "N/A"

    properties.append(data)

# Save to results.json
with open("results.json", "w", encoding="utf-8") as f:
    json.dump(properties, f, ensure_ascii=False, indent=2)
