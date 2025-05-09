import requests
from bs4 import BeautifulSoup

# URL of the main page
base_url = "https://mcpservers.org"
official_url = f"{base_url}/official"

# Send a GET request to the main page
response = requests.get(official_url)
soup = BeautifulSoup(response.text, "html.parser")

# Find all server cards
cards = soup.find_all(
    "div",
    class_="rounded-xl border bg-card text-card-foreground shadow flex flex-col hover:shadow-lg transition-shadow duration-300 border-opacity-40",
)  # Adjust the class name based on actual HTML

servers = []

for card in cards:
    link = card.find("a", text="View Details")["href"]
    full_link = f"{base_url}{link}"
    servers.append({"link": full_link})

for server in servers:
    detail_response = requests.get(server["link"])
    detail_soup = BeautifulSoup(detail_response.text, "html.parser")
    details_container = detail_soup.find("div", class_="mt-8")

    # Extract detailed description or other relevant information
    server_name = details_container.find("h1").get_text(strip=True)
    overview = details_container.find("p").get_text(strip=True)
    description_div = details_container.find(
        "div", class_="border rounded-lg p-4 border-gray-200 markdown-body"
    )

    # Get all inner HTML of the description div
    detailed_description = description_div.decode_contents() if description_div else ""

    server["name"] = server_name if server_name else None
    server["detailed_description"] = (
        detailed_description if detailed_description else None
    )
    server["overview"] = overview if overview else None

    print(f"Name: {server['name']}")
    print(f"Detailed Description: {server['overview']}\n")
