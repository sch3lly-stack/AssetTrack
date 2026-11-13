import os
import io
import base64
import json
import qrcode
from app.config import settings
from app.models.asset import Asset


def ensure_qr_dir():
    os.makedirs(settings.QR_DIR, exist_ok=True)


def generate_asset_qr(asset: Asset) -> str:
    ensure_qr_dir()
    
    qr_payload = {
        "asset_tag": asset.asset_tag,
        "serial_number": asset.serial_number,
        "name": asset.name,
        "manufacturer": asset.manufacturer,
        "model": asset.model,
        "url": f"/assets/{asset.id}"
    }

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(json.dumps(qr_payload))
    qr.make(fit=True)

    img = qr.make_image(fill_color="#0F172A", back_color="#FFFFFF")
    
    filename = f"{asset.asset_tag}.png".replace("/", "_").replace("\\", "_")
    filepath = os.path.join(settings.QR_DIR, filename)
    img.save(filepath)
    
    return f"/media/qr_codes/{filename}"


def get_asset_qr_base64(asset: Asset) -> str:
    qr_payload = {
        "asset_tag": asset.asset_tag,
        "serial_number": asset.serial_number,
        "name": asset.name,
        "manufacturer": asset.manufacturer,
        "model": asset.model,
        "url": f"/assets/{asset.id}"
    }

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(json.dumps(qr_payload))
    qr.make(fit=True)

    img = qr.make_image(fill_color="#0F172A", back_color="#FFFFFF")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    
    return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"
