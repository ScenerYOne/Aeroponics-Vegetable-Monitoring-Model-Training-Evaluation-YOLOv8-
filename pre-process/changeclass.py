import os
import glob
import sys

# ตั้งค่า encoding เป็น utf-8
sys.stdout.reconfigure(encoding='utf-8')

def remap_yolo_labels(folder_path, mapping_dict):
    """
    ฟังก์ชันแก้เลข Class ID ให้ตรงกับตารางมาตรฐาน (Master Index)
    """
    if not os.path.exists(folder_path):
        print(f"❌ ไม่พบโฟลเดอร์: {folder_path}")
        return

    txt_files = glob.glob(os.path.join(folder_path, '*.txt'))
    print(f"📂 กำลังประมวลผล {len(txt_files)} ไฟล์ ในโฟลเดอร์: {folder_path}")

    count_changed_files = 0
    
    for txt_file in txt_files:
        new_lines = []
        file_changed = False
        
        with open(txt_file, 'r') as f:
            lines = f.readlines()
            
        for line in lines:
            parts = line.strip().split()
            if len(parts) > 0:
                try:
                    old_id = int(parts[0])
                    
                    # ตรวจสอบว่าต้องเปลี่ยน ID นี้หรือไม่
                    if old_id in mapping_dict:
                        new_id = mapping_dict[old_id]
                        
                        # ถ้าเลขเปลี่ยน ให้ทำการแก้ไข
                        if new_id != old_id:
                            parts[0] = str(new_id)
                            file_changed = True
                        
                        # สร้างบรรทัดใหม่
                        new_lines.append(" ".join(parts) + "\n")
                    else:
                        # ถ้าคลาสไหนไม่มีในกฎ (เช่น อาจจะเป็นขยะหรือ error) ให้คงเดิมไว้
                        new_lines.append(line)
                        
                except ValueError:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        # บันทึกไฟล์ทับเมื่อมีการเปลี่ยนแปลง
        if file_changed:
            with open(txt_file, 'w') as f:
                f.writelines(new_lines)
            count_changed_files += 1

    print(f"✅ แก้ไขเสร็จสิ้น! จำนวน {count_changed_files} ไฟล์")
    print("-" * 50)



target_folder = r'D:\model_cuu\dataset_method_1\labels' 

# กฎการแปลง (Mapping Rules) ยึดตามรูปภาพที่คุณส่งมา
mapping_rules = {
    # Old_ID (จากไฟล์ data1) : New_ID (ตามตารางมาตรฐาน)
    0: 0,  # Italian -> Italian
    1: 3,  # Red Coral -> Red Coral (Index 3)
    2: 4,  # Caramel Romaine -> Caramel Romaine (Index 4)
    3: 5,  # No sponge -> Empty (Index 5)
}



if __name__ == "__main__":
    print(f"=== เริ่มปรับปรุง Class ID ให้ตรงกับตารางมาตรฐาน ===")
    remap_yolo_labels(target_folder, mapping_rules)