"""Reference data for the simulated resort group and the way each source system names things.

Each source system uses its own codes and spellings for the same property or channel. That
mismatch is deliberate: resolving it is the integration work done later in dbt staging.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

SEED = 20261021

SIM_START = date(2024, 12, 1)  # warm-up month: fills the room calendar before reporting starts
REPORT_START = date(2025, 1, 1)  # first night audit and first business date with data
OPENING_DATE = date(2024, 12, 31)  # business date of the opening reservation export
HORIZON = date(2027, 12, 31)  # last simulated stay date; daily runs stay valid until mid-2027


@dataclass(frozen=True)
class Property:
    id: int
    code: str  # PMS hotel code
    name: str  # official name (finance)
    location: str
    rooms: int
    base_occ: float
    fnb_ratio: float
    spa_ratio: float
    rating: float
    ota_name: str  # how the channel manager names it
    review_name: str  # how the review platforms name it


PROPERTIES = [
    Property(1, "UBD", "Tropical Haven Ubud", "Ubud", 45, 0.74, 0.22, 0.12, 4.55,
             "TH Ubud", "Tropical Haven Resort - Ubud"),
    Property(2, "SMY", "Tropical Haven Seminyak", "Seminyak", 78, 0.78, 0.30, 0.06, 4.30,
             "TH Seminyak", "Tropical Haven Resort - Seminyak"),
    Property(3, "CGU", "Tropical Haven Canggu", "Canggu", 32, 0.70, 0.26, 0.04, 4.45,
             "Tropical Haven Canggu Surf", "Tropical Haven Resort - Canggu"),
    Property(4, "SNR", "Tropical Haven Sanur", "Sanur", 55, 0.66, 0.24, 0.05, 4.40,
             "TH Sanur Family", "Tropical Haven Resort - Sanur"),
    Property(5, "NSD", "Tropical Haven Nusa Dua", "Nusa Dua", 40, 0.72, 0.28, 0.14, 4.70,
             "TH Nusa Dua", "Tropical Haven Resort - Nusa Dua"),
]  # fmt: skip
PROP = {p.id: p for p in PROPERTIES}


@dataclass(frozen=True)
class RoomType:
    id: int
    property_id: int
    code: str  # PMS room type code
    name: str
    base_rate: int  # USD per night
    max_occupancy: int
    count: int


ROOM_TYPES = [
    RoomType(1, 1, "UBD-GV", "Garden Villa", 180, 2, 20),
    RoomType(2, 1, "UBD-PV", "Pool Villa", 280, 2, 15),
    RoomType(3, 1, "UBD-RFS", "Rice Field Suite", 380, 4, 10),
    RoomType(4, 2, "SMY-OVR", "Ocean View Room", 220, 2, 30),
    RoomType(5, 2, "SMY-BFS", "Beachfront Suite", 320, 4, 25),
    RoomType(6, 2, "SMY-PRV", "Presidential Villa", 420, 6, 23),
    RoomType(7, 3, "CGU-SB", "Surf Bungalow", 250, 2, 15),
    RoomType(8, 3, "CGU-WRS", "Wave Rider Suite", 350, 4, 12),
    RoomType(9, 3, "CGU-OL", "Ocean Loft", 450, 6, 5),
    RoomType(10, 4, "SNR-FR", "Family Room", 190, 4, 15),
    RoomType(11, 4, "SNR-GS", "Garden Suite", 290, 2, 15),
    RoomType(12, 4, "SNR-FV", "Family Villa", 390, 6, 5),
    RoomType(13, 5, "NSD-DLX", "Deluxe Room", 200, 2, 15),
    RoomType(14, 5, "NSD-PRS", "Premium Suite", 300, 2, 15),
    RoomType(15, 5, "NSD-RV", "Royal Villa", 400, 4, 10),
    RoomType(16, 4, "SNR-STD", "Standard Room", 210, 2, 20),
]
RT = {r.id: r for r in ROOM_TYPES}
assert all(sum(r.count for r in ROOM_TYPES if r.property_id == p.id) == p.rooms for p in PROPERTIES)


@dataclass(frozen=True)
class Channel:
    id: int
    code: str  # PMS source code
    name: str
    type: str
    commission_pct: float
    cancel_prob: float
    lead_mean: float  # days
    rate_factor: float
    ota_spellings: tuple[str, ...] = ()  # names used by the channel manager feed (OTA only)


CHANNELS = [
    Channel(1, "WEB", "Direct Website", "Direct", 0, 0.06, 45, 0.97),
    Channel(2, "BDC", "Booking.com", "OTA", 15, 0.19, 30, 1.00,
            ("Booking.com", "booking.com", "BOOKING.COM", "Booking.com ")),
    Channel(3, "EXP", "Expedia", "OTA", 18, 0.16, 32, 1.01, ("Expedia", "expedia.com", "Expedia Group")),
    Channel(4, "AGD", "Agoda", "OTA", 14, 0.17, 25, 0.98, ("Agoda", "agoda")),
    Channel(5, "GADS", "Google Ads", "Paid", 8, 0.10, 28, 1.00),
    Channel(6, "IG", "Instagram", "Social", 5, 0.09, 35, 0.99),
    Channel(7, "TA", "Travel Agent", "Agent", 12, 0.08, 60, 0.92),
    Channel(8, "ABNB", "Airbnb", "OTA", 20, 0.14, 40, 1.03, ("Airbnb", "airbnb")),
    Channel(9, "TRIP", "TripAdvisor", "OTA", 16, 0.12, 30, 1.00, ("TripAdvisor", "Tripadvisor", "tripadvisor")),
    Channel(10, "CORP", "Corporate Direct", "Direct", 0, 0.05, 20, 0.90),
]  # fmt: skip
CH = {c.id: c for c in CHANNELS}

# ISO 3166 alpha-2 codes (as stored by the PMS) and the names review platforms show
COUNTRIES = {
    "AU": "Australia", "ID": "Indonesia", "CN": "China", "KR": "South Korea", "JP": "Japan",
    "SG": "Singapore", "IN": "India", "GB": "United Kingdom", "DE": "Germany", "FR": "France",
    "NL": "Netherlands", "US": "United States", "RU": "Russia", "CA": "Canada", "IT": "Italy",
    "ES": "Spain", "SE": "Sweden",
}  # fmt: skip

BASE_MIX = {"AU": 24, "ID": 14, "CN": 9, "IN": 7, "GB": 6, "US": 5, "DE": 5, "KR": 5, "JP": 4,
            "SG": 5, "FR": 4, "NL": 3, "RU": 3, "CA": 2, "IT": 2, "ES": 1, "SE": 1}  # fmt: skip
MIX_TILT = {
    1: {"DE": 2, "FR": 2, "NL": 2, "GB": 1.5, "US": 1.5, "JP": 1.3},
    2: {"AU": 1.4, "ID": 1.2, "RU": 1.5, "IN": 1.3},
    3: {"AU": 1.9, "RU": 1.6, "SE": 2, "ES": 1.8, "CA": 1.5},
    4: {"ID": 1.8, "AU": 1.3, "SG": 1.6, "NL": 1.5},
    5: {"CN": 2.2, "KR": 2, "JP": 1.6, "IN": 1.8, "ID": 1.2},
}
SPEND_FACTOR = {"US": 1.12, "GB": 1.08, "DE": 1.05, "JP": 1.07, "CN": 1.10, "KR": 1.06,
                "AU": 1.0, "ID": 0.88, "IN": 0.97, "RU": 1.04, "SG": 1.05}  # fmt: skip

FIRST_NAMES = {
    "AU": ["Jack", "Olivia", "Liam", "Charlotte", "Noah", "Mia", "Lachlan", "Isla", "Cooper", "Ruby"],
    "ID": ["Putu", "Made", "Dewi", "Rizky", "Siti", "Andi", "Ayu", "Budi", "Fitri", "Agus"],
    "CN": ["Wei", "Li", "Jing", "Hao", "Yan", "Mei", "Jun", "Xin"],
    "KR": ["Min-jun", "Seo-yeon", "Ji-ho", "Ha-eun", "Do-yun", "Su-bin"],
    "JP": ["Haruto", "Yui", "Sota", "Hina", "Ren", "Aoi"],
    "SG": ["Ethan", "Chloe", "Ryan", "Sarah", "Marcus", "Grace"],
    "IN": ["Aarav", "Ananya", "Vihaan", "Diya", "Arjun", "Priya"],
    "RU": ["Ivan", "Anna", "Dmitri", "Elena", "Alexei", "Olga"],
}
LAST_NAMES = {
    "AU": ["Smith", "Jones", "Williams", "Brown", "Wilson", "Taylor", "Martin", "Thompson"],
    "ID": ["Wijaya", "Santoso", "Pratama", "Saputra", "Hidayat", "Wirawan", "Kusuma", "Suryadi"],
    "CN": ["Wang", "Li", "Zhang", "Liu", "Chen", "Yang"],
    "KR": ["Kim", "Lee", "Park", "Choi", "Jung"],
    "JP": ["Sato", "Suzuki", "Takahashi", "Tanaka", "Watanabe"],
    "SG": ["Tan", "Lim", "Lee", "Ng", "Wong"],
    "IN": ["Sharma", "Patel", "Singh", "Gupta", "Kumar"],
    "RU": ["Ivanov", "Smirnov", "Kuznetsov", "Popov", "Volkov"],
}
WESTERN_FIRST = ["James", "Emma", "Oliver", "Sophie", "Lucas", "Hannah", "Thomas", "Laura", "Daniel",
                 "Julia", "Max", "Clara", "Leon", "Elise", "Matteo", "Sofia", "Erik", "Freya",
                 "Pablo", "Lucia"]  # fmt: skip
WESTERN_LAST = ["Miller", "Davis", "Garcia", "Martinez", "Anderson", "Muller", "Schmidt", "Dubois",
                "Bernard", "de Vries", "Jansen", "Rossi", "Bianchi", "Johansson", "Larsson",
                "Fernandez", "Roberts", "Clark"]  # fmt: skip

# Planted business events (the insights the dashboard should surface)
SEMINYAK_RENOVATION = (date(2026, 2, 2), date(2026, 2, 28))  # 10 Beachfront Suites closed
SEMINYAK_CLEANLINESS_DIP = (date(2026, 6, 1), date(2026, 9, 30))
UBUD_ROOFTOP_OPENING = date(2026, 6, 1)  # F&B uplift
DIRECT_CAMPAIGN_START = date(2026, 1, 1)  # direct share ramps up over 120 days

REVIEW_TEXTS = {
    5: ["Absolutely perfect stay, the team went above and beyond.",
        "Stunning villa and flawless service. Will be back.",
        "Best resort experience we have had in Bali.",
        "Beautiful property, spotless rooms and amazing breakfast."],
    4: ["Great stay overall, friendly staff and lovely pool.",
        "Very good location and comfortable rooms.",
        "Enjoyed our holiday, good value for money.",
        "Nice resort, breakfast could have more variety."],
    3: ["Decent stay but the room needed better cleaning.",
        "Location is good, service was slow at check-in.",
        "Average experience for the price paid.",
        "Noise from renovation works affected our stay."],
    2: ["Room was not clean on arrival and staff were slow to respond.",
        "Disappointing for the price, maintenance issues in the bathroom."],
}  # fmt: skip
