import os
from huggingface_hub import snapshot_download


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BASE_DIR = os.path.join(
    PROJECT_ROOT,
    "models",
    "base",
    "Qwen2.5-7B-Instruct"
)

os.makedirs(BASE_DIR, exist_ok=True)


print("=" * 70)
print("DOWNLOADING QWEN2.5-7B-INSTRUCT")
print("=" * 70)

snapshot_download(
    repo_id="Qwen/Qwen2.5-7B-Instruct",
    local_dir=BASE_DIR
)

print("\n✓ Base model downloaded")
print(f"Location: {BASE_DIR}")