# SpaceX Falcon 9 First Stage Landing Prediction

Dự án IBM Applied Data Science Capstone, xây dựng và chạy ngày 09/10/2026.

## Chạy trên Windows PowerShell

```powershell
cd SpaceX-Falcon9-Capstone
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python pipeline.py
python spacex_dash_app.py
```

Mở dashboard tại http://127.0.0.1:8050. Mở results/launch_map.html bằng trình duyệt. Notebook nằm trong notebooks/ và đã có kết quả thực thi. Mở notebook từ thư mục dự án hoặc notebooks/.

## Nguồn dữ liệu và phạm vi

- data/api_snapshot.json: 107 bản ghi trong bản phản hồi SpaceX API lưu trữ của IBM. Nguồn: https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/IBM-DS0321EN-SkillsNetwork/datasets/API_call_spacex_api.json . API trực tiếp trả HTTP 525 khi thực hiện dự án. Không tuyên bố đây là dữ liệu trực tiếp mới nhất.
- dataset_part_1.csv và dataset_part_2.csv: bộ CSV đã được IBM làm giàu, 90 lần phóng Falcon 9. Dự án tái tạo nhãn từ Outcome và xác nhận trùng khớp part_2. Không tuyên bố đã tái tạo toàn bộ bước làm giàu các ID API qua endpoint đang lỗi.
- spacex_launch_geo.csv và spacex_launch_dash.csv: bộ dữ liệu độc lập, 56 bản ghi cho các bài lab tương tác. Không ghép các bộ này để tính chung tỷ lệ.
- Wikipedia: HTML thực tế cho bảng 2010-2019, chứa cả Falcon Heavy và dòng chú thích. Dự án thu thập bảng, lưu HTML/CSV và tách riêng khỏi tập huấn luyện.
- CSV nguồn IBM: https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/IBM-DS0321EN-SkillsNetwork/datasets/ . Từng URL, SHA256 và số hàng nằm trong results/data_provenance.json.

Class 1 trong tập mô hình: Outcome không thuộc False ASDS, False Ocean, False RTLS, None ASDS, None None. Class 0 gồm kết quả không thành công, chưa xác định hoặc không có hạ cánh. Mission success trong API KHÁC landing_success. PayloadMass trong CSV tham chiếu đã bao gồm xử lý thiếu upstream của lab; không suy diễn số giá trị thiếu ban đầu.

## Kết quả thực tế

90 bản ghi: 60 Class 1, 30 Class 0. Train 72, test 18. Seed 42, stratified split, fivefold CV trên train. Fit imputer, scaler và encoder bên trong từng fold. SVM được chọn theo CV accuracy 0.888571. Cả bốn mô hình đạt test accuracy 0.777778. Confusion matrix SVM [[2,4],[0,12]]. Đây là protocol độc lập, không sao chép đáp án cũ của lab. 18 mẫu test chưa đủ để khẳng định khả năng triển khai.

Loại Outcome/LandingPad để giảm rò rỉ nhãn và loại ReusedCount vì có thể chứa lịch sử tái sử dụng sau thời điểm dự đoán. Dữ liệu quá khứ vẫn có thể có vấn đề về thời điểm ghi nhận đặc trưng. Chưa đánh giá bằng chronological holdout.

## Cấu trúc

- notebooks/: 8 notebook có code và output thực thi.
- pipeline.py: thu thập bản lưu IBM, web scraping, wrangling, EDA, SQL, Folium, modeling.
- spacex_dash_app.py: dropdown địa điểm và payload slider.
- results/: CSV kết quả, truy vấn SQL, SQLite, bản đồ, hình và số liệu mô hình.
- build_report.py: tạo lại báo cáo PDF từ kết quả.
- Data_Science_Capstone_Project_Report.pdf: báo cáo tiếng Anh dạng slide.

## GitHub và nộp bài

1. Tạo repository public tên SpaceX-Falcon9-Capstone trên GitHub.
2. Giải nén ZIP và upload nội dung bên trong thư mục dự án, không chỉ upload ZIP.
3. Sao chép URL repository vào repository_url.txt.
4. Chạy `python build_report.py` để URL xuất hiện trong báo cáo và trên các slide phương pháp.
5. Kiểm tra PDF, điền tên người thực hiện nếu muốn, rồi nộp PDF và URL theo đề bài.

Báo cáo hiện chưa có URL GitHub thật, nên chưa đủ tiêu chí liên kết repository. Không có repository được tạo hoặc đẩy lên tài khoản của bạn tự động.

## Giới hạn bản đồ/dashboard

Khoảng cách bờ biển dùng điểm chọn thủ công gần CCAFS SLC-40 và công thức Haversine. Không phải khoảng cách ngắn nhất tới coastline và không chứng minh nguyên nhân chọn địa điểm. Bản đồ cần mạng để tải tiles/CDN. All-sites pie hiển thị số lượt Class 1 theo địa điểm, không phải xếp hạng success rate.
