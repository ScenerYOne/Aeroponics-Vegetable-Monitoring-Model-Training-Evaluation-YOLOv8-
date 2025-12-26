import os
import glob
from collections import Counter
import sys

# ตั้งค่า encoding เพื่อให้แสดงผลภาษาไทยได้
sys.stdout.reconfigure(encoding='utf-8')

def check_multiple_folders(folder_list):
    # กำหนดชื่อ Class ตามเป้าหมาย (0-5)
    class_names = {
        0: "Italian",
        1: "Deer Tongue",
        2: "Green Lollo Rossa",
        3: "Red Coral",
        4: "Caramel Romaine",
        5: "Empty"
    }

    total_counts = Counter()
    total_files = 0
    global_errors = []

    print(f"{'='*60}")
    print(f"🕵️‍♂️  เริ่มการตรวจสอบ Class ID ใน {len(folder_list)} โฟลเดอร์")
    print(f"{'='*60}\n")

    for folder_path in folder_list:
        if not os.path.exists(folder_path):
            print(f"❌ ไม่พบโฟลเดอร์: {folder_path}")
            continue

        print(f"📂 กำลังตรวจสอบโฟลเดอร์: {folder_path}")
        
        txt_files = glob.glob(os.path.join(folder_path, '*.txt'))
        folder_counts = Counter()
        folder_errors = []
        
        for txt_file in txt_files:
            try:
                with open(txt_file, 'r') as f:
                    lines = f.readlines()
                    
                for line in lines:
                    parts = line.strip().split()
                    if len(parts) > 0:
                        class_id = int(parts[0])
                        
                        # เก็บสถิติ
                        folder_counts[class_id] += 1
                        total_counts[class_id] += 1
                        
                        # เช็ค Error (ถ้านอกเหนือจาก 0-5)
                        if class_id not in class_names:
                            err_msg = f"{os.path.basename(txt_file)} (ID: {class_id})"
                            folder_errors.append(err_msg)
                            global_errors.append(f"[{folder_path}] {err_msg}")
                            
            except Exception as e:
                print(f"   ❌ อ่านไฟล์ไม่ได้: {txt_file}")

        # สรุปของโฟลเดอร์นี้
        print(f"   - จำนวนไฟล์: {len(txt_files)}")
        if folder_errors:
            print(f"   ⚠️  พบ ID ผิดปกติ {len(folder_errors)} จุด!")
        else:
            print(f"   ✅ โฟลเดอร์นี้ถูกต้อง (Clean)")
        print("-" * 30)
        total_files += len(txt_files)

    # ==========================================
    # สรุปภาพรวมทั้งหมด (Grand Total)
    # ==========================================
    print(f"\n{'='*60}")
    print(f"📊 สรุปยอดรวมทั้งหมด (Grand Total)")
    print(f"{'='*60}")
    print(f"{'ID':<5} {'Class Name':<20} {'Count':<10}")
    print("-" * 40)
    
    # --- จุดที่แก้ไข: วนลูปตามรายชื่อ Class ทั้งหมด (0-5) ---
    # เพื่อให้แสดง Class ที่มีค่าเป็น 0 ด้วย
    all_class_ids = sorted(class_names.keys())
    
    for cls_id in all_class_ids:
        name = class_names[cls_id]
        # ดึงค่า count ถ้าไม่มีให้เป็น 0
        count = total_counts.get(cls_id, 0) 
        print(f"{cls_id:<5} {name:<20} {count:<10}")
        
    # เช็คเผื่อมี ID ประหลาด (Unknown) ที่ไม่อยู่ใน 0-5 โผล่มา
    unknown_ids = set(total_counts.keys()) - set(class_names.keys())
    for unknown_id in unknown_ids:
        print(f"{unknown_id:<5} {'UNKNOWN !!!':<20} {total_counts[unknown_id]:<10}")

    print("-" * 40)
    print(f"รวมไฟล์ทั้งหมด: {total_files} ไฟล์")
    
    if global_errors:
        print(f"\n🚨 พบไฟล์ที่มี Class ผิดปกติ ({len(global_errors)} เคส):")
        for err in global_errors:
            print(f" - {err}")
    else:
        print(f"\n✨ เยี่ยมมาก! ข้อมูลทั้งหมดถูกต้อง พร้อมเทรน 100%")

# ==========================================
#  ใส่ Path ของโฟลเดอร์ labels ตรงนี้
# ==========================================
folders_to_check = [
    r'D:\model_cuu\dataset_method_1\labels'
]

# รันโปรแกรม
check_multiple_folders(folders_to_check)