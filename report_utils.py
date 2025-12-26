import os
import json
import shutil
import pandas as pd
from datetime import datetime

def create_log_directory(base_path='training_logs'):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_dir = os.path.join(base_path, f'training_{timestamp}')
    
    os.makedirs(os.path.join(log_dir, 'plots'), exist_ok=True)
    os.makedirs(os.path.join(log_dir, 'metrics'), exist_ok=True)
    os.makedirs(os.path.join(log_dir, 'models'), exist_ok=True)
    
    return log_dir

def save_results(source_run_dir, log_dir, model_path):
    files_to_copy = [
        'results.png', 'confusion_matrix.png', 'confusion_matrix_normalized.png',
        'F1_curve.png', 'PR_curve.png', 'P_curve.png', 'R_curve.png', 
        'results.csv'
    ]
    
    for file in files_to_copy:
        src = os.path.join(source_run_dir, file)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(log_dir, 'plots', file))

    if os.path.exists(model_path):
        shutil.copy2(model_path, os.path.join(log_dir, 'models', 'best.pt'))

    results_csv = os.path.join(source_run_dir, 'results.csv')
    summary_data = {}
    
    if os.path.exists(results_csv):
        try:
            df = pd.read_csv(results_csv)
            df.columns = [c.strip() for c in df.columns]
            
            best_idx = df['metrics/mAP50(B)'].idxmax()
            
            summary_data = {
                'best_epoch': int(df.iloc[best_idx]['epoch']),
                'mAP50': float(df.iloc[best_idx]['metrics/mAP50(B)']),
                'mAP50-95': float(df.iloc[best_idx]['metrics/mAP50-95(B)']),
                'precision': float(df.iloc[best_idx]['metrics/precision(B)']),
                'recall': float(df.iloc[best_idx]['metrics/recall(B)']),
                'train_box_loss': float(df.iloc[-1]['train/box_loss']),
                'val_box_loss': float(df.iloc[-1]['val/box_loss'])
            }
            
            with open(os.path.join(log_dir, 'metrics', 'summary.json'), 'w') as f:
                json.dump(summary_data, f, indent=4)
        except:
            pass
            
    return summary_data

def generate_text_report(log_dir, config, summary_data):
    report_path = os.path.join(log_dir, 'TRAINING_REPORT.txt')
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("="*50 + "\n")
        f.write("YOLOv8 TRAINING REPORT\n")
        f.write("="*50 + "\n\n")
        
        f.write("1. CONFIGURATION\n")
        f.write("-" * 30 + "\n")
        for k, v in config.items():
            f.write(f"{k}: {v}\n")
        f.write("\n")
        
        f.write("2. BEST PERFORMANCE METRICS\n")
        f.write("-" * 30 + "\n")
        if summary_data:
            f.write(f"Best Result at Epoch: {summary_data.get('best_epoch')}\n")
            f.write(f"mAP50       : {summary_data.get('mAP50'):.4f}\n")
            f.write(f"mAP50-95    : {summary_data.get('mAP50-95'):.4f}\n")
            f.write(f"Precision   : {summary_data.get('precision'):.4f}\n")
            f.write(f"Recall      : {summary_data.get('recall'):.4f}\n")
            f.write(f"Final Loss  : {summary_data.get('train_box_loss'):.4f}\n")
        else:
            f.write("No metrics data found.\n")
            
        f.write("\n" + "="*50 + "\n")
        f.write(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")