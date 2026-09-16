"""
Generates synthetic sample medical bill images for testing and demonstration.
"""
import os
import cv2
import numpy as np


def generate_samples(output_dir: str):
    os.makedirs(output_dir, exist_ok=True)

    # 1. Clean Receipt Image
    img_clean = np.ones((250, 700, 3), dtype=np.uint8) * 255
    cv2.putText(img_clean, "APOLLO HOSPITALS BILLING", (40, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (20, 20, 20), 2)
    cv2.putText(img_clean, "Consultation: 500  |  Pharmacy: 700", (40, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (50, 50, 50), 2)
    cv2.putText(img_clean, "Total: INR 1200 | Paid: 1000 | Due: 200", (40, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 2)
    cv2.putText(img_clean, "Discount: 10%", (40, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (70, 70, 70), 2)
    clean_path = os.path.join(output_dir, "sample_receipt_clean.png")
    cv2.imwrite(clean_path, img_clean)
    print(f"Created: {clean_path}")

    # 2. Noisy / Crumpled Receipt Image (Simulates OCR digit degradation)
    img_noisy = np.ones((250, 700, 3), dtype=np.uint8) * 245
    cv2.putText(img_noisy, "T0tal: Rs l200 | Pald: 1000 | Due: 200", (40, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (30, 30, 30), 2)
    # Add simulated paper crumple noise & line folds
    cv2.line(img_noisy, (20, 30), (680, 220), (210, 210, 210), 2)
    cv2.line(img_noisy, (50, 200), (650, 50), (220, 220, 220), 1)
    noise = np.random.normal(0, 8, img_noisy.shape).astype(np.int16)
    img_noisy = np.clip(img_noisy.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    noisy_path = os.path.join(output_dir, "sample_receipt_ocr_noise.png")
    cv2.imwrite(noisy_path, img_noisy)
    print(f"Created: {noisy_path}")

    # 3. Unreadable Noisy Image (Triggers Guardrail)
    img_unreadable = np.random.randint(100, 200, (200, 400, 3), dtype=np.uint8)
    for _ in range(15):
        pt1 = (np.random.randint(0, 400), np.random.randint(0, 200))
        pt2 = (np.random.randint(0, 400), np.random.randint(0, 200))
        cv2.line(img_unreadable, pt1, pt2, (60, 60, 60), 2)
    unreadable_path = os.path.join(output_dir, "sample_unreadable.png")
    cv2.imwrite(unreadable_path, img_unreadable)
    print(f"Created: {unreadable_path}")


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    generate_samples(current_dir)
