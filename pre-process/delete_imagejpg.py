from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Set
import codecs

# ตั้งค่าให้แสดงผลภาษาไทยได้ถูกต้อง
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='replace')


def find_non_hourly_images(directory: Path, exts: Set[str]) -> List[Path]:
    """
    ค้นหารูปภาพที่มีเวลา 20 นาทีหรือ 40 นาที
    Pattern: YYYYMMDD_HHMMSS โดยที่ MM = 20 หรือ 40
    """
    pattern = re.compile(r'_\d{8}_\d{2}(20|40)\d{2}_')
    
    matches: List[Path] = []
    for p in directory.iterdir():
        if not p.is_file(): continue
        if p.suffix.lower().lstrip('.') not in exts: continue
        
        if pattern.search(p.name):
            matches.append(p)
    return matches


def rename_files_remove_hash(directory: Path, exts: Set[str], dry_run: bool = True) -> int:
    """
    เปลี่ยนชื่อไฟล์โดยลบ hash ออก (62fb71e-5_... -> 5_...)
    """
    pattern = re.compile(r'^[a-f0-9]+-(\d+_.+)$', re.IGNORECASE)
    renamed = 0
    for p in directory.iterdir():
        if not p.is_file(): continue
        if p.suffix.lower().lstrip('.') not in exts: continue
        
        match = pattern.match(p.name)
        if match:
            new_name = match.group(1)
            new_path = p.parent / new_name
            
            if new_path.exists():
                print(f"  ⚠ ข้าม (Hash): {p.name} (ไฟล์ {new_name} มีอยู่แล้ว)")
                continue
            
            if dry_run:
                print(f"  [แก้ Hash] {p.name} \n             --> {new_name}")
            else:
                try:
                    p.rename(new_path)
                    print(f"  ✓ แก้ Hash: {p.name} \n             --> {new_name}")
                    renamed += 1
                except Exception as e:
                    print(f"  ✗ ไม่สามารถเปลี่ยนชื่อ {p.name}: {e}")
    return renamed


def clean_long_duplicate_files(directory: Path, exts: Set[str], dry_run: bool = True) -> int:
    """
    จัดการไฟล์ชื่อยาว (5_05-17_5_2025...)
    - ถ้ามีไฟล์ชื่อสั้น (5_2025...) อยู่แล้ว -> ลบไฟล์ชื่อยาวทิ้ง (Duplicate)
    - ถ้าไม่มีไฟล์ชื่อสั้น -> เปลี่ยนชื่อไฟล์ยาวเป็นไฟล์สั้น (Rename)
    """
    cleaned = 0
    
    # Regex จับ Pattern: เลข_เดือน-วัน_เลข_(วันเวลา...)
    # Group 1: เลขหน้า (เช่น 5)
    # Group 2: ส่วนหลัง (เช่น 20250517_000334_panorama.jpg)
    long_pattern = re.compile(r'^(\d+)_\d{2}-\d{2}_\d+_(\d{8}_\d{6}_panorama.+)$')

    for p in directory.iterdir():
        if not p.is_file(): continue
        if p.suffix.lower().lstrip('.') not in exts: continue

        match = long_pattern.match(p.name)
        if match:
            # สร้างชื่อเป้าหมายแบบสั้น
            short_name = f"{match.group(1)}_{match.group(2)}"
            short_path = p.parent / short_name
            
            if short_path.exists():
                # กรณีที่ 1: ไฟล์ชื่อสั้นมีอยู่แล้ว = ไฟล์นี้คือตัวซ้ำ -> ลบทิ้ง
                if dry_run:
                    print(f"  [ลบตัวซ้ำ] {p.name} (เพราะมี {short_name} แล้ว)")
                else:
                    try:
                        p.unlink()
                        print(f"  ✓ ลบตัวซ้ำ: {p.name}")
                        cleaned += 1
                    except Exception as e:
                        print(f"  ✗ ลบไม่ได้ {p.name}: {e}")
            else:
                # กรณีที่ 2: ไฟล์ชื่อสั้นยังไม่มี = ไฟล์นี้ชื่อผิด -> เปลี่ยนชื่อ
                if dry_run:
                    print(f"  [แก้ชื่อยาว] {p.name} \n              --> {short_name}")
                else:
                    try:
                        p.rename(short_path)
                        print(f"  ✓ แก้ชื่อยาว: {p.name} \n              --> {short_name}")
                        cleaned += 1
                    except Exception as e:
                        print(f"  ✗ เปลี่ยนชื่อไม่ได้ {p.name}: {e}")
                        
    return cleaned


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean Images: Remove Hash, Delete Duplicates, Delete 20/40min")
    
    # ปรับ Default path และ extensions ตามที่ต้องการ (Labels หรือ Images)
    parser.add_argument("--dir", default=r'D:\model_cuu\dataset\images', help="โฟลเดอร์เป้าหมาย")
    parser.add_argument("--exts", default='jpg,jpeg,png', help="นามสกุลไฟล์")
    
    parser.add_argument("--dry-run", action='store_true', help="แสดงรายการโดยไม่ทำจริง")
    parser.add_argument("--yes", action='store_true', help="ข้ามการยืนยันและดำเนินการทันที")
    parser.add_argument("--skip-delete", action='store_true', help="ข้ามการลบไฟล์")
    parser.add_argument("--skip-rename", action='store_true', help="ข้ามการเปลี่ยนชื่อ")

    args = parser.parse_args()
    target_dir = Path(args.dir)
    exts = set([e.strip().lower() for e in args.exts.split(',') if e.strip()])

    if not target_dir.exists():
        print(f"Error: ไม่พบโฟลเดอร์: {target_dir}")
        return

    print(f"Target: {target_dir}")
    print(f"Extensions: {exts}")

    # ============================================
    # ส่วนที่ 1: เปลี่ยนชื่อไฟล์ (ลบ hash)
    # ============================================
    if not args.skip_rename:
        print("=" * 60)
        print("ส่วนที่ 1: ลบ Hash ออกจากชื่อไฟล์ (xxxx-5_2025... -> 5_2025...)")
        print("=" * 60)
        rename_files_remove_hash(target_dir, exts, dry_run=args.dry_run)
        print()
    
    # ============================================
    # ส่วนที่ 2: จัดการไฟล์ชื่อยาว (ซ้ำ)
    # ============================================
    print("=" * 60)
    print("ส่วนที่ 2: ลบไฟล์ชื่อยาวที่ซ้ำ (5_05-17_5_2025... -> ลบ)")
    print("=" * 60)
    clean_long_duplicate_files(target_dir, exts, dry_run=args.dry_run)
    print()

    

if __name__ == '__main__':
    main()