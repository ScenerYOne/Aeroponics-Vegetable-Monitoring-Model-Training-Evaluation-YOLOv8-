from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Set

# Ensure stdout/stderr use UTF-8 (helps on Windows consoles with CP1252)
import codecs
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='replace')


def find_non_hourly_images(directory: Path, exts: Set[str]) -> List[Path]:
    """
    ค้นหารูปภาพที่มีเวลา 20 นาทีหรือ 40 นาที
    Pattern: YYYYMMDD_HHMMSS โดยที่ MM = 20 หรือ 40
    ตัวอย่าง: _20250610_082010_ (08:20:10) หรือ _20250610_084034_ (08:40:34)
    """
    pattern = re.compile(r'_\d{8}_\d{2}(20|40)\d{2}_')
    
    matches: List[Path] = []
    for p in directory.iterdir():
        if not p.is_file():
            continue
        if p.suffix.lower().lstrip('.') not in exts:
            continue
        
        if pattern.search(p.name):
            matches.append(p)
    
    return matches


def rename_files_remove_hash(directory: Path, exts: Set[str], dry_run: bool = True) -> int:
    """
    เปลี่ยนชื่อไฟล์โดยลบ hash ออก
    จาก: 62fb71e-5_20250517_000034_panorama.jpg
    เป็น: 5_20250517_000034_panorama.jpg
    """
    # Pattern: ตรวจจับ hash-number_ ที่ต้องการลบออก
    # ตัวอย่าง: 62fb71e-5_ หรือ 62ec9ecf-5_
    pattern = re.compile(r'^[a-f0-9]+-(\d+_.+)$', re.IGNORECASE)
    
    renamed = 0
    for p in directory.iterdir():
        if not p.is_file():
            continue
        if p.suffix.lower().lstrip('.') not in exts:
            continue
        
        match = pattern.match(p.name)
        if match:
            # ชื่อใหม่ = เฉพาะส่วนหลัง - (เช่น 5_20250517_000034_panorama.jpg)
            new_name = match.group(1)
            new_path = p.parent / new_name
            
            # ตรวจสอบว่าไฟล์ใหม่มีอยู่แล้วหรือไม่
            if new_path.exists():
                print(f"  ⚠ ข้าม: {p.name} (ไฟล์ {new_name} มีอยู่แล้ว)")
                continue
            
            if dry_run:
                print(f"  {p.name} → {new_name}")
            else:
                try:
                    p.rename(new_path)
                    print(f"  ✓ {p.name} → {new_name}")
                    renamed += 1
                except Exception as e:
                    print(f"  ✗ ไม่สามารถเปลี่ยนชื่อ {p.name}: {e}")
    
    return renamed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ลบรูปภาพที่มีเวลา 20 นาที และ 40 นาที + เปลี่ยนชื่อไฟล์ลบ hash ออก"
    )
    parser.add_argument("--dir", default=r'D:\model_cuu\dataset_method_1\labels', help="โฟลเดอร์เป้าหมาย")
    parser.add_argument("--dry-run", action='store_true', help="แสดงรายการโดยไม่ทำจริง")
    parser.add_argument("--yes", action='store_true', help="ข้ามการยืนยันและดำเนินการทันที")
    parser.add_argument(
        "--exts", 
        default='jpg,jpeg,png,bmp,tif,tiff,webp,txt', 
        help="นามสกุลไฟล์ (คั่นด้วยจุลภาค)"
    )
    parser.add_argument(
        "--skip-delete", 
        action='store_true', 
        help="ข้ามการลบไฟล์ (ทำเฉพาะเปลี่ยนชื่อ)"
    )
    parser.add_argument(
        "--skip-rename", 
        action='store_true', 
        help="ข้ามการเปลี่ยนชื่อ (ทำเฉพาะลบไฟล์)"
    )

    args = parser.parse_args()

    target_dir = Path(args.dir)
    if not target_dir.exists() or not target_dir.is_dir():
        print(f"Error: ไม่พบโฟลเดอร์: {target_dir}")
        return

    exts = set([e.strip().lower() for e in args.exts.split(',') if e.strip()])
    
    # ============================================
    # ส่วนที่ 1: เปลี่ยนชื่อไฟล์ (ลบ hash)
    # ============================================
    if not args.skip_rename:
        print("=" * 60)
        print("ส่วนที่ 1: เปลี่ยนชื่อไฟล์ (ลบ hash ออกจากชื่อไฟล์)")
        print("=" * 60)
        print()
        
        renamed = rename_files_remove_hash(target_dir, exts, dry_run=args.dry_run)
        
        if args.dry_run:
            print()
            print("Dry-run mode: ไม่มีการเปลี่ยนชื่อจริง")
        else:
            if not args.yes:
                print()
                confirm = input("ดำเนินการเปลี่ยนชื่อไฟล์? พิมพ์ 'yes': ")
                if confirm.strip().lower() != 'yes':
                    print("ยกเลิก")
                    return
            
            print()
            print("กำลังเปลี่ยนชื่อไฟล์...")
            renamed = rename_files_remove_hash(target_dir, exts, dry_run=False)
            print(f"\n✓ เปลี่ยนชื่อสำเร็จ {renamed} ไฟล์")
        
        print()
    
    # ============================================
    # ส่วนที่ 2: ลบไฟล์เวลา 20 และ 40 นาที
    # ============================================
    # if not args.skip_delete:
    #     print("=" * 60)
    #     print("ส่วนที่ 2: ลบไฟล์ที่มีเวลา 20 นาที และ 40 นาที")
    #     print("=" * 60)
    #     print()
        
    #     matches = find_non_hourly_images(target_dir, exts)

    #     if not matches:
    #         print("✓ ไม่พบไฟล์ที่ต้องลบ")
    #     else:
    #         print(f"พบไฟล์ที่จะลบ {len(matches)} ไฟล์:")
    #         print()
            
    #         for p in matches:
    #             match = re.search(r'_\d{8}_(\d{6})_', p.name)
    #             time_str = match.group(1) if match else "N/A"
    #             hh = time_str[0:2]
    #             mm = time_str[2:4]
    #             ss = time_str[4:6]
    #             print(f" - {p.name} (เวลา: {hh}:{mm}:{ss})")

    #         if args.dry_run:
    #             print()
    #             print("Dry-run mode: ไม่มีการลบไฟล์")
    #         else:
    #             print()
    #             if not args.yes:
    #                 confirm = input("ยืนยันการลบไฟล์? พิมพ์ 'yes': ")
    #                 if confirm.strip().lower() != 'yes':
    #                     print("ยกเลิก")
    #                     return

    #             deleted = 0
    #             failed = 0
    #             for p in matches:
    #                 try:
    #                     p.unlink()
    #                     deleted += 1
    #                 except Exception as e:
    #                     print(f"✗ ลบไม่สำเร็จ {p.name}: {e}")
    #                     failed += 1

    #             print()
    #             print(f"✓ ลบสำเร็จ {deleted} ไฟล์")
    #             if failed > 0:
    #                 print(f"✗ ลบไม่สำเร็จ {failed} ไฟล์")


if __name__ == '__main__':
    main()