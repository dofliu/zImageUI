"""
檢查模型快取狀態的工具腳本
"""
import os

cache_path = r"D:\AI_Cache\HuggingFace"
model_name = "models--Tongyi-MAI--Z-Image-Turbo"
model_path = os.path.join(cache_path, model_name)

print("=" * 60)
print("模型快取檢查工具")
print("=" * 60)

print(f"\n快取根目錄: {cache_path}")
print(f"快取目錄是否存在: {'✓ 是' if os.path.exists(cache_path) else '✗ 否'}")

print(f"\n模型目錄: {model_path}")
print(f"模型是否已快取: {'✓ 是' if os.path.exists(model_path) else '✗ 否'}")

if os.path.exists(model_path):
    # 計算模型資料夾大小
    total_size = 0
    file_count = 0
    for dirpath, dirnames, filenames in os.walk(model_path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if os.path.exists(filepath):
                total_size += os.path.getsize(filepath)
                file_count += 1

    size_gb = total_size / (1024 ** 3)
    print(f"\n模型資料:")
    print(f"  - 檔案數量: {file_count}")
    print(f"  - 總大小: {size_gb:.2f} GB")

    print("\n主要檔案:")
    # 列出主要模型檔案
    snapshots_dir = os.path.join(model_path, "snapshots")
    if os.path.exists(snapshots_dir):
        for snapshot in os.listdir(snapshots_dir):
            snapshot_path = os.path.join(snapshots_dir, snapshot)
            if os.path.isdir(snapshot_path):
                print(f"\n  快照: {snapshot}")
                for file in os.listdir(snapshot_path)[:10]:  # 只顯示前10個檔案
                    file_path = os.path.join(snapshot_path, file)
                    if os.path.isfile(file_path):
                        file_size = os.path.getsize(file_path) / (1024 ** 2)  # MB
                        print(f"    - {file} ({file_size:.1f} MB)")

    print("\n✅ 模型已完整快取,後續啟動將從本地載入")
else:
    print("\n⚠️  模型尚未快取到本地")
    print("首次執行 app.py 時會自動下載模型到此目錄")

print("\n" + "=" * 60)

# 檢查 CUDA 可用性
try:
    import torch
    print("\nGPU 狀態:")
    if torch.cuda.is_available():
        print(f"✓ CUDA 可用")
        print(f"  - GPU 數量: {torch.cuda.device_count()}")
        print(f"  - GPU 名稱: {torch.cuda.get_device_name(0)}")
        print(f"  - CUDA 版本: {torch.version.cuda}")

        # 顯示 GPU 記憶體資訊
        total_memory = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
        allocated_memory = torch.cuda.memory_allocated(0) / (1024 ** 3)
        cached_memory = torch.cuda.memory_reserved(0) / (1024 ** 3)

        print(f"\nGPU 記憶體:")
        print(f"  - 總容量: {total_memory:.2f} GB")
        print(f"  - 已分配: {allocated_memory:.2f} GB")
        print(f"  - 已快取: {cached_memory:.2f} GB")
        print(f"  - 可用: {total_memory - cached_memory:.2f} GB")
    else:
        print("✗ CUDA 不可用,將無法使用 GPU")
except ImportError:
    print("\n⚠️  PyTorch 未安裝,無法檢查 GPU 狀態")

print("=" * 60)
