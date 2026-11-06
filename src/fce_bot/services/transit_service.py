"""Transit query service for Ferrovia Circumetnea schedules and routes."""

import logging
from typing import List, Optional
from datetime import datetime, timedelta
from fce_bot.core.models import TransportType, FilterType, Stop, TripSegment, Itinerary
from fce_bot.data.db import get_db, normalize_stop_name

logger = logging.getLogger(__name__)


class TransitService:
    """Provides high-level timetable lookups, station queries, and route calculations."""

    def __init__(self, db_path=None):
        self.db_path = db_path

    def search_stops(
        self,
        query: str,
        transport_type: Optional[TransportType] = None,
        limit: int = 20
    ) -> List[Stop]:
        """Search stops matching a text query (prefix or fuzzy word match)."""
        norm_q = normalize_stop_name(query)
        if not norm_q:
            return []

        sql = """
            SELECT stop_id, stop_name, normalized_name, lat, lon, has_bus, has_train, has_metro
            FROM stops
            WHERE (normalized_name LIKE ? OR normalized_name LIKE ?)
        """
        params = [f"{norm_q}%", f"% {norm_q}%"]

        if transport_type == TransportType.BUS:
            sql += " AND has_bus = 1"
        elif transport_type == TransportType.TRENO:
            sql += " AND has_train = 1"
        elif transport_type == TransportType.METRO:
            sql += " AND has_metro = 1"

        sql += " ORDER BY stop_name LIMIT ?"
        params.append(limit)

        with get_db(self.db_path) as conn:
            cur = conn.cursor()
            rows = cur.execute(sql, params).fetchall()
            return [
                Stop(
                    stop_id=r["stop_id"],
                    stop_name=r["stop_name"],
                    normalized_name=r["normalized_name"],
                    lat=r["lat"],
                    lon=r["lon"],
                    has_bus=bool(r["has_bus"]),
                    has_train=bool(r["has_train"]),
                    has_metro=bool(r["has_metro"]),
                )
                for r in rows
            ]

    def get_stops_by_type(
        self,
        transport_type: TransportType = TransportType.QUALSIASI,
        limit: Optional[int] = None
    ) -> List[Stop]:
        """Get distinct stops available for a given transport type."""
        sql = """
            SELECT MIN(stop_id) as stop_id, stop_name, normalized_name, lat, lon,
                   MAX(has_bus) as has_bus, MAX(has_train) as has_train, MAX(has_metro) as has_metro
            FROM stops
            WHERE 1=1
        """
        if transport_type == TransportType.BUS:
            sql += " AND has_bus = 1"
        elif transport_type == TransportType.TRENO:
            sql += " AND has_train = 1"
        elif transport_type == TransportType.METRO:
            sql += " AND has_metro = 1"

        sql += " GROUP BY stop_name ORDER BY stop_name"
        params = ()
        if limit is not None and limit > 0:
            sql += " LIMIT ?"
            params = (limit,)

        with get_db(self.db_path) as conn:
            cur = conn.cursor()
            rows = cur.execute(sql, params).fetchall()
            return [
                Stop(
                    stop_id=r["stop_id"],
                    stop_name=r["stop_name"],
                    normalized_name=r["normalized_name"],
                    lat=r["lat"],
                    lon=r["lon"],
                    has_bus=bool(r["has_bus"]),
                    has_train=bool(r["has_train"]),
                    has_metro=bool(r["has_metro"]),
                )
                for r in rows
            ]

    def _resolve_stop_ids(
        self,
        name_or_query: str,
        transport_type: TransportType = TransportType.QUALSIASI
    ) -> List[str]:
        """Resolve a stop name query to a list of matching stop_ids for the transport mode."""
        norm = normalize_stop_name(name_or_query)
        sql = """
            SELECT stop_id FROM stops
            WHERE (normalized_name = ? OR normalized_name LIKE ? OR normalized_name LIKE ?)
        """
        params = [norm, f"{norm}%", f"%{norm}%"]

        if transport_type == TransportType.BUS:
            sql += " AND has_bus = 1"
        elif transport_type == TransportType.TRENO:
            sql += " AND has_train = 1"
        elif transport_type == TransportType.METRO:
            sql += " AND has_metro = 1"

        with get_db(self.db_path) as conn:
            cur = conn.cursor()
            rows = cur.execute(sql, params).fetchall()
            return [r["stop_id"] for r in rows]

    def find_trips(
        self,
        origin: str,
        destination: str,
        target_time: str = "08:00",
        transport_type: TransportType = TransportType.QUALSIASI,
        filter_type: FilterType = FilterType.DEPARTURE_AFTER,
        limit: int = 10
    ) -> List[Itinerary]:
        """Find direct or connecting itineraries between two stations."""
        # Standardize target_time to HH:MM format
        cleaned_time = target_time.replace(".", ":")
        parts = cleaned_time.split(":")
        if len(parts) == 1:
            cleaned_time = f"{int(parts[0]):02d}:00"
        elif len(parts) >= 2:
            cleaned_time = f"{int(parts[0]):02d}:{int(parts[1]):02d}"

        origin_ids = self._resolve_stop_ids(origin, transport_type=transport_type)
        dest_ids = self._resolve_stop_ids(destination, transport_type=transport_type)

        if not origin_ids or not dest_ids:
            logger.info("Could not resolve stops for %s: origin=%s (%d), dest=%s (%d)", transport_type.value, origin, len(origin_ids), destination, len(dest_ids))
            return []

        # 1. Direct search
        direct_itineraries = self._query_direct(
            origin_ids=origin_ids,
            dest_ids=dest_ids,
            target_time=cleaned_time,
            transport_type=transport_type,
            filter_type=filter_type,
            limit=limit
        )

        if direct_itineraries:
            return direct_itineraries

        # 2. Connection search (1 transfer) if no direct trips exist
        connecting_itineraries = self._query_connecting(
            origin_ids=origin_ids,
            dest_ids=dest_ids,
            target_time=cleaned_time,
            transport_type=transport_type,
            filter_type=filter_type,
            limit=limit
        )

        return connecting_itineraries

    def _query_direct(
        self,
        origin_ids: List[str],
        dest_ids: List[str],
        target_time: str,
        transport_type: TransportType,
        filter_type: FilterType,
        limit: int
    ) -> List[Itinerary]:
        """Query direct trips on the same vehicle/trip."""
        orig_placeholders = ",".join("?" for _ in origin_ids)
        dest_placeholders = ",".join("?" for _ in dest_ids)

        sql = f"""
            SELECT
                s1.stop_name as dep_stop,
                st1.departure_time as dep_time,
                s2.stop_name as arr_stop,
                st2.arrival_time as arr_time,
                r.transport_type,
                coalesce(nullif(r.route_short_name, 'NULL'), r.route_long_name, '') as route_name,
                coalesce(t.trip_headsign, '') as headsign
            FROM stop_times st1
            JOIN stop_times st2 ON st1.trip_id = st2.trip_id AND st2.stop_sequence > st1.stop_sequence
            JOIN stops s1 ON st1.stop_id = s1.stop_id
            JOIN stops s2 ON st2.stop_id = s2.stop_id
            JOIN trips t ON st1.trip_id = t.trip_id
            JOIN routes r ON t.route_id = r.route_id
            WHERE st1.stop_id IN ({orig_placeholders})
              AND st2.stop_id IN ({dest_placeholders})
        """
        params = list(origin_ids) + list(dest_ids)

        if transport_type != TransportType.QUALSIASI:
            sql += " AND r.transport_type = ?"
            params.append(transport_type.value)

        # Apply time filters
        if filter_type == FilterType.DEPARTURE_AFTER:
            sql += " AND st1.departure_time >= ?"
            params.append(target_time)
            sql += " ORDER BY st1.departure_time ASC"
        elif filter_type == FilterType.ARRIVAL_BEFORE:
            sql += " AND st2.arrival_time <= ?"
            params.append(target_time)
            sql += " ORDER BY st2.arrival_time DESC"
        elif filter_type == FilterType.DEPARTURE_NEAR:
            # Departure within current hour window (e.g. 08:00 to 08:59)
            hour_prefix = target_time.split(":")[0] + ":"
            sql += " AND st1.departure_time LIKE ?"
            params.append(f"{hour_prefix}%")
            sql += " ORDER BY st1.departure_time ASC"
        elif filter_type == FilterType.ARRIVAL_NEAR:
            hour_prefix = target_time.split(":")[0] + ":"
            sql += " AND st2.arrival_time LIKE ?"
            params.append(f"{hour_prefix}%")
            sql += " ORDER BY st2.arrival_time ASC"

        sql += " LIMIT ?"
        params.append(limit)

        with get_db(self.db_path) as conn:
            cur = conn.cursor()
            rows = cur.execute(sql, params).fetchall()

            # Deduplicate results with same departure/arrival times & route
            seen = set()
            itineraries: List[Itinerary] = []
            for r in rows:
                key = (r["dep_time"], r["arr_time"], r["route_name"])
                if key in seen:
                    continue
                seen.add(key)

                tt = TransportType(r["transport_type"]) if r["transport_type"] in [e.value for e in TransportType] else TransportType.QUALSIASI
                segment = TripSegment(
                    transport_type=tt,
                    route_name=r["route_name"],
                    headsign=r["headsign"],
                    departure_stop=r["dep_stop"],
                    departure_time=r["dep_time"],
                    arrival_stop=r["arr_stop"],
                    arrival_time=r["arr_time"]
                )
                itineraries.append(Itinerary(
                    departure_stop=r["dep_stop"],
                    departure_time=r["dep_time"],
                    arrival_stop=r["arr_stop"],
                    arrival_time=r["arr_time"],
                    is_direct=True,
                    segments=[segment]
                ))

            return itineraries

    def _query_connecting(
        self,
        origin_ids: List[str],
        dest_ids: List[str],
        target_time: str,
        transport_type: TransportType,
        filter_type: FilterType,
        limit: int
    ) -> List[Itinerary]:
        """Query 1-transfer connections (Leg 1 -> Interchange -> Leg 2)."""
        orig_placeholders = ",".join("?" for _ in origin_ids)
        dest_placeholders = ",".join("?" for _ in dest_ids)

        sql = f"""
            SELECT
                s_orig.stop_name as leg1_dep_stop,
                st1.departure_time as leg1_dep_time,
                s_transfer.stop_name as transfer_stop,
                st2.arrival_time as leg1_arr_time,
                r1.transport_type as leg1_type,
                coalesce(nullif(r1.route_short_name, 'NULL'), r1.route_long_name, '') as leg1_route,
                coalesce(t1.trip_headsign, '') as leg1_headsign,

                st3.departure_time as leg2_dep_time,
                s_dest.stop_name as leg2_arr_stop,
                st4.arrival_time as leg2_arr_time,
                r2.transport_type as leg2_type,
                coalesce(nullif(r2.route_short_name, 'NULL'), r2.route_long_name, '') as leg2_route,
                coalesce(t2.trip_headsign, '') as leg2_headsign
            FROM stop_times st1
            JOIN stop_times st2 ON st1.trip_id = st2.trip_id AND st2.stop_sequence > st1.stop_sequence
            JOIN trips t1 ON st1.trip_id = t1.trip_id
            JOIN routes r1 ON t1.route_id = r1.route_id
            JOIN stops s_orig ON st1.stop_id = s_orig.stop_id
            JOIN stops s_transfer ON st2.stop_id = s_transfer.stop_id

            -- Interchange matching
            JOIN stop_times st3 ON st2.stop_id = st3.stop_id
            JOIN stop_times st4 ON st3.trip_id = st4.trip_id AND st4.stop_sequence > st3.stop_sequence
            JOIN trips t2 ON st3.trip_id = t2.trip_id
            JOIN routes r2 ON t2.route_id = r2.route_id
            JOIN stops s_dest ON st4.stop_id = s_dest.stop_id

            WHERE st1.stop_id IN ({orig_placeholders})
              AND st4.stop_id IN ({dest_placeholders})
              AND st1.trip_id != st3.trip_id
              AND st3.departure_time >= st2.arrival_time
              AND st1.departure_time >= ?
        """
        params = list(origin_ids) + list(dest_ids) + [target_time]

        if transport_type != TransportType.QUALSIASI:
            sql += " AND (r1.transport_type = ? AND r2.transport_type = ?)"
            params.extend([transport_type.value, transport_type.value])

        sql += " ORDER BY st1.departure_time ASC, st4.arrival_time ASC LIMIT ?"
        params.append(limit * 2)

        with get_db(self.db_path) as conn:
            cur = conn.cursor()
            rows = cur.execute(sql, params).fetchall()

            seen = set()
            itineraries: List[Itinerary] = []
            for r in rows:
                key = (r["leg1_dep_time"], r["leg2_arr_time"], r["transfer_stop"])
                if key in seen:
                    continue
                seen.add(key)

                t1_type = TransportType(r["leg1_type"]) if r["leg1_type"] in [e.value for e in TransportType] else TransportType.QUALSIASI
                t2_type = TransportType(r["leg2_type"]) if r["leg2_type"] in [e.value for e in TransportType] else TransportType.QUALSIASI

                seg1 = TripSegment(
                    transport_type=t1_type,
                    route_name=r["leg1_route"],
                    headsign=r["leg1_headsign"],
                    departure_stop=r["leg1_dep_stop"],
                    departure_time=r["leg1_dep_time"],
                    arrival_stop=r["transfer_stop"],
                    arrival_time=r["leg1_arr_time"]
                )
                seg2 = TripSegment(
                    transport_type=t2_type,
                    route_name=r["leg2_route"],
                    headsign=r["leg2_headsign"],
                    departure_stop=r["transfer_stop"],
                    departure_time=r["leg2_dep_time"],
                    arrival_stop=r["leg2_arr_stop"],
                    arrival_time=r["leg2_arr_time"]
                )
                itineraries.append(Itinerary(
                    departure_stop=r["leg1_dep_stop"],
                    departure_time=r["leg1_dep_time"],
                    arrival_stop=r["leg2_arr_stop"],
                    arrival_time=r["leg2_arr_time"],
                    is_direct=False,
                    segments=[seg1, seg2]
                ))
                if len(itineraries) >= limit:
                    break

            return itineraries


transit_service = TransitService()
