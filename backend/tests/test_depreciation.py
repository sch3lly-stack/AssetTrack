from datetime import date
from app.models.asset import Asset, DepreciationMethod
from app.services.depreciation import calculate_asset_depreciation


def test_straight_line_depreciation():
    asset = Asset(
        purchase_cost=3600.0,
        salvage_value=0.0,
        purchase_date=date(2025, 1, 1),
        expected_lifespan_months=36,
        depreciation_method=DepreciationMethod.STRAIGHT_LINE,
    )
    # Exactly 12 months later (1 year into 3-year lifespan)
    as_of = date(2026, 1, 1)
    deprec = calculate_asset_depreciation(asset, as_of_date=as_of)

    # 3600 / 36 = $100 per month * 12 months = $1200 depreciation
    # Remaining book value = $2400
    assert deprec["age_months"] == 12
    assert deprec["remaining_months"] == 24
    assert deprec["accumulated_depreciation"] == 1200.0
    assert deprec["current_book_value"] == 2400.0
    assert deprec["percent_depreciated"] == 33.33
    assert not deprec["is_past_eol"]


def test_double_declining_depreciation():
    asset = Asset(
        purchase_cost=10000.0,
        salvage_value=1000.0,
        purchase_date=date(2025, 1, 1),
        expected_lifespan_months=24,
        depreciation_method=DepreciationMethod.DOUBLE_DECLINING,
    )
    as_of = date(2025, 7, 1)  # 6 months in
    deprec = calculate_asset_depreciation(asset, as_of_date=as_of)

    assert deprec["age_months"] == 6
    assert deprec["current_book_value"] < 10000.0
    assert deprec["current_book_value"] >= 1000.0  # never below salvage
    assert deprec["accumulated_depreciation"] > 0


def test_past_eol_flag():
    asset = Asset(
        purchase_cost=2000.0,
        salvage_value=100.0,
        purchase_date=date(2020, 1, 1),
        expected_lifespan_months=36,  # 3 years
        depreciation_method=DepreciationMethod.STRAIGHT_LINE,
    )
    as_of = date(2026, 1, 1)  # 6 years later
    deprec = calculate_asset_depreciation(asset, as_of_date=as_of)

    assert deprec["is_past_eol"] is True
    assert deprec["remaining_months"] == 0
    assert deprec["current_book_value"] == 100.0  # equals salvage value
