"""
Quick test script — run this in backend folder with venv active:
  python test_blip.py

This will:
1. Trigger BLIP model download (~900MB, one time only)
2. Test caption generation with a sample image
3. Show you the real AI caption
"""

import requests
import sys
import os
from pathlib import Path

BASE_URL = "http://localhost:8000"

def check_health():
    print("\n📡 Checking server health...")
    try:
        r = requests.get(f"{BASE_URL}/api/v1/health", timeout=5)
        data = r.json()
        print(f"   Status      : {data.get('status')}")
        print(f"   Model Mode  : {data.get('model_mode')}  ← should say 'blip' after loading")
        print(f"   Model Loaded: {data.get('model_loaded')}")
        print(f"   Device      : {data.get('device')}")
        print(f"   Redis       : {data.get('redis_connected')} (false is OK)")
        return True
    except Exception as e:
        print(f"   ❌ Could not reach server: {e}")
        return False

def test_with_sample_image():
    print("\n🖼️  Testing caption generation...")
    
    # Create a simple test image (red square - quick test)
    try:
        from PIL import Image
        import io
        img = Image.new("RGB", (224, 224), color=(180, 100, 60))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)
        image_bytes = buf.getvalue()
        print("   Created test image (224x224 solid color)")
    except Exception as e:
        print(f"   ❌ PIL error: {e}")
        return

    print("   Sending to /api/v1/generate-caption ...")
    print("   ⏳ First call triggers BLIP download (~900MB) — may take a few minutes...")
    
    try:
        r = requests.post(
            f"{BASE_URL}/api/v1/generate-caption",
            files={"file": ("test.jpg", image_bytes, "image/jpeg")},
            params={"beam_size": 3},
            timeout=300,  # 5 min timeout for download
        )
        if r.status_code == 200:
            data = r.json()
            print(f"\n   ✅ SUCCESS!")
            print(f"   Caption     : {data.get('caption')}")
            print(f"   Confidence  : {data.get('confidence')}")
            print(f"   Time (ms)   : {data.get('processing_time_ms')}")
            print(f"   Model Mode  : {data.get('model_mode')}")
            print(f"   Cached      : {data.get('cached')}")
        else:
            print(f"   ❌ Error {r.status_code}: {r.text}")
    except requests.exceptions.Timeout:
        print("   ⏳ Still downloading BLIP... this is normal for first run.")
        print("      Open http://localhost:5173 and upload an image — it will work once download completes.")
    except Exception as e:
        print(f"   ❌ Request failed: {e}")

if __name__ == "__main__":
    if check_health():
        test_with_sample_image()
    print("\n✅ Done. Open http://localhost:5173 to use the app.\n")
