import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, Column, Integer, String, Text, select
from sqlalchemy.orm import sessionmaker, declarative_base
from schemas import AppMetadata

# ---------------- ORM SETUP ----------------

Base = declarative_base()


class Server(Base):
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, nullable=False)
    name = Column(String)
    overview = Column(Text, nullable=True)
    detailed_description = Column(Text, nullable=True)


# Update this with your real DB credentials
DATABASE_URL = DATABASE_URL = "postgresql://michael@localhost:5432/hmfai-local"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def create_tables():
    Base.metadata.create_all(engine)


# ---------------- SCRAPING LOGIC ----------------

BASE_URL = "https://mcpservers.org"
OFFICIAL_URL = f"{BASE_URL}/official"


def scrape_server_list():
    response = requests.get(OFFICIAL_URL)
    soup = BeautifulSoup(response.text, "html.parser")

    cards = soup.find_all(
        "div",
        class_="rounded-xl border bg-card text-card-foreground shadow flex flex-col hover:shadow-lg transition-shadow duration-300 border-opacity-40",
    )

    server_links = []
    for card in cards:
        link = card.find("a", text="View Details")
        if link and "href" in link.attrs:
            full_url = f"{BASE_URL}{link['href']}"
            server_links.append(full_url)

    return server_links


def scrape_server_details(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    details = soup.find("div", class_="mt-8")
    if not details:
        return None

    name = details.find("h1").get_text(strip=True)
    overview = details.find("p").get_text(strip=True)
    description_div = details.find(
        "div", class_="border rounded-lg p-4 border-gray-200 markdown-body"
    )
    detailed_description = description_div.decode_contents() if description_div else ""

    return {
        "url": url,
        "name": name,
        "overview": overview,
        "detailed_description": detailed_description,
    }


# ---------------- DB LOGIC ----------------


def update_database():
    session = Session()
    existing_urls = {row[0] for row in session.execute(select(Server.url)).all()}

    new_links = [url for url in scrape_server_list() if url not in existing_urls]

    for url in new_links:
        print(f"New link found! Scraping: {url}")
        data = scrape_server_details(url)
        if data:
            server = Server(**data)
            session.add(server)

    session.commit()
    session.close()


def read_apps() -> list[AppMetadata]:
    session = Session()
    apps = session.query(Server).all()
    session.close()

    return apps
