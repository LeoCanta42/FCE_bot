"""Domain models and data schemas for FCE Bot."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class TransportType(str, Enum):
    BUS = "BUS"
    TRENO = "TRENO"       # Ferrovia Circumetnea superficie (littorina)
    METRO = "METRO"       # Metropolitana di Catania
    QUALSIASI = "QUALSIASI"

    @classmethod
    def from_str(cls, val: str) -> "TransportType":
        cleaned = val.strip().upper()
        if "METRO" in cleaned:
            return cls.METRO
        if "BUS" in cleaned or "AUTOBUS" in cleaned or "AUTOLINEE" in cleaned:
            return cls.BUS
        if "TRENO" in cleaned or "LITTORINA" in cleaned or cleaned in ("TR", "TR."):
            return cls.TRENO
        return cls.QUALSIASI


class FilterType(str, Enum):
    DEPARTURE_NEAR = "near_partenza"    # Departures within specified hour
    ARRIVAL_NEAR = "near_arrivo"        # Arrivals within specified hour
    DEPARTURE_AFTER = "near_partenza2"  # Departures from specified hour onwards
    ARRIVAL_BEFORE = "near_arrivo2"     # Arrivals before or at specified hour


@dataclass
class Stop:
    stop_id: str
    stop_name: str
    normalized_name: str
    lat: float = 0.0
    lon: float = 0.0
    has_bus: bool = False
    has_train: bool = False
    has_metro: bool = False

    def to_dict(self) -> dict:
        return {
            "stop_id": self.stop_id,
            "stop_name": self.stop_name,
            "normalized_name": self.normalized_name,
            "lat": self.lat,
            "lon": self.lon,
            "has_bus": self.has_bus,
            "has_train": self.has_train,
            "has_metro": self.has_metro,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Stop":
        return cls(
            stop_id=data["stop_id"],
            stop_name=data["stop_name"],
            normalized_name=data["normalized_name"],
            lat=data.get("lat", 0.0),
            lon=data.get("lon", 0.0),
            has_bus=data.get("has_bus", False),
            has_train=data.get("has_train", False),
            has_metro=data.get("has_metro", False),
        )


@dataclass
class TripSegment:
    transport_type: TransportType
    route_name: str
    headsign: str
    departure_stop: str
    departure_time: str   # HH:MM format
    arrival_stop: str
    arrival_time: str     # HH:MM format

    @property
    def duration_minutes(self) -> int:
        try:
            t1 = datetime.strptime(self.departure_time, "%H:%M")
            t2 = datetime.strptime(self.arrival_time, "%H:%M")
            diff = (t2 - t1).total_seconds() / 60
            return int(diff) if diff >= 0 else int(diff + 1440)
        except Exception:
            return 0

    def to_dict(self) -> dict:
        return {
            "transport_type": self.transport_type.value,
            "route_name": self.route_name,
            "headsign": self.headsign,
            "departure_stop": self.departure_stop,
            "departure_time": self.departure_time,
            "arrival_stop": self.arrival_stop,
            "arrival_time": self.arrival_time
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TripSegment":
        return cls(
            transport_type=TransportType(data["transport_type"]),
            route_name=data["route_name"],
            headsign=data.get("headsign", ""),
            departure_stop=data["departure_stop"],
            departure_time=data["departure_time"],
            arrival_stop=data["arrival_stop"],
            arrival_time=data["arrival_time"]
        )


@dataclass
class Itinerary:
    departure_stop: str
    departure_time: str
    arrival_stop: str
    arrival_time: str
    is_direct: bool
    segments: List[TripSegment] = field(default_factory=list)

    @property
    def duration_minutes(self) -> int:
        try:
            t1 = datetime.strptime(self.departure_time, "%H:%M")
            t2 = datetime.strptime(self.arrival_time, "%H:%M")
            diff = (t2 - t1).total_seconds() / 60
            return int(diff) if diff >= 0 else int(diff + 1440)
        except Exception:
            return 0

    def to_dict(self) -> dict:
        return {
            "departure_stop": self.departure_stop,
            "departure_time": self.departure_time,
            "arrival_stop": self.arrival_stop,
            "arrival_time": self.arrival_time,
            "is_direct": self.is_direct,
            "segments": [s.to_dict() for s in self.segments]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Itinerary":
        return cls(
            departure_stop=data["departure_stop"],
            departure_time=data["departure_time"],
            arrival_stop=data["arrival_stop"],
            arrival_time=data["arrival_time"],
            is_direct=data["is_direct"],
            segments=[TripSegment.from_dict(s) for s in data.get("segments", [])]
        )

    def format_telegram(self) -> str:
        """Render itinerary nicely formatted for Telegram Markdown."""
        icon_map = {
            TransportType.BUS: "🚌",
            TransportType.TRENO: "🚆",
            TransportType.METRO: "🚇",
            TransportType.QUALSIASI: "🚍"
        }
        if self.is_direct:
            seg = self.segments[0]
            icon = icon_map.get(seg.transport_type, "🚍")
            return (
                f"{icon} *{seg.transport_type.value}* ({seg.route_name})\n"
                f"  📍 *Partenza:* `{seg.departure_time}` - {seg.departure_stop}\n"
                f"  🏁 *Arrivo:* `{seg.arrival_time}` - {seg.arrival_stop}\n"
                f"  ⏱ Durata: ~{self.duration_minutes} min | Verso: _{seg.headsign}_\n"
            )
        else:
            lines = ["🔀 *Soluzione con cambio*:\n"]
            for idx, seg in enumerate(self.segments, 1):
                icon = icon_map.get(seg.transport_type, "🚍")
                lines.append(
                    f"*{idx}. {icon} {seg.transport_type.value} ({seg.route_name})*\n"
                    f"   Salita: `{seg.departure_time}` - {seg.departure_stop}\n"
                    f"   Discesa: `{seg.arrival_time}` - {seg.arrival_stop}\n"
                )
            lines.append(f"⏱ *Durata totale stimata:* ~{self.duration_minutes} min\n")
            return "".join(lines)

    def format_clean(self) -> str:
        """Render itinerary as clean plain text without Markdown asterisks or brackets."""
        icon_map = {
            TransportType.BUS: "🚌",
            TransportType.TRENO: "🚆",
            TransportType.METRO: "🚇",
            TransportType.QUALSIASI: "🚍"
        }
        if self.is_direct:
            seg = self.segments[0]
            icon = icon_map.get(seg.transport_type, "🚍")
            headsign_part = f" (Direzione {seg.headsign})" if seg.headsign else ""
            return (
                f"{icon} {seg.transport_type.value}: partenza ore {seg.departure_time} da {seg.departure_stop}, "
                f"arrivo ore {seg.arrival_time} a {seg.arrival_stop} (~{self.duration_minutes} min){headsign_part}"
            )
        else:
            parts = []
            for seg in self.segments:
                icon = icon_map.get(seg.transport_type, "🚍")
                parts.append(f"{icon} {seg.transport_type.value} ({seg.departure_stop} ore {seg.departure_time} -> {seg.arrival_stop} ore {seg.arrival_time})")
            return f"🔀 Cambio: {' con '.join(parts)} (durata complessiva ~{self.duration_minutes} min)"


class NewsItem(BaseModel):
    title: str
    link: str
    published_date: Optional[str] = None
    summary: Optional[str] = None
    guid: Optional[str] = None

    def format_telegram(self) -> str:
        text = f"📢 *{self.title.strip()}*\n"
        if self.published_date:
            text += f"📅 _{self.published_date}_\n"
        if self.summary:
            clean_summary = self.summary.strip()
            if len(clean_summary) > 300:
                clean_summary = clean_summary[:297] + "..."
            text += f"\n{clean_summary}\n"
        text += f"\n🔗 [Leggi sul sito FCE]({self.link})"
        return text


class DocumentsInfo(BaseModel):
    metro_url: str
    train_url: str
    bus_url: str
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AIQueryRequest(BaseModel):
    question: str
    user_id: Optional[str] = None


class AIQueryResponse(BaseModel):
    answer: str
    origin: Optional[str] = None
    destination: Optional[str] = None
    time: Optional[str] = None
    itineraries_count: int = 0
    itineraries: List[dict] = Field(default_factory=list)
