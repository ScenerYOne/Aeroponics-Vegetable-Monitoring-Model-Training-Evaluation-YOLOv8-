from ultralytics import YOLO
import sys

def main():
    sys.stdout.reconfigure(encoding='utf-8')

    model_path = r'D:\model_cuu\training_logs\training_20251205_232546\models\best.pt' 
    yaml_path = r'D:\model_cuu\dataset\data.yaml'


    model = YOLO(model_path)

    print(f"--- กำลังตรวจสอบความแม่นยำจากโมเดล: {model_path} ---")

    metrics = model.val(
        data=yaml_path, 
        split='test',   
        imgsz=640, 
        batch=16, 
        device='0',     
        plots=True,      
        conf=0.25       
    )

    print("\n--- สรุปผลลัพธ์ ---")
    print(f"mAP50: {metrics.box.map50}")
    print(f"mAP50-95: {metrics.box.map}")

if __name__ == '__main__':
    main()