import os
import shutil
import random
from ultralytics import YOLO
import report_utils  
import sys

sys.stdout.reconfigure(encoding='utf-8')

dataset_root = r'D:\model_cuu\dataset'  
epochs = 100


def auto_split_data(base_path):
    img_dir = os.path.join(base_path, 'images')
    lbl_dir = os.path.join(base_path, 'labels')

    if os.path.exists(os.path.join(img_dir, 'train')):
        print(" พบโฟลเดอร์ train/val/test แล้ว ข้ามขั้นตอนการแบ่งไฟล์...")
        return
    print(" ยังไม่พบโฟลเดอร์ train... กำลังเริ่มแบ่งไฟล์ (70/15/15)...")
    images = [f for f in os.listdir(img_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]

    if not images:
        print(" ไม่พบรูปภาพในโฟลเดอร์ images (หรืออาจจะแบ่งไปแล้ว)")
        return
    random.shuffle(images)

    total = len(images)
    end_train = int(total * 0.70)
    end_val = end_train + int(total * 0.15)

    splits = {
        'train': images[:end_train],
        'val': images[end_train:end_val],
        'test': images[end_val:]
    }

    for mode, files in splits.items():
        d_img = os.path.join(img_dir, mode)
        d_lbl = os.path.join(lbl_dir, mode)
        os.makedirs(d_img, exist_ok=True)
        os.makedirs(d_lbl, exist_ok=True)
        for f in files:
            src_img = os.path.join(img_dir, f)
            dst_img = os.path.join(d_img, f)
            shutil.move(src_img, dst_img)
            txt_name = os.path.splitext(f)[0] + '.txt'
            src_txt = os.path.join(lbl_dir, txt_name)
            dst_txt = os.path.join(d_lbl, txt_name)
            if os.path.exists(src_txt):
                shutil.move(src_txt, dst_txt)
            else:
                pass
    print(f" แบ่งไฟล์เสร็จสิ้น: Train={len(splits['train'])}, Val={len(splits['val'])}, Test={len(splits['test'])}")


if __name__ == '__main__':
    print(f"--- GPU Check: device='0' (NVIDIA) ---")
    if os.path.exists(dataset_root):
        auto_split_data(dataset_root)
    else:
        print(f"Error: ไม่พบโฟลเดอร์ {dataset_root}")
        exit()

    yaml_path = os.path.join(dataset_root, 'data.yaml')

    if not os.path.exists(yaml_path):
        print(f"Error: ไม่พบไฟล์ data.yaml ที่ {yaml_path}")
        print("กรุณาสร้างไฟล์ data.yaml ตามขั้นตอนก่อนหน้าก่อนเริ่มเทรน")
        exit()
    print(f"Using Data Config: {yaml_path}")

    model = YOLO(r'training_logs\training_20251127_232007\models\best.pt')
    try:
        results = model.train(
            data=yaml_path,
            epochs=epochs,
            batch=16,
            imgsz=640,
            device='0',      
            patience=50,    
            save=True,
            project='runs/train',
            name='my_lettuce_model',
            verbose=True,
            plots=True      
        )

        save_dir_str = str(results.save_dir)
        best_pt_path = os.path.join(save_dir_str, 'weights', 'best.pt')

        try:
            print("--- Generating Report ---")
            log_dir = report_utils.create_log_directory()

            summary = report_utils.save_results(save_dir_str, log_dir, best_pt_path)
            report_utils.generate_text_report(log_dir, {'Epochs': epochs, 'Device': 'GPU'}, summary)
            print(f"Report generated at: {{log_dir}}")
        except Exception as e:
            print(f" Report generation failed (ข้ามได้): {{e}}")


        print(f"--- Exporting to ONNX form: {{best_pt_path}} ---")

        best_model = YOLO(best_pt_path)
        best_model.export(format='onnx')

        print(" เสร็จสมบูรณ์! เช็คผลลัพธ์ได้ที่โฟลเดอร์ runs/train")

    except Exception as e:
        print(f"\n เกิดข้อผิดพลาดขณะเทรน: {{e}}")
        print("คำแนะนำ: ลองเช็คไฟล์ data.yaml อีกครั้งว่า path: ถูกต้องหรือไม่")

        try:
            print("--- Generating Report ---")
            log_dir = report_utils.create_log_directory()
            summary = report_utils.save_results(save_dir_str, log_dir, best_pt_path)
            report_utils.generate_text_report(log_dir, {'Epochs': epochs, 'Device': 'GPU'}, summary)
            print(f"Report generated at: {log_dir}")
        except Exception as e:
            print(f" Report generation failed (ข้ามได้): {e}")

        # ONNX 
        print(f"--- Exporting to ONNX form: {best_pt_path} ---")

        best_model = YOLO(best_pt_path)
        best_model.export(format='onnx')

        print("เสร็จสมบูรณ์! เช็คผลลัพธ์ได้ที่โฟลเดอร์ runs/train")

    except Exception as e:

        print(f"\n เกิดข้อผิดพลาดขณะเทรน: {e}")