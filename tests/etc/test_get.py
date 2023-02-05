import pytest
import tomlkit

from tomato import etc


@pytest.fixture
def etc_data() -> tomlkit.TOMLDocument:
    """Setup basic `etc.data` for tests in this file."""
    etc.data = tomlkit.parse(
        """
    [table]
foo = "bar"  # String
baz = 13

[table2]
array = [1, 2, 3]
    """
    )


@pytest.mark.etc
@pytest.mark.parametrize("key", ["table", "table2"])
def test_get(etc_data: ..., key: str) -> None:
    "Simple one key."
    assert etc.data[key] is etc.get(key)


@pytest.mark.etc
def test_get_dotted(etc_data: ...) -> None:
    """Keys with dots in them."""
    assert etc.data["table"]["foo"] is etc.get("table.foo")
    assert etc.data["table"]["baz"] is etc.get("table.baz")
    assert etc.data["table2"]["array"] is etc.get("table2.array")
    assert etc.data["table2"]["array"][0] is etc.get("table2.array.0")
    assert etc.data["table2"]["array"][2] is etc.get("table2.array.2")


@pytest.mark.etc
def test_get_list(etc_data: ...) -> None:
    """Multiple keys."""
    assert etc.data["table"]["foo"] is etc.get("table", "foo")
    assert etc.data["table"]["baz"] is etc.get("table", "baz")
    assert etc.data["table2"]["array"] is etc.get("table2", "array")
    assert etc.data["table2"]["array"][0] is etc.get("table2", "array", "0")
    assert etc.data["table2"]["array"][2] is etc.get("table2", "array", 2)
    assert etc.data["table2"]["array"][2] is etc.get(*["table2", "array", 2])


@pytest.mark.etc
def test_get_defaults(etc_data: ...) -> None:
    """Non-existing keys with default values."""
    obj = object()

    assert "bar" == etc.get("table", "foo", default_value=None)
    assert 2 == etc.get("table2", "foo", default_value=2)
    assert obj is etc.get("table2", "foo", default_value=obj)
    assert None is etc.get("table2", "foo", default_value=None)

    print("testing")


@pytest.mark.etc
@pytest.mark.parametrize(
    "keys",
    [
        ("table.unknown_key",),
        ("table", "unknown_key"),
        ("table2", "foo"),
    ],
)
def test_get_no_defaults(etc_data: ..., keys: list[str]) -> None:
    """Non-existing keys without default values."""
    with pytest.raises(KeyError):
        etc.get(*keys)


@pytest.mark.etc
@pytest.mark.parametrize(
    "keys",
    [
        (
            [
                "table.unknown_key",
            ],
        ),
        (["table", "unknown_key"],),
        (
            [
                "table2",
            ],
            "array",
        ),
        (
            "table2",
            [
                "array",
            ],
        ),
    ],
)
def test_get_errors_attr(etc_data: ..., keys: list[str]) -> None:
    """Invalid keys."""
    with pytest.raises(AttributeError):
        etc.get(*keys)


@pytest.mark.etc
@pytest.mark.parametrize(
    "keys",
    [
        (
            "table2",
            "array",
            [
                2,
            ],
        ),
        (),
    ],
)
def test_get_errors_type(etc_data: ..., keys: list[str]) -> None:
    """Invalid keys."""
    with pytest.raises(TypeError):
        etc.get(*keys)


@pytest.mark.etc
def test_get_empty(etc_data: ...) -> None:
    """Calls without `keys`."""
    with pytest.raises(TypeError):
        etc.get()


@pytest.mark.etc
@pytest.mark.parametrize("defaults", [None, etc.DEFAULT_VALUE])
def test_get_empty_defs(etc_data: ..., defaults: ...) -> None:
    """Calls without `keys`."""
    with pytest.raises(TypeError):
        etc.get(default_value=defaults)


@pytest.mark.etc
@pytest.mark.parametrize(
    "keys",
    [
        "table",
        [
            "table",
        ],
        "table.foo",
        ["table", "not_exists"],
    ],
)
def test_get_named_keys(etc_data: ..., keys: ...) -> None:
    with pytest.raises(TypeError):
        etc.get(keys=keys)
