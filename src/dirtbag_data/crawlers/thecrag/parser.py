"""Parsers de The Crag (spec Phase 5) — deterministas, sin LLM.

Selectores confirmados contra fixtures reales (tests/fixtures/thecrag/):

Página de área
- filas:  <tr title=" N ascents - path"> … <td class="g">5.9</td>
           <td class="rt"><span class="route"><a href="…/route/<id>">★… nombre</a>
           <td class="s sport"></td> … </tr>
- hijos:  <div class="area" data-nid="<id>"> <div class="name"><a href="…/area/<id>">
           <span class="primary-node-name">Nombre</span> … <div class="routes">27</div>

Página de ruta
- nombre: <span itemprop="name">Alien Tufa</span> dentro de h1
- grado:  <span class="grade gb3" title="Set using US grade config">5.11c</span>
- largo:  <strong>Length:</strong> 28m
- coords: <meta property="place:location:latitude" content="25.39458…">
- path:   spans.crumb__long del breadcrumb (último crumb = la ruta)
- disc.:  title="Filter to 1 sport routes" o <title>… 28m Sport climb in …>

El path del <tr title> viene con entidades dobles (&amp;nbsp; / &amp;#8250;):
hay que desescapar DOS veces y partir por el separador U+203A.
"""

from __future__ import annotations

import html as H
import re
from urllib.parse import urljoin

from dirtbag_data.models.records import AreaPage, ChildArea, ParsedRoute, RouteLink
from dirtbag_data.normalization.grades import GradeSystem, detect_system
from dirtbag_data.normalization.lengths import parse_length

_TR_RE = re.compile(r'<tr title="([^"]*)">(.*?)</tr>', re.S)
_TD_G_RE = re.compile(r'<td class="g">([^<]*)</td>')
_TD_RT_RE = re.compile(
    r'<td class="rt"><span class="route"><a href="([^"]+)">(.*?)</a>', re.S
)
_TD_S_RE = re.compile(r'<td class="s([^"]*)"')

_AREA_START = '<div class="area" data-nid="'
_AREA_NID_RE = re.compile(r'<div class="area" data-nid="(\d+)"')
_AREA_NAME_RE = re.compile(
    r'<div class="name"><a href="([^"]+)"><span class="primary-node-name">([^<]+)</span>'
)
_AREA_ROUTES_RE = re.compile(r'<div class="routes">(\d+)</div>')

_NAME_RE = re.compile(r'<span itemprop="name">([^<]+)</span>')
_TITLE_RE = re.compile(r"<title>([^<]+)</title>")
_GRADE_RE = re.compile(
    r'<span class="grade[^"]*"(?: title="Set using ([A-Za-z ]+) grade config")?>([^<]+)</span>'
)
_LENGTH_RE = re.compile(r"<strong>Length:</strong>\s*([0-9.,]+\s*[A-Za-z']+)")
_LAT_RE = re.compile(r'place:location:latitude" content="([^"]+)"')
_LNG_RE = re.compile(r'place:location:longitude" content="([^"]+)"')
_CRUMB_RE = re.compile(r'<span[^>]*crumb__long[^>]*>([^<]+)</span>')
_DISC_FILTER_RE = re.compile(r'title="Filter to \d+ (\w+) routes"')
_DISC_TITLE_RE = re.compile(r",\s*\d+\s*(?:m|ft)\s+(\w+)\s+climb in", re.I)
_ROUTE_ID_RE = re.compile(r"/route/(\d+)")

_US_GRADE_HINTS = {
    "US": GradeSystem.YDS,
    "FRENCH": GradeSystem.FRENCH,
    "FONT": GradeSystem.FONT,
    "UIAA": GradeSystem.UIAA,
    "V": GradeSystem.V_SCALE,
}

_BAND_CELLS = {"gb1", "gb2", "gb3", "gb4"}


def _decode_title(raw: str) -> str:
    """Desescapa dos veces (&amp;nbsp; → espacio, &amp;#8250; → U+203A)."""
    text = H.unescape(H.unescape(raw))
    return text.replace("\xa0", " ").strip()


_STAR_SPAN_RE = re.compile(r'<span class="star">[^<]*</span>')


def _clean_text(fragment: str) -> str:
    """Quita estrellas y etiquetas internas, normaliza espacios."""
    without_stars = _STAR_SPAN_RE.sub("", fragment)
    without_tags = re.sub(r"<[^>]+>", " ", without_stars)
    return " ".join(H.unescape(without_tags).split())


def parse_area_page(html: str, url: str) -> AreaPage:
    """Extrae rutas destacadas y sub-áreas de una página de área."""
    routes: list[RouteLink] = []
    for title_raw, row_html in _TR_RE.findall(html):
        grade_m = _TD_G_RE.search(row_html)
        link_m = _TD_RT_RE.search(row_html)
        if not grade_m or not link_m:
            continue
        href, inner = link_m.groups()
        route_id_m = _ROUTE_ID_RE.search(href)
        if not route_id_m:
            continue
        grade_value = grade_m.group(1).strip()
        if not grade_value:
            continue
        title = _decode_title(title_raw)
        # " 14 ascents - El Salto > Cañon ..." -> path de nombres de area
        area_path: list[str] = []
        if " - " in title:
            path_part = title.split(" - ", 1)[1]
            area_path = [seg.strip() for seg in path_part.split("›") if seg.strip()]  # noqa: RUF001
        disc_m = _TD_S_RE.search(row_html)
        discipline: str | None = None
        if disc_m:
            classes = disc_m.group(1).split()
            classes = [c for c in classes if c != "s" and c not in _BAND_CELLS]
            discipline = classes[0] if classes else None
        name = _clean_text(inner)
        if not name:
            continue
        system = detect_system(grade_value)
        routes.append(
            RouteLink(
                source_entity_id=route_id_m.group(1),
                url=urljoin(url, href),
                name=name,
                grade_value=grade_value,
                grade_system=system,
                discipline=discipline,
                area_path=area_path,
            )
        )

    children: list[ChildArea] = []
    parts = html.split(_AREA_START)
    for chunk in parts[1:]:
        nid_m = _AREA_NID_RE.match(_AREA_START + chunk)
        if not nid_m:
            continue
        head = chunk[:4000]
        name_m = _AREA_NAME_RE.search(head)
        if not name_m:
            continue
        href, name = name_m.groups()
        count_m = _AREA_ROUTES_RE.search(head)
        route_count = int(count_m.group(1)) if count_m else None
        children.append(
            ChildArea(
                source_entity_id=nid_m.group(1),
                url=urljoin(url, href),
                name=H.unescape(name).strip(),
                route_count=route_count,
            )
        )

    return AreaPage(url=url, routes=routes, child_areas=children)


def parse_route_page(html: str, url: str) -> ParsedRoute:
    """Extrae la ficha completa de una página de ruta."""
    route_id_m = _ROUTE_ID_RE.search(url)
    if not route_id_m:
        raise ValueError(f"no /route/<id> in URL: {url}")

    name_m = _NAME_RE.search(html)
    if name_m:
        name = H.unescape(name_m.group(1)).strip()
    else:
        title_m = _TITLE_RE.search(html)
        if not title_m:
            raise ValueError(f"no route name found: {url}")
        # "5.11c ★★★Alien Tufa, 28m Sport climb in El Salto | theCrag"
        title = H.unescape(title_m.group(1)).replace("| theCrag", "").strip()
        stripped = re.sub(r"^(?:[\w.]+\s+)?(?:★+\s*)?", "", title)
        name = stripped.split(",", 1)[0].strip()

    grade_m = _GRADE_RE.search(html)
    if not grade_m:
        raise ValueError(f"no grade found: {url}")
    hint, grade_raw = grade_m.groups()
    grade_value = grade_raw.strip()
    if hint:
        system = _US_GRADE_HINTS.get(hint.strip().upper()) or detect_system(grade_value)
    else:
        system = detect_system(grade_value)

    length_raw_m = _LENGTH_RE.search(html)
    length_raw = length_raw_m.group(1).strip() if length_raw_m else None
    length_m = parse_length(length_raw)

    lat_m = _LAT_RE.search(html)
    lng_m = _LNG_RE.search(html)
    latitude = float(lat_m.group(1)) if lat_m else None
    longitude = float(lng_m.group(1)) if lng_m else None

    discipline: str | None = None
    disc_m = _DISC_FILTER_RE.search(html)
    if disc_m:
        discipline = disc_m.group(1).lower()
    else:
        disc_t = _DISC_TITLE_RE.search(html)
        if disc_t:
            discipline = disc_t.group(1).lower()

    area_path: list[str] = []
    crumbs_idx = html.find("crumbs__all")
    if crumbs_idx != -1:
        window = html[crumbs_idx : crumbs_idx + 5000]
        area_path = [
            H.unescape(seg).strip() for seg in _CRUMB_RE.findall(window)
        ]
        # el último crumb es la propia ruta
        area_path = [seg for seg in area_path if seg != name]

    return ParsedRoute(
        source_entity_id=route_id_m.group(1),
        source_url=url,
        name=name,
        grade_value=grade_value,
        grade_system=system,
        discipline=discipline,
        length_raw=length_raw,
        length_m=length_m,
        latitude=latitude,
        longitude=longitude,
        status="unknown",
        area_path=area_path,
    )
