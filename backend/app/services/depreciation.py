from datetime import date
from typing import Dict, Any
from app.models.asset import Asset, DepreciationMethod


def calculate_asset_depreciation(asset: Asset, as_of_date: date = None) -> Dict[str, Any]:
    if as_of_date is None:
        as_of_date = date.today()

    cost = float(asset.purchase_cost)
    salvage = float(asset.salvage_value)
    lifespan_months = max(1, asset.expected_lifespan_months)
    depreciable_base = max(0.0, cost - salvage)

    # Calculate age in months
    p_date = asset.purchase_date
    months_diff = (as_of_date.year - p_date.year) * 12 + (as_of_date.month - p_date.month)
    age_months = max(0, months_diff)
    remaining_months = max(0, lifespan_months - age_months)

    method = asset.depreciation_method

    if method == DepreciationMethod.STRAIGHT_LINE:
        monthly_depreciation = depreciable_base / lifespan_months
        accumulated = min(depreciable_base, monthly_depreciation * age_months)
        current_book_value = max(salvage, cost - accumulated)

    elif method == DepreciationMethod.DOUBLE_DECLINING:
        # 2 / N rate per year -> monthly rate = 2 / lifespan_months
        rate = 2.0 / lifespan_months
        book_val = cost
        for _ in range(min(age_months, lifespan_months)):
            deprec = book_val * rate
            if book_val - deprec < salvage:
                deprec = max(0.0, book_val - salvage)
                book_val -= deprec
                break
            book_val -= deprec
        current_book_value = max(salvage, round(book_val, 2))
        accumulated = round(cost - current_book_value, 2)

    elif method == DepreciationMethod.SUM_OF_YEARS:
        total_digits = (lifespan_months * (lifespan_months + 1)) / 2
        effective_months = min(age_months, lifespan_months)
        # Sum of fractions from 1 to effective_months
        # fraction for month k (1-indexed) = (lifespan_months - k + 1) / total_digits
        deprec_sum = 0.0
        for k in range(1, effective_months + 1):
            fraction = (lifespan_months - k + 1) / total_digits
            deprec_sum += depreciable_base * fraction
        accumulated = min(depreciable_base, round(deprec_sum, 2))
        current_book_value = max(salvage, round(cost - accumulated, 2))

    else:
        # Fallback straight line
        monthly_depreciation = depreciable_base / lifespan_months
        accumulated = min(depreciable_base, monthly_depreciation * age_months)
        current_book_value = max(salvage, cost - accumulated)

    percent_depreciated = 0.0
    if depreciable_base > 0:
        percent_depreciated = round((accumulated / depreciable_base) * 100, 2)
    elif cost > 0:
        percent_depreciated = 100.0

    is_approaching_eol = 0 < remaining_months <= 6
    is_past_eol = age_months >= lifespan_months

    return {
        "current_book_value": round(current_book_value, 2),
        "accumulated_depreciation": round(accumulated, 2),
        "age_months": age_months,
        "remaining_months": remaining_months,
        "percent_depreciated": min(100.0, percent_depreciated),
        "is_approaching_eol": is_approaching_eol,
        "is_past_eol": is_past_eol,
    }
