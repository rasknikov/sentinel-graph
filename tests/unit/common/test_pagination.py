from packages.common.pagination import Page, PageMeta


def test_page_meta_validates_positive_page_values() -> None:
    meta = PageMeta(page=1, page_size=25, total_items=100)

    assert meta.model_dump(mode="json") == {
        "page": 1,
        "page_size": 25,
        "total_items": 100,
    }


def test_page_serializes_items_and_meta() -> None:
    page = Page[str](
        items=["a", "b"],
        meta=PageMeta(page=1, page_size=2, total_items=2),
    )

    assert page.model_dump(mode="json") == {
        "items": ["a", "b"],
        "meta": {"page": 1, "page_size": 2, "total_items": 2},
    }
