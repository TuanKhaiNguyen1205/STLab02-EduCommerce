# STLab02 EduCommerce – 22 test cases (5 requirements)

Phạm vi: REQ-02, REQ-04, REQ-09, REQ-10, REQ-12. Không chọn REQ-06, REQ-08, REQ-11.

## Đổi mới
- Bổ sung `TC-02-005`: `qty=true` cho REQ-02 Cart, expected `INVALID_QUANTITY`, `qty=0`, `lines=0`.
- Source `ecommerce_app.py` là baseline không chỉnh sửa; Python `bool` được coi là `int` trong `isinstance`, dẫn đến FAIL thật.
- 22 test cases: **21 PASS, 1 FAIL, 0 BLOCKED**. Mọi báo cáo đã được chạy lại từ cùng nguồn CSV.

## Chạy lại
1. Colab: mở `STLab02_EduCommerce_Synced.ipynb`, chọn Runtime > Run all. Notebook tự tạo các file.
2. Local: `pip install pandas openpyxl matplotlib gradio` rồi `python test_runner.py`.
3. Kiểm tra `reports/test_execution.csv`, `reports/test_report.xlsx`, `reports/test_dashboard.html`.

## Lưu ý khi nộp
Bổ sung thông tin sinh viên, ảnh E01–E10 chụp trực tiếp trên Colab và liên kết GitHub. Không đưa lỗi mô phỏng thành lỗi thật.
