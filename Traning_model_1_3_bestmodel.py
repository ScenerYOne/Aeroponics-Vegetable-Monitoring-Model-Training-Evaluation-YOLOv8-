import os
import shutil
import random
from ultralytics import YOLO
import report_utils 
import sys

sys.stdout.reconfigure(encoding='utf-8')

dataset_root = r'D:\model_cuu\dataset'  
additional_datasets = [r'D:\model_cuu\dataset_method_1'] 
epochs = 100


def auto_split_data(base_path, extra_paths=[]):

    def distribute(files, src_img, src_lbl, dst_base, move_files=False):
        if not files: return
        total = len(files)
        end_train = int(total * 0.70)
        end_val = end_train + int(total * 0.15)
        splits = {'train': files[:end_train], 'val': files[end_train:end_val], 'test': files[end_val:]}
        
        for mode, f_list in splits.items():
            d_img = os.path.join(dst_base, 'images', mode)
            d_lbl = os.path.join(dst_base, 'labels', mode)
            os.makedirs(d_img, exist_ok=True)
            os.makedirs(d_lbl, exist_ok=True)
            for f in f_list:
                s_i = os.path.join(src_img, f)
                d_i = os.path.join(d_img, f)
                if os.path.exists(d_i): continue
                if move_files: shutil.move(s_i, d_i)
                else: shutil.copy2(s_i, d_i)
                
                txt = os.path.splitext(f)[0] + '.txt'
                s_t = os.path.join(src_lbl, txt)
                d_t = os.path.join(d_lbl, txt)
                if os.path.exists(s_t) and not os.path.exists(d_t):
                    if move_files: shutil.move(s_t, d_t)
                    else: shutil.copy2(s_t, d_t)

    for p in extra_paths:
        if not os.path.exists(p): continue
        print(f" Processing extra dataset: {p}")
        i_dir = os.path.join(p, 'images')
        l_dir = os.path.join(p, 'labels')
        if os.path.exists(i_dir):
            imgs = [f for f in os.listdir(i_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
            random.shuffle(imgs)
            distribute(imgs, i_dir, l_dir, base_path, move_files=False)

    img_dir = os.path.join(base_path, 'images')
    lbl_dir = os.path.join(base_path, 'labels')

    if os.path.exists(img_dir):
        images = [f for f in os.listdir(img_dir) if os.path.isfile(os.path.join(img_dir, f)) and f.lower().endswith(('.jpg', '.png', '.jpeg'))]
        if images:
            print(f" Found {len(images)} unsorted images in {base_path}. Splitting...")
            random.shuffle(images)
            distribute(images, img_dir, lbl_dir, base_path, move_files=True)
        else:
            print(" No unsorted images found in base dataset root.")
    
    print(f" Dataset preparation complete.")


if __name__ == '__main__':
    print(f"--- GPU Check: device='0' (NVIDIA) ---")
    if os.path.exists(dataset_root):
        auto_split_data(dataset_root, additional_datasets)
    else:
        print(f"Error: ไม่พบโฟลเดอร์ {dataset_root}")
        exit()

    yaml_path = os.path.join(dataset_root, 'data.yaml')

    if not os.path.exists(yaml_path):
        print(f"Error: ไม่พบไฟล์ data.yaml ที่ {yaml_path}")
        print("กรุณาสร้างไฟล์ data.yaml ตามขั้นตอนก่อนหน้าก่อนเริ่มเทรน")
        exit()
    print(f"Using Data Config: {yaml_path}")

    # เทรนโมเดล
    model = YOLO(r'D:\model_cuu\runs\train\my_lettuce_model_1_34\weights\best.pt')  
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
            name='my_lettuce_model_1_3',
            verbose=True,
            plots=True,  
            optimizer='AdamW',  
            lr0=0.001,          
            lrf=0.01,           
            cos_lr=True,        
            warmup_epochs=3.0,
        )

    
        save_dir_str = str(results.save_dir)
        best_pt_path = os.path.join(save_dir_str, 'weights', 'best.pt')

        # 4. สร้าง Report
        try:
            print("--- Generating Report ---")
            log_dir = report_utils.create_log_directory()

            summary = report_utils.save_results(save_dir_str, log_dir, best_pt_path)
            report_utils.generate_text_report(log_dir, {'Epochs': epochs, 'Device': 'GPU'}, summary)
            print(f"Report generated at: {{log_dir}}")
        except Exception as e:
            print(f" Report generation failed (ข้ามได้): {{e}}")

        # Export ONNX (แก้จุดที่ Error แล้ว)
        print(f"--- Exporting to ONNX form: {{best_pt_path}} ---")

        # โหลดโมเดลจากไฟล์ best.pt ที่ถูกต้อง
        best_model = YOLO(best_pt_path)
        best_model.export(format='onnx')

        print(" เสร็จสมบูรณ์ เช็คผลลัพธ์ได้ที่โฟลเดอร์ runs/train")

    except Exception as e:
        print(f"\n เกิดข้อผิดพลาดขณะเทรน: {{e}}")
        print("คำแนะนำ: ลองเช็คไฟล์ data.yaml อีกครั้งว่า path: ถูกต้องหรือไม่")

        # 4. สร้าง Report
        try:
            print("--- Generating Report ---")
            log_dir = report_utils.create_log_directory()
            summary = report_utils.save_results(save_dir_str, log_dir, best_pt_path)
            report_utils.generate_text_report(log_dir, {'Epochs': epochs, 'Device': 'GPU'}, summary)
            print(f"Report generated at: {log_dir}")
        except Exception as e:
            print(f" Report generation failed (ข้ามได้): {e}")

        # Export ONNX (แก้จุดที่ Error แล้ว)
        print(f"--- Exporting to ONNX form: {best_pt_path} ---")

        # โหลดโมเดลจากไฟล์ best.pt ที่ถูกต้อง
        best_model = YOLO(best_pt_path)
        best_model.export(format='onnx')

        print(" เสร็จสมบูรณ์ เช็คผลลัพธ์ได้ที่โฟลเดอร์ runs/train")

    except Exception as e:
        print(f"\n เกิดข้อผิดพลาดขณะเทรน: {e}")
