from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Set
import codecs

# ตั้งค่าให้แสดงผลภาษาไทยได้ถูกต้องใน Terminal Windows
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='replace')

def clean_extension_mistakes(directory: Path, exts: Set[str], dry_run: bool = True) -> int:
    """
    แก้ไขนามสกุลผิด: _jpg.txt -> .txt
    """
    fixed = 0
    for p in directory.iterdir():
        if not p.is_file(): continue
        
        # แก้ _jpg.txt หรือ _png.txt เป็น .txt
        if p.name.endswith("_jpg.txt"):
            new_name = p.name.replace("_jpg.txt", ".txt")
        elif p.name.endswith("_png.txt"):
            new_name = p.name.replace("_png.txt", ".txt")
        else:
            continue

        new_path = p.parent / new_name
        if new_path.exists():
             # ถ้าแก้แล้วชื่อไปซ้ำกับที่มีอยู่ ก็ข้ามไปก่อน เดี๋ยวฟังก์ชัน duplicate จะจัดการต่อ
             continue

        if dry_run:
            print(f"  [แก้ชื่อ] {p.name} -> {new_name}")
        else:
            try:
                p.rename(new_path)
                print(f"  ✓ แก้ชื่อ: {p.name} -> {new_name}")
                fixed += 1
            except Exception as e:
                print(f"  ✗ Error: {e}")
    return fixed

def clean_long_duplicate_files(directory: Path, exts: Set[str], dry_run: bool = True) -> int:
    """
    จัดการไฟล์ชื่อยาว (5_05-17_5_2025...txt)
    1. ถ้ามีไฟล์ชื่อสั้น (5_2025...txt) อยู่แล้ว -> ลบไฟล์ชื่อยาวทิ้ง (Duplicate)
    2. ถ้าไม่มีไฟล์ชื่อสั้น -> เปลี่ยนชื่อไฟล์ยาวเป็นไฟล์สั้น (Rename)
    """
    cleaned = 0
    
    # Regex จับ Pattern: เลขหน้า_ขยะตรงกลาง_วันเวลา...
    # ใช้ได้ทั้ง .txt และ .jpg
    long_pattern = re.compile(r'^(\d+)_.+?_(\d{8}_\d{6}_panorama.*)$')

    for p in directory.iterdir():
        if not p.is_file(): continue
        
        # กรองนามสกุล
        current_ext = p.suffix.lower().lstrip('.')
        if current_ext not in exts: continue

        match = long_pattern.match(p.name)
        if match:
            # สร้างชื่อเป้าหมายแบบสั้น: Group1(เลขหน้า) + "_" + Group2(วันเวลา...)
            short_name = f"{match.group(1)}_{match.group(2)}"
            short_path = p.parent / short_name
            
            if short_path.exists():
                # กรณีที่ 1: ไฟล์ชื่อสั้นมีอยู่แล้ว = ไฟล์นี้คือตัวซ้ำ -> ลบทิ้ง
                if dry_run:
                    print(f"  [ลบตัวซ้ำ] {p.name}")
                    print(f"             (เพราะมี {short_name} อยู่แล้ว)")
                else:
                    try:
                        p.unlink()
                        print(f"  ✓ ลบตัวซ้ำ: {p.name}")
                        cleaned += 1
                    except Exception as e:
                        print(f"  ✗ ลบไม่ได้ {p.name}: {e}")
            else:
                # กรณีที่ 2: ไฟล์ชื่อสั้นยังไม่มี -> เปลี่ยนชื่อให้สั้นลง
                if dry_run:
                    print(f"  [แก้ชื่อยาว] {p.name}")
                    print(f"              -> {short_name}")
                else:
                    try:
                        p.rename(short_path)
                        print(f"  ✓ แก้ชื่อยาว: {p.name}")
                        print(f"              -> {short_name}")
                        cleaned += 1
                    except Exception as e:
                        print(f"  ✗ เปลี่ยนชื่อไม่ได้ {p.name}: {e}")
                        
    return cleaned

def find_non_hourly_files(directory: Path, exts: Set[str]) -> List[Path]:
    """ค้นหาไฟล์ที่มีเวลา 20 นาทีหรือ 40 นาที"""
    pattern = re.compile(r'_\d{8}_\d{2}(20|40)\d{2}_')
    matches: List[Path] = []
    for p in directory.iterdir():
        if not p.is_file(): continue
        if p.suffix.lower().lstrip('.') not in exts: continue
        if pattern.search(p.name):
            matches.append(p)
    return matches

def main() -> None:
    parser = argparse.ArgumentParser(description="Clean TXT Labels & Duplicates")
    
    # *** ตั้งค่า Default ให้เป็น labels และ .txt ***
    parser.add_argument("--dir", default=r'D:\model_cuu\dataset_method_1\labels', help="โฟลเดอร์เป้าหมาย")
    parser.add_argument("--exts", default='txt', help="นามสกุลไฟล์")
    
    parser.add_argument("--dry-run", action='store_true', help="แสดงรายการโดยไม่ทำจริง")
    parser.add_argument("--yes", action='store_true', help="ยืนยันทำทันที")
    parser.add_argument("--skip-delete", action='store_true', help="ข้ามการลบไฟล์ 20/40 (ไม่รวมลบไฟล์ซ้ำ)")

    args = parser.parse_args()
    target_dir = Path(args.dir)
    exts = set([e.strip().lower() for e in args.exts.split(',') if e.strip()])

    if not target_dir.exists():
        print(f"Error: ไม่พบโฟลเดอร์: {target_dir}")
        return

    print(f"Target: {target_dir}")
    print(f"Extensions: {exts}")

    # 1. แก้ _jpg.txt ก่อน
    print("=" * 60)
    print("ส่วนที่ 1: แก้ไขนามสกุลผิด (_jpg.txt -> .txt)")
    print("=" * 60)
    clean_extension_mistakes(target_dir, exts, dry_run=args.dry_run)
    print()

    # 2. จัดการไฟล์ซ้ำและชื่อยาว
    print("=" * 60)
    print("ส่วนที่ 2: ลบไฟล์ซ้ำ (Duplicate) และแก้ชื่อยาว")
    print("=" * 60)
    clean_long_duplicate_files(target_dir, exts, dry_run=args.dry_run)
    print()

    
if __name__ == '__main__':
    main()