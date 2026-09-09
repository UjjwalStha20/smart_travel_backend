"""Offline Nepal knowledge base built from the project's seeded data.

Responsibilities:
- Build COMPACT factual context snippets for the LLM prompt.
- Provide instant, useful fallback answers when the LLM is slow/unavailable
  so the chatbot NEVER hangs or returns an empty bubble.

All answers stay strictly Nepal-focused (the dataset only contains Nepal).
"""

from typing import Dict, List, Optional

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.chat.intent import (
    ACCOMMODATION,
    BUDGET,
    CULTURE,
    DESTINATION,
    FOOD,
    ITINERARY,
    NATURE,
    NEPAL_GENERAL,
    OUT_OF_SCOPE,
    PERMITS,
    RELIGION,
    TRANSPORT,
    TREKKING,
    WEATHER,
    extract_destination_names,
    extract_months,
    season_for_month,
)
from app.models import (
    Accommodation,
    Attraction,
    Destination,
    DestinationThingToDo,
    EntryFee,
    FoodCost,
    Permit,
    TrekkingRoute,
)

_OUT_OF_SCOPE_REPLIES = [
    "I'm focused on travel within Nepal. I can suggest a Nepal destination with a similar experience if you'd like! 🇳🇵",
    "I specialize exclusively in Nepal travel. Tell me what you enjoy and I'll recommend a great spot inside Nepal instead.",
    "That destination is outside my Nepal-only scope. But I can point you to a similar adventure right here in Nepal — just ask!",
]

_OUT_OF_SCOPE_RESPONSES = {
    "thailand": "If you enjoyed Thailand's temples and beaches, Nepal offers Pashupatinath & Boudhanath for sacred sites and Rara Lake for serene water landscapes.",
    "india": "If you liked India's heritage, Nepal has Bhaktapur and Patan durbar squares plus Lumbini, the birthplace of Buddha.",
    "bhutan": "If Bhutan's mountain culture appeals to you, Nepal's Paro-like experiences include the Annapurna and Everest regions with teahouse treks and monastery visits.",
    "china": "If you're drawn by China's mountains and culture, Nepal's Everest Base Camp and Mustang region offer comparable high-altitude adventure with a different flavor.",
    "japan": "If you loved Japan's temples and nature, Nepal's Swayambhunath, Nagarkot and Pokhara combine heritage with mountain views.",
    "usa": "If you liked the US national parks, Nepal's Chitwan and Bardiya wildlife parks plus Sagarmatha and Langtang offer world-class park adventures.",
}

_SEASON_TREK_GUIDANCE = {
    "spring": (
        "Spring (March–May) is one of the best trekking seasons with warm days and rhododendron blooms. "
        "Popular: Poon Hill, Annapurna Base Camp, Manaslu and Everest region. High passes are usually clear."
    ),
    "summer": (
        "Summer/monsoon (June–August) brings heavy rain and muddy trails in most regions. "
        "Better choices during monsoon: Mustang and Upper Manang (rain shadow), plus the lower "
        "Annapurna foothills and Kathmandu Valley cultural sites. Everest visibility is often low."
    ),
    "autumn": (
        "Autumn (September–November) is the clearest and most popular trekking season with crisp skies. "
        "Poon Hill, ABC, Everest Base Camp, Annapurna Circuit and Langtang are all excellent choices."
    ),
    "winter": (
        "Winter (December–February) is cold but clear at lower altitudes. Great options: Poon Hill, "
        "Ghorepani and lower Langtang. High passes like Thorong La and Chola can be snowbound — "
        "check conditions with a local agency before going."
    ),
}


class NepalKnowledge:
    """Query helpers + compact factual builders over the Nepal dataset."""

    def __init__(self, session: Session):
        self.session = session
        self._destinations: Optional[List[Destination]] = None
        self._food: Optional[List[FoodCost]] = None
        self._accommodation: Optional[List[Accommodation]] = None

    # ------------------------------------------------------------------
    # Bulk-loaders (load once per request, reused across helpers)
    # ------------------------------------------------------------------

    def destinations(self, reload: bool = False) -> List[Destination]:
        if self._destinations is None or reload:
            stmt = (
                select(Destination)
                .options(
                    selectinload(Destination.address),
                    selectinload(Destination.attraction),
                    selectinload(Destination.trekking_routes),
                    selectinload(Destination.permits),
                    selectinload(Destination.things_to_do),
                )
                .order_by(Destination.name.asc())
            )
            self._destinations = self.session.exec(stmt).all()
        return self._destinations

    def food_costs(self) -> List[FoodCost]:
        if self._food is None:
            self._food = self.session.exec(select(FoodCost)).all()
        return self._food

    def accommodations(self) -> List[Accommodation]:
        if self._accommodation is None:
            self._accommodation = self.session.exec(
                select(Accommodation).order_by(Accommodation.name.asc())
            ).all()
        return self._accommodation

    def find_destination(self, name: str) -> Optional[Destination]:
        cased = name.strip().lower()
        for d in self.destinations():
            dn = d.name.lower()
            if dn == cased or dn.startswith(cased + " ") or dn in cased:
                return d
        for d in self.destinations():
            if cased in d.name.lower():
                return d
        return None

    # Aliases → database names for common trek abbreviations.
    _ALIASES = {"abc": "annapurna base camp", "ebc": "everest base camp"}

    def destinations_matching(self, names: List[str]) -> List[Destination]:
        """Best-effort name + locale (address.place/district/province) match."""
        if not names:
            return self.destinations()
        dests = self.destinations()
        out: List[Destination] = []

        def add(d):
            if d not in out:
                out.append(d)

        for n in names:
            n = n.strip().lower()
            if not n:
                continue
            n = self._ALIASES.get(n, n)
            # 1) Destination-name match (prefix wins over plain substring).
            for d in dests:
                dn = d.name.lower()
                if dn == n or dn.startswith(n + " ") or dn in n:
                    add(d)
            for d in dests:
                if n in d.name.lower():
                    add(d)
            # 2) Locale match through the address (city/district/province).
            for d in dests:
                a = d.address
                if not a:
                    continue
                hay = " ".join(x for x in (a.place, a.district, a.province) if x).lower()
                if n in hay or hay in n:
                    add(d)
        return out

    # ------------------------------------------------------------------
    # Compact context builders (used inside the LLM prompt)
    # ------------------------------------------------------------------

    def topic_context(self, intent: str, message: str, limit: int = 5) -> str:
        """Return a COMPACT factual snippet relevant to the user's intent.

        Kept deliberately terse (one line per item) because the whole block is
        injected into the LLM prompt where prompt-eval time dominates latency.
        """
        blocks: List[str] = []

        if intent in (DESTINATION, ITINERARY, NEPAL_GENERAL, NATURE):
            names = extract_destination_names(message)
            dests = self.destinations_matching(names)[:limit]
            if intent in (DESTINATION, ITINERARY) and names and not dests:
                dests = self.destinations()[:limit]
            context = self._compact_destinations(dests) if dests else ""
            if intent == NATURE and context:
                context = "Nature & scenery (destinations):\n" + context
            blocks.append(context)

        if intent == TREKKING:
            blocks.append(self._compact_trek_context(message, limit=limit))

        if intent == FOOD:
            blocks.append(self._compact_food())

        if intent == PERMITS:
            blocks.append(self._compact_permits())

        if intent == BUDGET:
            blocks.append(self._format_budget_hints())

        if intent == ACCOMMODATION:
            blocks.append(self._compact_accommodation())

        if intent == WEATHER:
            blocks.append(self._season_guidance(message))

        if intent in (CULTURE, RELIGION):
            names = extract_destination_names(message)
            dests = self.destinations_matching(names)[:limit]
            blocks.append(self._compact_cultural(dests))

        if intent == TRANSPORT:
            blocks.append(self._format_transport_hints())

        return "\n".join(b for b in blocks if b.strip())

    # ------------------------------------------------------------------
    # Fallback natural answers (no LLM needed)
    # ------------------------------------------------------------------

    def fallback_answer(self, intent: str, message: str) -> str:
        """Return a useful, well-structured answer from the dataset."""
        if intent == OUT_OF_SCOPE:
            return self._out_of_scope_reply(message)

        if intent in (DESTINATION, ITINERARY, NEPAL_GENERAL, NATURE, CULTURE, RELIGION):
            names = extract_destination_names(message)
            dests = self.destinations_matching(names)
            if not dests:
                dests = self.destinations()[:5]
            return self._format_destinations(dests, natural=True)

        if intent == TREKKING:
            return self._fallback_trek_answer(message)

        if intent == FOOD:
            return self._fallback_food_answer()

        if intent == PERMITS:
            return self._fallback_permits_answer()

        if intent == BUDGET:
            return self._fallback_budget_answer()

        if intent == ACCOMMODATION:
            return self._fallback_accommodation_answer()

        if intent == TRANSPORT:
            return self._fallback_transport_answer()

        if intent == WEATHER:
            return self._fallback_weather_answer(message)

        if intent == NEPAL_GENERAL:
            return self._nepal_general_answer()

        return (
            "I'm your Nepal travel assistant. I can help with destinations, trekking routes, "
            "permits, budgets, food, weather, transport and more. Ask me something like "
            "\u201cWhat are the things to do in Kathmandu?\u201d or \u201cWhich trek is good in "
            "October?\u201d 😊"
        )

    # ------------------------------------------------------------------
    # Formatters
    # ------------------------------------------------------------------

    def _format_destinations(self, dests: List[Destination], natural: bool = False) -> str:
        parts = []
        for d in dests[:8]:
            head = f"{d.name} — {d.description}"
            if natural:
                parts.append(f"{d.name}:\n{d.description}")
            else:
                parts.append(f"{d.name}:\n{d.description}")
            details = []
            if d.best_time:
                details.append("Best time: " + ", ".join(str(b) for b in d.best_time))
            if d.rating:
                details.append(f"Rating: {d.rating}/5")
            if d.permit_required:
                details.append("Permit required")
            attr = d.attraction
            if attr:
                if getattr(attr, "opening_hours", None):
                    details.append(f"Hours: {attr.opening_hours}")
                fees = self.session.exec(
                    select(EntryFee).where(EntryFee.attraction_id == attr.id)
                ).all()
                if fees:
                    prices = ", ".join(f"{f.category}: NPR {f.price}" for f in fees[:4])
                    details.append(f"Entry fee ({prices})")
            if details:
                parts.append("  - " + "\n  - ".join(details))
        return "\n\n".join(parts)

    def _treks_for_message(self, message: str, limit: int = 8) -> List[TrekkingRoute]:
        routes = []
        seen = set()
        months = extract_months(message)
        season = season_for_month(months[0]) if months else ""
        names = extract_destination_names(message)

        pool = self.destinations_matching(names) if names else self.destinations()
        if not names:
            pool = [d for d in pool if d.category == "trek"] or pool

        for dest in pool:
            for r in dest.trekking_routes or []:
                score = self._trek_season_score(r, dest, season)
                routes.append((score, r, dest))

        routes.sort(key=lambda x: x[0], reverse=True)
        out = []
        for score, r, dest in routes:
            key = r.id
            if key in seen:
                continue
            seen.add(key)
            out.append(r)
            if len(out) >= limit:
                break
        return out

    @staticmethod
    def _trek_season_score(route: TrekkingRoute, dest: Destination, season: str) -> float:
        score = 0.0
        if season and dest.best_time:
            seasons = [str(b).lower() for b in dest.best_time]
            if season in seasons or any(s in season or season in s for s in seasons):
                score += 3.0
            elif season == "summer" and any("rain shadow" in s for s in seasons):
                score += 2.0
        difficulty = (getattr(route, "difficulty", "") or "").lower()
        if difficulty == "easy":
            score += 1.0
        elif difficulty == "moderate":
            score += 0.6
        return score

    def _format_treks(self, message: str, limit: int = 8) -> str:
        routes = self._treks_for_message(message, limit)
        if not routes:
            return ""
        parts = []
        dest_by_route = {r.id: r for r in routes}
        for r in routes:
            dest = self._dest_for_route(r)
            line = f"{r.route_name} ({dest.name if dest else ''})"
            bits = [line]
            if getattr(r, "difficulty", None):
                bits.append(f"difficulty {r.difficulty}")
            if getattr(r, "recommended_days", None):
                bits.append(f"{r.recommended_days} days")
            if getattr(r, "total_distance_km", None):
                bits.append(f"{r.total_distance_km} km")
            if getattr(r, "max_altitude", None):
                bits.append(f"max {r.max_altitude} m")
            if getattr(r, "description", None):
                bits.append(r.description)
            parts.append(" - ".join(bits))
        return "\n".join(parts)

    def _dest_for_route(self, route: TrekkingRoute) -> Optional[Destination]:
        for d in self.destinations():
            if route in (d.trekking_routes or []):
                return d
        return None

    def _format_food(self) -> str:
        foods = self.food_costs()[:10]
        if not foods:
            return ""
        lines = [f"{f.name} ({f.category}): budget NPR {f.budget_price}, standard NPR {f.standard_price}, luxury NPR {f.luxury_price}" for f in foods]
        return "Nepali food prices (NPR):\n" + "\n".join(lines)

    def _format_permits(self) -> str:
        lines = []
        for dest in self.destinations():
            for p in dest.permits or []:
                lines.append(f"{p.permit_type} ({p.category}): NPR {p.price} — {dest.name}")
        if not lines:
            return ""
        return "Known permits (NPR):\n" + "\n".join(lines[:10])

    def _format_budget_hints(self) -> str:
        return (
            "Budget hints for Nepal:\n"
            "• Budget teahouse/lodge rooms: roughly NPR 800–1,500/night in trekking areas.\n"
            "• Dal Bhat set meal: NPR 500+ (often all-you-can-eat on treks).\n"
            "• Local bus: NPR 500–1,500 between major cities; domestic flights from ~NPR 8,000–15,000.\n"
            "• Temple/durbar square entry fees: typically NPR 500–1,500 for foreigners."
        )

    def _format_accommodation(self) -> str:
        acc = self.accommodations()[:8]
        if not acc:
            return ""
        lines = []
        for a in acc:
            prices = []
            if getattr(a, "budget_price", None):
                prices.append(f"budget NPR {a.budget_price}")
            if getattr(a, "standard_price", None):
                prices.append(f"standard NPR {a.standard_price}")
            if getattr(a, "luxury_price", None):
                prices.append(f"luxury NPR {a.luxury_price}")
            tail = f" ({', '.join(prices)})" if prices else ""
            loc = f" ({a.location})" if a.location else ""
            lines.append(f"{a.name}{loc} — {a.description or ''}{tail}".strip())
        return "\n".join(lines)

    def _season_guidance(self, message: str) -> str:
        months = extract_months(message)
        season = season_for_month(months[0]) if months else ""
        if season and season in _SEASON_TREK_GUIDANCE:
            return _SEASON_TREK_GUIDANCE[season]
        return (
            "Nepal seasons (general): spring (Mar–May) great trails & rhododendrons; "
            "summer/monsoon (Jun–Aug) wet, rain-shadow areas like Mustang are better; "
            "autumn (Sep–Nov) clearest skies, peak season; winter (Dec–Feb) cold but "
            "clear at lower altitudes."
        )

    def _format_cultural(self, dests: List[Destination]) -> str:
        if not dests:
            dests = self.destinations()[:6]
        parts = []
        for d in dests:
            bits = [f"{d.name}"]
            if d.best_time:
                bits.append("Best: " + ", ".join(str(b) for b in d.best_time))
            parts.append(" - ".join(bits))
        return "\n".join(parts)

    def _format_transport_hints(self) -> str:
        return (
            "Transport notes for Nepal:\n"
            "• Tourist buses connect Kathmandu–Pokhara (~6–7 hrs) and Kathmandu–Chitwan (~5 hrs).\n"
            "• Domestic flights: Kathmandu–Pokhara (~25 min), Kathmandu–Lukla for Everest.\n"
            "• Mountain flights (Lukla/Jomsom) can be cancelled for weather — keep a buffer day.\n"
            "• Local buses are cheap but slower and fuller than tourist coaches."
        )

    # ------------------------------------------------------------------
    # Compact context formatters (single-line; low prompt-eval cost)
    # ------------------------------------------------------------------

    def _compact_destinations(self, dests: List[Destination]) -> str:
        lines = []
        for d in dests[:5]:
            bits = [f"{d.name} ({self._cat(d)})"]
            if d.best_time:
                bits.append("best " + ", ".join(str(b)[:3] for b in d.best_time))
            if d.rating:
                bits.append(f"rating {d.rating}")
            if d.permit_required:
                bits.append("permit needed")
            if d.description:
                bits.append(d.description[:110])
            lines.append("• " + " | ".join(bits))
        return "\n".join(lines)

    @staticmethod
    def _cat(dest: Destination) -> str:
        return dest.category.value if hasattr(dest.category, "value") else str(dest.category)

    def _compact_trek_context(self, message: str, limit: int = 5) -> str:
        months = extract_months(message)
        season = season_for_month(months[0]) if months else ""
        lines = []
        guide = _SEASON_TREK_GUIDANCE.get(season)
        if guide:
            lines.append(guide[:220])
        routes = self._treks_for_message(message, limit)
        for r in routes:
            dest = self._dest_for_route(r)
            bits = [f"{r.route_name} ({dest.name if dest else ''})"]
            if getattr(r, "difficulty", None):
                bits.append(str(r.difficulty))
            if getattr(r, "recommended_days", None):
                bits.append(f"{r.recommended_days}d")
            if getattr(r, "max_altitude", None):
                bits.append(f"max {r.max_altitude}m")
            if getattr(r, "description", None):
                bits.append(str(r.description)[:90])
            lines.append("• " + " | ".join(bits))
        return "\n".join(lines)

    def _compact_food(self) -> str:
        foods = self.food_costs()[:8]
        if not foods:
            return ""
        lines = ["Nepali food prices (NPR):"]
        for f in foods:
            lines.append(
                f"• {f.name} ({f.category}): {f.budget_price}/{f.standard_price}/{f.luxury_price}"
            )
        return "\n".join(lines)

    def _compact_permits(self) -> str:
        lines = []
        seen = set()
        for dest in self.destinations():
            for p in dest.permits or []:
                key = (p.permit_type, p.category)
                if key in seen:
                    continue
                seen.add(key)
                lines.append(f"• {p.permit_type} ({p.category}) NPR {p.price} — {dest.name}")
                if len(lines) >= 6:
                    break
            if len(lines) >= 6:
                break
        return "\n".join(lines)

    def _compact_accommodation(self) -> str:
        acc = self.accommodations()[:6]
        if not acc:
            return ""
        lines = []
        for a in acc:
            prices = []
            for tier, key in (("b", "budget_price"), ("std", "standard_price"), ("lx", "luxury_price")):
                v = getattr(a, key, None)
                if v:
                    prices.append(f"{tier} {v}")
            bits = [a.name or ""]
            if a.location:
                bits.append(a.location)
            if prices:
                bits.append("NPR " + ", ".join(prices))
            lines.append("• " + " | ".join(bits))
        return "\n".join(lines)

    def _compact_cultural(self, dests: List[Destination]) -> str:
        if not dests:
            dests = self.destinations()[:5]
        lines = []
        for d in dests[:5]:
            bits = [f"{d.name} ({self._cat(d)})"]
            if d.best_time:
                bits.append("best " + ", ".join(str(b)[:3] for b in d.best_time))
            attr = d.attraction
            if attr and getattr(attr, "opening_hours", None):
                bits.append(f"hours {attr.opening_hours[:60]}")
            lines.append("• " + " | ".join(bits))
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Natural fallback answers
    # ------------------------------------------------------------------

    def _out_of_scope_reply(self, message: str) -> str:
        lower = message.lower()
        for name, reply in _OUT_OF_SCOPE_RESPONSES.items():
            if name in lower:
                return reply
        return _OUT_OF_SCOPE_REPLIES[0]

    def _fallback_trek_answer(self, message: str) -> str:
        routes = self._treks_for_message(message, limit=5)
        months = extract_months(message)
        season = season_for_month(months[0]) if months else ""
        guide = _SEASON_TREK_GUIDANCE.get(season, "")
        lines = []
        if guide:
            lines.append(guide)
            lines.append("")
        if routes:
            lines.append("Trek routes that fit best based on our data:")
            for i, r in enumerate(routes, 1):
                dest = self._dest_for_route(r)
                line = f"{i}. {r.route_name}"
                if dest:
                    line += f" ({dest.name})"
                if r.difficulty:
                    line += f" — {r.difficulty}"
                if r.recommended_days:
                    line += f", {r.recommended_days} days"
                if r.max_altitude:
                    line += f", max {r.max_altitude}m"
                if r.description:
                    line += f". {r.description}"
                lines.append(line)
        else:
            lines.append("I don't have detailed trek route data for that right now, but I can suggest Poon Hill (easy) or Annapurna Base Camp (moderate) as well-known starts. Always check current trail conditions with a local agency.")
        lines.append(
            "Note: these are general seasonal recommendations from our dataset, not live trail conditions."
        )
        return "\n".join(lines)

    def _fallback_food_answer(self) -> str:
        foods = self.food_costs()[:8]
        lines = ["Must-try food in Nepal 🇳🇵:"]
        if foods:
            for f in foods:
                price = f.budget_price or f.standard_price or ""
                price_txt = f" (~NPR {price})" if price else ""
                lines.append(f"• {f.name}{price_txt} — classic and easy to find.")
        lines.append("• Drink only boiled or purified water. Tell your host about any dietary restrictions (veg/vegan is widely understood).")
        return "\n".join(lines)

    def _fallback_permits_answer(self) -> str:
        lines = ["Common permits you may need in Nepal:"]
        seen = set()
        for dest in self.destinations():
            for p in dest.permits or []:
                key = (p.permit_type, p.category)
                if key in seen:
                    continue
                seen.add(key)
                lines.append(f"• {p.permit_type} card ({p.category}): ~NPR {p.price} ({dest.name}).")
                if len(lines) >= 7:
                    break
        return "\n".join(lines) + "\n\nAlso remember the Nepal tourist visa on arrival. Rules can change — confirm current fees before you go."

    def _fallback_budget_answer(self) -> str:
        return (
            "A realistic Nepal budget (per person, not including international flights):\n"
            "• Budget: ~NPR 2,500–4,000/day (local buses, simple teahouses, Dal Bhat).\n"
            "• Mid-range: ~NPR 6,000–12,000/day (private transport, nice hotels, guided activities).\n"
            "• Comfort/luxury: NPR 15,000+/day (boutique lodges, domestic flights, private guides).\n\n"
            "Temples/durbar squares cost roughly NPR 500–1,500 entry, trekking permits add "
            "TIMS + park fees (~NPR 2,000–5,000)."
        )

    def _fallback_accommodation_answer(self) -> str:
        acc = self.accommodations()[:8]
        lines = ["Accommodation in Nepal (based on our data):"]
        if acc:
            for a in acc:
                name = getattr(a, "name", "")
                desc = getattr(a, "description", "")
                loc = f" in {getattr(a, 'location', '')}" if getattr(a, "location", "") else ""
                lines.append(f"• {name}{loc} — {desc}".strip())
        else:
            lines.append("• Teahouses and budget lodges from ~NPR 800–1,500/night in trekking areas.")
            lines.append("• Hotels in Kathmandu/Pokhara range from budget guesthouses to 5-star resorts.")
        return "\n".join(lines[:8])

    def _fallback_transport_answer(self) -> str:
        return self._format_transport_hints()

    def _fallback_weather_answer(self, message: str) -> str:
        return self._season_guidance(message)