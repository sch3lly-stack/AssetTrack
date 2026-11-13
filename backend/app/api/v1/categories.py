from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.category import AssetCategory
from app.models.asset import Asset
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.api.deps import require_authenticated, require_asset_manager_or_admin
from app.services.audit import log_audit_event

router = APIRouter(prefix="/categories", tags=["Asset Categories"])


@router.get("", response_model=List[CategoryResponse])
def list_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated)
):
    cats = db.query(AssetCategory).all()
    results = []
    for c in cats:
        resp = CategoryResponse.model_validate(c)
        resp.asset_count = db.query(Asset).filter(Asset.category_id == c.id).count()
        results.append(resp)
    return results


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    cat_in: CategoryCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_asset_manager_or_admin)
):
    existing = db.query(AssetCategory).filter(
        (AssetCategory.name.ilike(cat_in.name)) | (AssetCategory.code == cat_in.code.upper())
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category with this name or code already exists")

    new_cat = AssetCategory(
        name=cat_in.name,
        code=cat_in.code.upper(),
        description=cat_in.description,
        default_lifespan_months=cat_in.default_lifespan_months,
        default_depreciation_method=cat_in.default_depreciation_method
    )
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)

    log_audit_event(
        db=db,
        action="CREATE_CATEGORY",
        entity_type="AssetCategory",
        entity_id=new_cat.id,
        changes={"name": new_cat.name, "code": new_cat.code},
        user=current_user,
        request=request
    )
    return new_cat


@router.put("/{cat_id}", response_model=CategoryResponse)
def update_category(
    cat_id: str,
    cat_in: CategoryUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_asset_manager_or_admin)
):
    cat = db.query(AssetCategory).filter(AssetCategory.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    if cat_in.name:
        cat.name = cat_in.name
    if cat_in.code:
        cat.code = cat_in.code.upper()
    if cat_in.description is not None:
        cat.description = cat_in.description
    if cat_in.default_lifespan_months is not None:
        cat.default_lifespan_months = cat_in.default_lifespan_months
    if cat_in.default_depreciation_method is not None:
        cat.default_depreciation_method = cat_in.default_depreciation_method

    db.commit()
    db.refresh(cat)

    log_audit_event(
        db=db,
        action="UPDATE_CATEGORY",
        entity_type="AssetCategory",
        entity_id=cat.id,
        changes={"name": cat.name, "code": cat.code},
        user=current_user,
        request=request
    )
    return cat
