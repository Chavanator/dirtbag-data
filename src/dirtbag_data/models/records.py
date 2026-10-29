"""Contratos de datos producidos por los parsers (models/, spec Phase 5)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from dirtbag_data.normalization.grades import GradeSystem


class RouteLink(BaseModel):
    """Fila de ruta vista en una página de área (descubrimiento)."""

    source_entity_id: str
    url: str
    name: str
    grade_value: str
    grade_system: GradeSystem
    discipline: str | None = None
    area_path: list[str] = Field(default_factory=list)


class ChildArea(BaseModel):
    """Sub-área listada en una página de área."""

    source_entity_id: str
    url: str
    name: str
    route_count: int | None = None


class AreaPage(BaseModel):
    """Resultado de parsear una página de área."""

    url: str
    routes: list[RouteLink] = Field(default_factory=list)
    child_areas: list[ChildArea] = Field(default_factory=list)


class ParsedRoute(BaseModel):
    """Ficha completa de una ruta (página de ruta), tal como la fuente la muestra."""

    source_entity_id: str
    source_url: str
    name: str
    grade_value: str
    grade_system: GradeSystem
    discipline: str | None = None
    length_raw: str | None = None
    length_m: float | None = None
    latitude: float | None = None
    longitude: float | None = None
    status: str = "unknown"
    area_path: list[str] = Field(default_factory=list)

    def fill_missing(self, link: RouteLink) -> None:
        """Completa huecos de la ficha con los datos de la fila del área."""
        if not self.discipline:
            self.discipline = link.discipline
        if not self.area_path:
            self.area_path = link.area_path
