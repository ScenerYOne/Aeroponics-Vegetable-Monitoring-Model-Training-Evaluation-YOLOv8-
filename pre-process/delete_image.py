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

def convert_jpg_labels_to_txt(directory: Path, dry_run: bool = True) -> int:
    """
    ฟังก์ชันพิเศษ: แปลง .jpg เป็น .txt (ใช้เฉพาะในโฟลเดอร์ labels)
    แก้ปัญหาไฟล์ labels ที่ถูกเปลี่ยนนามสกุลผิด
    """
    converted = 0
    for p in directory.iterdir():
        if not p.is_file(): continue
        
        # ถ้าเจอนามสกุล .jpg หรือ .jpeg ให้เปลี่ยนเป็น .txt
        if p.suffix.lower() in ['.jpg', '.jpeg']:
            new_name = p.stem + ".txt" # ใช้ชื่อเดิมแต่เปลี่ยนนามสกุล
            new_path = p.parent / new_name
            
            if new_path.exists():
                print(f"  ⚠ ข้าม: {p.name} (มีไฟล์ {new_name} อยู่แล้ว)")
                continue
                
            if dry_run:
                print(f"  [แก้ JPG->TXT] {p.name} \n             --> {new_name}")
            else:
                try:
                    p.rename(new_path)
                    print(f"  ✓ แก้ไข: {p.name} \n         --> {new_name}")
                    converted += 1
                except Exception as e:
                    print(f"  ✗ แก้ไขไม่ได้ {p.name}: {e}")
    return converted

def delete_rf_files(directory: Path, exts: Set[str], dry_run: bool = True) -> int:
    """
    ลบไฟล์ที่มี .rf. (Roboflow generated files)
    ตัวอย่าง: 5_20250611_030011_panorama.jpg.rf.0e69f1166c...jpg
    """
    deleted = 0
    # Pattern: หาคำว่า .rf. ตามด้วยตัวอักษรภาษาอังกฤษหรือตัวเลข
    # หรือเช็คแค่สตริง ".rf." ก็ครอบคลุมไฟล์จาก Roboflow ส่วนใหญ่
    
    for p in directory.iterdir():
        if not p.is_file(): continue
        
        # เช็คว่ามี .rf. อยู่ในชื่อไฟล์หรือไม่
        if ".rf." in p.name:
            if dry_run:
                print(f"  [ลบ] {p.name}")
            else:
                try:
                    p.unlink()
                    print(f"  ✓ ลบสำเร็จ: {p.name}")
                    deleted += 1
                except Exception as e:
                    print(f"  ✗ ลบไม่ได้ {p.name}: {e}")
                    
    return deleted

def rename_files_clean_format(directory: Path, exts: Set[str], dry_run: bool = True) -> int:
    """
    (ฟังก์ชันเดิม) จัดระเบียบชื่อไฟล์ 5_05-17_... -> 5_2025...
    """
    renamed = 0
    shorten_pattern = re.compile(r'^(\d+)_.+?_(\d{8}_\d{6}_panorama.*)$')

    for p in directory.iterdir():
        if not p.is_file(): continue
        if p.suffix.lower().lstrip('.') not in exts and ".rf." not in p.name: continue

        current_name = p.name
        
        # Step A: ตัด .rf. ทิ้ง (เผื่อกรณีไฟล์ที่รอดจากการลบ หรืออยากแค่เปลี่ยนชื่อ)
        if ".rf." in current_name:
            current_name = current_name.split(".rf.")[0]
            if directory.name == 'labels':
                if not current_name.endswith(".txt"):
                    current_name = Path(current_name).stem + ".txt"
            else:
                if current_name.endswith("_jpg"): current_name = current_name[:-4] + ".jpg"
                elif current_name.endswith("_png"): current_name = current_name[:-4] + ".png"

        # Step B: ตัดส่วนกลางทิ้ง
        match = shorten_pattern.match(current_name)
        if match:
            current_name = f"{match.group(1)}_{match.group(2)}"

        if current_name != p.name:
            new_path = p.parent / current_name
            if new_path.exists():
                # ถ้าไฟล์ปลายทางมีอยู่แล้ว (อาจจะเป็นไฟล์ clean ที่มีอยู่แล้ว)
                # เราอาจจะเลือกลบไฟล์ duplicate นี้ทิ้งแทนการ rename
                if dry_run:
                    print(f"  ⚠ ข้าม (ไฟล์ซ้ำ): {p.name} -> {current_name} มีอยู่แล้ว")
                continue
            
            if dry_run:
                print(f"  [เปลี่ยนชื่อ] {p.name} \n           --> {current_name}")
            else:
                try:
                    p.rename(new_path)
                    print(f"  ✓ เปลี่ยนชื่อ: {p.name} \n           --> {current_name}")
                    renamed += 1
                except Exception as e:
                    print(f"  ✗ Error: {e}")
                    
    return renamed

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
    parser = argparse.ArgumentParser(description="Delete .rf files & Clean names")
    parser.add_argument("--dir", default=r'D:\dele\train\labels', help="โฟลเดอร์เป้าหมาย")
    parser.add_argument("--exts", default='jpg,jpeg,png', help="นามสกุลไฟล์")
    parser.add_argument("--dry-run", action='store_true', help="แสดงรายการโดยไม่ทำจริง")
    parser.add_argument("--yes", action='store_true', help="ยืนยันทำทันที")
    parser.add_argument("--skip-delete", action='store_true', help="ข้ามการลบไฟล์")

    args = parser.parse_args()
    target_dir = Path(args.dir)
    exts = set([e.strip().lower() for e in args.exts.split(',') if e.strip()])

    if not target_dir.exists():
        print(f"Error: ไม่พบโฟลเดอร์: {target_dir}")
        return

    print(f"Target: {target_dir}")

    # ============================================
    # ส่วนที่ 1: ลบไฟล์ขยะที่มี .rf. (สำคัญ! ลบก่อนจัดระเบียบ)
    # ============================================
    if not args.skip_delete:
        print("=" * 60)
        print("ส่วนที่ 1: ลบไฟล์ Duplicate จาก Roboflow (.rf.xxxxx)")
        print("=" * 60)
        delete_rf_files(target_dir, exts, dry_run=args.dry_run)
        print()

    # ============================================
    # ส่วนที่ 2: เปลี่ยนชื่อไฟล์ (Clean Format)
    # ============================================
    print("=" * 60)
    print("ส่วนที่ 2: จัดระเบียบชื่อไฟล์ (5_05-17_... -> 5_2025...)")
    print("=" * 60)
    rename_files_clean_format(target_dir, exts, dry_run=args.dry_run)
    print()
    
if __name__ == '__main__':
    main()