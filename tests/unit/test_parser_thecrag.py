"""Tests del parser de The Crag contra fixtures reales capturados.

No hay red: todos los casos usan HTML estático de tests/fixtures/thecrag/.
"""

from dirtbag_data.crawlers.thecrag.parser import parse_area_page, parse_route_page
from dirtbag_data.normalization.grades import GradeSystem
from tests.conftest import load_fixture


def test_root_area_counts():
    page = parse_area_page(
        load_fixture("el_salto_area.html"),
        "https://www.thecrag.com/en/climbing/mexico/el-salto",
    )
    assert len(page.routes) == 18
    assert len(page.child_areas) == 12


def test_first_row_decoded():
    page = parse_area_page(
        load_fixture("el_salto_area.html"),
        "https://www.thecrag.com/en/climbing/mexico/el-salto",
    )
    first = page.routes[0]
    assert first.source_entity_id == "6411281955"
    assert first.name == "Floyd el rosa"
    assert first.grade_value == "5.9"
    assert first.grade_system is GradeSystem.YDS
    assert first.discipline == "sport"
    # path del tr title desescapado dos veces: "El Salto / Cañon de San Cristobal / ..."
    assert first.area_path[0] == "El Salto"
    assert "Cañón de San Cristobal" in first.area_path
    assert first.url.endswith("/route/6411281955")


def test_child_areas():
    page = parse_area_page(
        load_fixture("el_salto_area.html"),
        "https://www.thecrag.com/en/climbing/mexico/el-salto",
    )
    delirios = next(c for c in page.child_areas if c.source_entity_id == "9288277437")
    assert delirios.name == "Los Delirios"
    assert delirios.route_count == 27
    # el enlace de nombre NO lleva /locate (ese es el de la ventana de mapa)
    assert delirios.url.endswith("/area/9288277437")
    assert "/locate" not in delirios.url


def test_leaf_area_partial_rows():
    page = parse_area_page(
        load_fixture("area_9288353292.html"),
        "https://www.thecrag.com/en/climbing/mexico/el-salto/area/9288353292",
    )
    # las páginas de área solo listan destacados (3 de 18) — lo documentamos
    assert len(page.routes) == 3
    assert page.routes[0].source_entity_id == "9288615810"
    assert page.routes[0].grade_value == "5.11c"
    assert page.child_areas == []


def test_route_page_full_ficha():
    url = "https://www.thecrag.com/en/climbing/mexico/el-salto/route/11939401"
    route = parse_route_page(load_fixture("route_11939401.html"), url)
    assert route.source_entity_id == "11939401"
    assert route.name == "Alien Tufa"
    assert route.grade_value == "5.11c"
    assert route.grade_system is GradeSystem.YDS  # hint "Set using US grade config"
    assert route.length_raw == "28m"
    assert route.length_m == 28.0
    assert route.latitude == 25.39458320761
    assert route.longitude == -100.23904078036
    assert route.discipline == "sport"
    assert route.status == "unknown"
    assert route.area_path == [
        "North America",
        "Mexico",
        "Nuevo León",
        "El Salto",
        "Cañón de San Cristobal",
        "Las Ánimas",
    ]


def test_route_page_requires_route_id():
    import pytest

    with pytest.raises(ValueError, match="no /route/"):
        parse_route_page("<html></html>", "https://www.thecrag.com/en/climbing/mexico")
