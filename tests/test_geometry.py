import pytest

from seaez.params import DEFAULT


@pytest.fixture(scope="module")
def mesh():
    from design.geometry import hull_mesh
    return hull_mesh(DEFAULT)


def test_hull_mesh_watertight(mesh):
    assert mesh.is_watertight


def test_hull_mesh_dimensions(mesh):
    length = mesh.bounds[1][0] - mesh.bounds[0][0]
    beam = mesh.bounds[1][1] - mesh.bounds[0][1]
    assert length == pytest.approx(DEFAULT.hull_length_ft, rel=0.05)
    assert beam <= DEFAULT.hull_beam_ft * 1.05


def test_hull_volume_sane(mesh):
    # Loft of massing_v0's stations encloses roughly 20-35 ft^3.
    assert 15.0 < mesh.volume < 40.0
