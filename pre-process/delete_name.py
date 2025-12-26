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

def rename_files_clean_format(directory: Path, exts: Set[str], dry_run: bool = True) -> int:
    """
    1. ตัดส่วนที่เป็น .rf.xxxxx ออก
    2. ตัดส่วนเกินตรงกลางออก (เช่น 5_05-17_5_2025... -> 5_2025...)
    """
    renamed = 0
    
    # Regex สำหรับจับ pattern: เลขหน้า_ขยะตรงกลาง_วันเวลา...
    # Group 1 = เลขหน้า (เช่น 5)
    # Group 2 = ตั้งแต่วันเวลาเป็นต้นไป (เช่น 20250517_000334_panorama.jpg)
    # ความหมาย: หาตัวเลขหน้าสุด (_) อะไรก็ได้ตรงกลาง (_) แล้วตามด้วย วันที่_เวลา
    shorten_pattern = re.compile(r'^(\d+)_.+?_(\d{8}_\d{6}_panorama.*)$')

    for p in directory.iterdir():
        if not p.is_file(): continue
        
        # กรองเฉพาะนามสกุลที่กำหนด
        if p.suffix.lower().lstrip('.') not in exts and ".rf." not in p.name:
            continue

        current_name = p.name
        
        # -------------------------------------------------
        # Step A: ตัด .rf. ทิ้ง (Clean Roboflow)
        # -------------------------------------------------
        if ".rf." in current_name:
            current_name = current_name.split(".rf.")[0]
            
            # คืนค่าตามนามสกุลที่ถูกต้องตามประเภทโฟลเดอร์
            if directory.name == 'labels':
                # ถ้าอยู่ใน folder labels ต้องเป็น .txt เสมอ
                if not current_name.endswith(".txt"):
                    current_name = Path(current_name).stem + ".txt"
            else:
                # ถ้าเป็น images ให้เป็น .jpg (หรือนามสกุลเดิม)
                if current_name.endswith("_jpg"):
                    current_name = current_name[:-4] + ".jpg"
                elif current_name.endswith("_png"):
                    current_name = current_name[:-4] + ".png"
            

        # -------------------------------------------------
        # Step B: ตัดส่วนกลางที่ยาวเกินไปทิ้ง (Shorten Name)
        # -------------------------------------------------
        # เช็คว่าชื่อเข้าข่าย 5_05-17_5_2025... หรือไม่
        match = shorten_pattern.match(current_name)
        if match:
            # สร้างชื่อใหม่: Group1(เลขหน้า) + "_" + Group2(วันเวลา...)
            # ผลลัพธ์: 5_20250517_000334_panorama.jpg
            current_name = f"{match.group(1)}_{match.group(2)}"

        # -------------------------------------------------
        # Step C: ดำเนินการเปลี่ยนชื่อ
        # -------------------------------------------------
        if current_name != p.name:
            new_path = p.parent / current_name
            
            if new_path.exists():
                print(f"  ⚠ ข้าม: {p.name} (ไฟล์ {current_name} มีอยู่แล้ว)")
                continue
            
            if dry_run:
                print(f"  {p.name} \n    --> {current_name}")
            else:
                try:
                    p.rename(new_path)
                    print(f"  ✓ {p.name} \n    --> {current_name}")
                    renamed += 1
                except Exception as e:
                    print(f"  ✗ ไม่สามารถเปลี่ยนชื่อ {p.name}: {e}")
                    
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
    parser = argparse.ArgumentParser(description="Clean Images & Labels")
    
    # *** ตั้งค่า Default ให้เป็น images และ .jpg ***
    parser.add_argument("--dir", default=r'D:\model_cuu\dataset_method_1\labels', help="โฟลเดอร์เป้าหมาย")
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
    print(f"Extensions: {exts}")

    # 1. เปลี่ยนชื่อไฟล์ (ตัด .rf และ ตัดส่วนกลางทิ้ง)
    print("=" * 60)
    print("ส่วนที่ 1: จัดระเบียบชื่อไฟล์ (5_05-17_... -> 5_2025...)")
    print("=" * 60)
    rename_files_clean_format(target_dir, exts, dry_run=args.dry_run)
    print()
    

if __name__ == '__main__':
    main()