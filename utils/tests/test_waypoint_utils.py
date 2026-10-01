"""
TODO(bootcamper): write the tests for ``src/waypoint_utils.py`` in here.

The example below covers files that parse fine: with and without ``home``,
and files with comments and blank lines in them. The rest is yours:

- Bad data: a file whose top level isn't a mapping, waypoints missing
  ``lat``, ``lon``, or ``alt``, values that aren't numbers, YAML that
  doesn't parse, and a file that isn't there.
- Out of range: latitudes past +/-90 and longitudes past +/-180 get
  rejected.
- Nothing to work with: an empty file, an empty ``waypoints`` list, and
  ``sort_clockwise_sweep`` given a list of 0 or 1 waypoints.
- ``east_north_coordinate_offset_m``: offsets you worked out yourself,
  compared with ``pytest.approx``. Never use ``==`` on meters.
- Ordering: with no ``home``, ``sort_clockwise_sweep`` goes clockwise
  starting from north.
- With a ``home``: the order starts in home's direction instead, and goes
  back to starting at north if home is right on top of the centroid.
- Two waypoints in the same direction: the closer one comes first.
- Parsing gives you frozen ``Coordinate`` objects that can't be changed.

Graded by ``warg run utils grade-tests``: pass on the real code, 90% branch
coverage, and fail on every broken copy in ``grader/mutants/``.
"""

from dataclasses import FrozenInstanceError

import pytest

from src.types import Coordinate
from src.waypoint_utils import (
    east_north_coordinate_offset_m,
    parse_waypoints_file,
    sort_clockwise_sweep,
)

# The helper and the test below are given to you.


def write_to_tmp_waypoints_file(tmp_path, text):
    """Write ``text`` to a YAML file and hand back its path.

    ``tmp_path`` is a pytest fixture: a fresh empty directory per test.
    """
    path = tmp_path / "waypoints.yaml"
    path.write_text(text)
    return path


# One test, three files. ``parametrize`` runs the test body once per
# ``(text, expected)`` pair, and ``ids`` names each run so a failure tells you
# which file broke.
@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            """
            home: {lat: 1, lon: 2, alt: 3}
            waypoints:
              - {lat: 4, lon: 5, alt: 6}
            """,
            (Coordinate(1, 2, 3), [Coordinate(4, 5, 6)]),
        ),
        (
            """
            waypoints:
              - {lat: 4, lon: 5, alt: 6}
              - {lat: 7, lon: 8, alt: 9}
            """,
            (None, [Coordinate(4, 5, 6), Coordinate(7, 8, 9)]),
        ),
        (
            """
            # a lap

            home: {lat: 1, lon: 2, alt: 3}

            waypoints:
              # first leg
              - {lat: 4, lon: 5, alt: 6}
            """,
            (Coordinate(1, 2, 3), [Coordinate(4, 5, 6)]),
        ),
    ],
    ids=["home-and-waypoints", "no-home", "comments-and-blank-lines"],
)
def test_parse_waypoints_file_success(tmp_path, text, expected):
    path = write_to_tmp_waypoints_file(tmp_path, text)
    assert parse_waypoints_file(path) == expected

def test_parse_waypoints_file_empty(tmp_path):
    path = write_to_tmp_waypoints_file(tmp_path, "")
    assert parse_waypoints_file(path) == (None, [])
    
def test_parse_waypoints_file_missing_lat(tmp_path):
    path = write_to_tmp_waypoints_file(
        tmp_path,
        """
        waypoints:
          - {lon: 1, alt: 1}
        """,
    )
    with pytest.raises(ValueError):
      parse_waypoints_file(path)

def test_parse_waypoints_file_missing_alt(tmp_path):
    path = write_to_tmp_waypoints_file(
        tmp_path,
        """
        waypoints:
          - {lat: 1, lon: 1}
        """,
    )
    with pytest.raises(ValueError):
      parse_waypoints_file(path)

def test_parse_waypoints_file_missing_lon(tmp_path):
    path = write_to_tmp_waypoints_file(
        tmp_path,
        """
        waypoints:
          - {lat: 1, alt: 1}
        """,
    )
    with pytest.raises(ValueError):
      parse_waypoints_file(path)

def test_parse_waypoints_file_range1(tmp_path):
    path = write_to_tmp_waypoints_file(
        tmp_path,
        """
        waypoints:
          - {lat: 91, lon: 180, alt: 10}
        """,
    )
    with pytest.raises(ValueError):
        parse_waypoints_file(path)

def test_parse_waypoints_file_range2(tmp_path):
    path = write_to_tmp_waypoints_file(
        tmp_path,
        """
        waypoints:
          - {lat: 90, lon: 181, alt: 10}
        """,
    )
    with pytest.raises(ValueError):
        parse_waypoints_file(path)

def test_parse_waypoints_file_invalid_yaml(tmp_path):
    path = write_to_tmp_waypoints_file(
        tmp_path,
        """
        waypoints:
          - {lat: 1, lon: 2, alt: 3
        """,
    )

    with pytest.raises(ValueError):
        parse_waypoints_file(path)

def test_parse_waypoints_file_empty_waylist(tmp_path):
    path = write_to_tmp_waypoints_file(
        tmp_path,
        """
        waypoints: []
        """,
    )

    assert parse_waypoints_file(path) == (None, [])

def test_parse_waypoints_file_range3(tmp_path):
    path = write_to_tmp_waypoints_file(
        tmp_path,
        """
        waypoints:
          - {lat: a, lon: 10, alt: c}
        """,
    )

    with pytest.raises(ValueError):
        parse_waypoints_file(path)

def test_parse_waypoints_file_mapping(tmp_path):
    path = write_to_tmp_waypoints_file(
        tmp_path,
        """
          - lat: 1, lon: 2, alt: 3
        """,
    )

    with pytest.raises(ValueError):
        parse_waypoints_file(path)
  
def test_sort_clockwise_sweep_one_waypoint():
    waypoint = Coordinate(43, -80, 15)

    assert sort_clockwise_sweep([waypoint]) == [waypoint]

def test_sort_clockwise_sweep_no_waypoints():
    assert sort_clockwise_sweep([]) == []

def test_east_north_coordinate_offset_m_east():
    east, north = east_north_coordinate_offset_m(
        10.0, -80.0,
        10.0, -79.0,
    )

    assert east == pytest.approx(109506, abs =1)
    assert north == pytest.approx(0)
    
def test_east_north_coordinate_offset_m_north():
    east, north = east_north_coordinate_offset_m(
        10.0, -80.0,
        11.0, -80.0,
    )

    assert east == pytest.approx(0)
    assert north == pytest.approx(111195, abs=1)

def test_parse_waypoints_file_coordinate_is_frozen(tmp_path):
    path = write_to_tmp_waypoints_file(
        tmp_path,
        """
        waypoints:
          - {lat: 1, lon: 2, alt: 3}
        """,
    )

    _, waypoints = parse_waypoints_file(path)

    with pytest.raises(FrozenInstanceError):
        waypoints[0].lat = 5

def test_sort_clockwise_sweep_no_home():
    north = Coordinate(3, -1, 10)
    east = Coordinate(2, 0, 10)
    south = Coordinate(1, -1, 10)
    west = Coordinate(2, -2, 10)

    waypoints = [west, south, north, east]

    assert sort_clockwise_sweep(waypoints) == [north, east, south, west]

def test_sort_clockwise_sweep_no_home2():
    a = Coordinate(2, 10, 10)
    b = Coordinate(2, 0, 10)
    c = Coordinate(2, -1, 10)

    waypoints = [c, b, a]

    assert sort_clockwise_sweep(waypoints) == [a, b, c]


def test_parse_waypoints_file_missing_file(tmp_path):
    path = tmp_path / "dfgxsrth.yaml"

    with pytest.raises(OSError):
        parse_waypoints_file(path)

def test_sort_clockwise_sweep_home2():
    home = Coordinate(2, 1, 10)
    north = Coordinate(3, -1, 10)
    east = Coordinate(2, 0, 10)
    south = Coordinate(1, -1, 10)
    west = Coordinate(2, -2, 10)

    waypoints = [west, south, north, east]

    assert sort_clockwise_sweep(waypoints, home) == [east, south, west, north]

