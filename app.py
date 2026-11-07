import streamlit as st
import pandas as pd
import requests
import base64
import json
from datetime import datetime

# Cấu hình giao diện hiển thị trên điện thoại
st.set_page_config(page_title="PC09 - NINH BÌNH", layout="centered", initial_sidebar_state="collapsed")

# --- THÔNG TIN CẤU HÌNH GITHUB API AN TOÀN ---
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]
FILE_PATH = "data_pc09.csv"

# Đường dẫn API chuẩn kết nối đến máy chủ GitHub
API_URL = f"https://github.com{REPO_NAME}/contents/{FILE_PATH}"

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# Hàm đọc dữ liệu từ file CSV trên GitHub về App
def load_data_from_github():
    try:
        response = requests.get(API_URL, headers=headers, timeout=10)
        if response.status_code == 200:
            file_json = response.json()
            content = base64.b64decode(file_json["content"]).decode("utf-8")
            raw_lines = content.strip().split("\n")
            if not raw_lines:
                return pd.DataFrame(), file_json["sha"]
                
            headers_csv = [h.strip() for h in raw_lines[0].split(",")]
            data_rows = []
            for line in raw_lines[1:]:
                if line.strip():
                    data_rows.append([item.strip() for item in line.split(",")])
                    
            df = pd.DataFrame(data_rows, columns=headers_csv)
            return df, file_json["sha"]
        else:
            return pd.DataFrame(), None
    except Exception as e:
        return pd.DataFrame(), None

# Giao diện chính của App trên điện thoại
st.title("🚨 PC09 - CÔNG AN TỈNH NINH BÌNH")
tab1, tab2 = st.tabs(["📝 NHẬP HỒ SƠ", "🔍 TRA CỨU VỤ VIỆC"])

# ==================== TAB 1: NHẬP LIỆU VỤ VIỆC ====================
with tab1:
    st.subheader("Form Nhập Liệu Vụ Việc")
    with st.form("form_nhap", clear_on_submit=True):
        so_vu = st.text_input("Số vụ")
        dia_ban = st.text_input("Địa bàn (Huyện/Xã)")
        noi_xay_ra = st.text_input("Nơi xảy ra")
        ten_vu = st.text_input("Tên vụ việc")
        cq_yeucau = st.text_input("Cơ quan yêu cầu")
        
        st.write("**Hoạt động tiến hành:**")
        cb_hientruong = st.checkbox("Khám nghiệm hiện trường")
        cb_tuthi = st.checkbox("Khám nghiệm tử thi")
        cb_dunglai = st.checkbox("Dựng lại hiện trường")
        
        tinh_chat = st.text_input("Tính chất vụ việc")
        tinh_trang = st.text_input("Tình trạng")
        noi_dung = st.text_area("Nội dung vụ việc")
        dau_vet = st.text_input("Các dấu vết chính")
        tai_lieu = st.text_input("Tài liệu")
        nhan_dinh = st.text_input("Nhận định")
        can_bo = st.text_input("Cán bộ thực hiện")
        cap_kn = st.text_input("Cấp khám nghiệm")
        
        st.write("**Loại dấu vết thu được:**")
        cb_duongvan = st.checkbox("Đường vân")
        cb_congcu = st.checkbox("Dấu vết công cụ")
        cb_mau = st.checkbox("Dấu vết máu")
        
        st.write("**Kết quả khám nghiệm:**")
        cb_kq_tinhchat = st.checkbox("Xác định tính chất vụ việc")
        cb_kq_doituong = st.checkbox("Xác định đối tượng")

        submit_btn = st.form_submit_button(label="CẬP NHẬT LÊN CƠ SỞ DỮ LIỆU", type="primary")

        if submit_btn:
            if not ten_vu or not dia_ban:
                st.warning("Vui lòng nhập đầy đủ Tên vụ việc và Địa bàn!")
            else:
                hoat_dong_list = [k for k, v in {"Khám nghiệm hiện trường": cb_hientruong, "Khám nghiệm tử thi": cb_tuthi, "Dựng lại hiện trường": cb_dunglai}.items() if v]
                loai_dau_vet_list = [k for k, v in {"Đường vân": cb_duongvan, "Dấu vết công cụ": cb_congcu, "Dấu vết máu": cb_mau}.items() if v]
                ket_qua_list = [k for k, v in {"Xác định tính chất vụ việc": cb_kq_tinhchat, "Xác định đối tượng": cb_kq_doituong}.items() if v]
                
                df, sha = load_data_from_github()
                stt_moi = len(df) + 1 if df is not None else 1
                ngay_hien_tai = datetime.now().strftime("%d/%m/%Y")
                
                clean = lambda x: str(x).replace(",", " - ").replace("\n", " ")
                new_line = f"\n{stt_moi},{clean(so_vu)},{clean(dia_ban)},{ngay_hien_tai},{clean(noi_xay_ra)},{clean(ten_vu)},{clean(cq_yeucau)},{clean('; '.join(hoat_dong_list))},{clean(tinh_chat)},{clean(tinh_trang)},{clean(noi_dung)},{clean(dau_vet)},{clean(tai_lieu)},{clean(nhan_dinh)},{clean(can_bo)},{clean(cap_kn)},{clean('; '.join(loai_dau_vet_list))},{clean('; '.join(ket_qua_list))}"
                
                try:
                    response = requests.get(API_URL, headers=headers, timeout=10)
                    if response.status_code == 200:
                        current_content = base64.b64decode(response.json()["content"]).decode("utf-8")
                        updated_content = current_content.strip() + new_line
                        
                        update_data = {
                            "message": f"App di dong them moi STT {stt_moi}",
                            "content": base64.b64encode(updated_content.encode("utf-8")).decode("utf-8"),
                            "sha": sha
                        }
                        
                        put_res = requests.put(API_URL, headers=headers, json=update_data, timeout=10)
                        if put_res.status_code == 200 or put_res.status_code == 201:
                            st.success(f"Thành công! Đã cập nhật vụ việc STT {stt_moi} vào hệ thống.")
                        else:
                            st.error(f"Lỗi ghi dữ liệu lên hệ thống GitHub. Mã lỗi: {put_res.status_code}")
                    else:
                        st.error("Không lấy được dữ liệu gốc để tiến hành đồng bộ!")
                except Exception as ex:
                    st.error(f"Lỗi kết nối mạng: {str(ex)}")

# ==================== TAB 2: TRA CỨU / TÌM KIẾM ====================
with tab2:
    st.subheader("Tìm Kiếm Thông Tin Vụ Việc")
    keyword = st.text_input("Nhập Số vụ, Địa bàn hoặc Tên vụ việc cần tìm...")
    
    if keyword:
        df, _ = load_data_from_github()
        if df is not None and not df.empty:
            result_df = df[df['Tên vụ việc'].astype(str).str.contains(keyword, case=False, na=False) | 
                           df['Số vụ'].astype(str).str.contains(keyword, case=False, na=False) | 
                           df['Địa bàn'].astype(str).str.contains(keyword, case=False, na=False)]
            
            if not result_df.empty:
                st.write(f"Tìm thấy **{len(result_df)}** kết quả phù hợp:")
                for index, row in result_df.iterrows():
                    with st.expander(f"STT: {row['STT']} - Vụ: {row['Tên vụ việc']} ({row['Địa bàn']})"):
                        st.write(f"• **Số vụ:** {row['Số vụ']} | **Ngày khám nghiệm:** {row['Ngày tháng']}")
                        st.write(f"• **Nơi xảy ra:** {row['Nơi xảy ra']}")
                        st.write(f"• **Hoạt động tiến hành:** {row['Hoạt động tiến hành']}")
                        st.write(f"• **Nội dung diễn biến:** {row['Nội dung vụ việc']}")
                        st.write(f"• **Dấu vết thu được:** {row['Loại dấu vết']}")
            else:
                st.info("Không tìm thấy dữ liệu nào trùng khớp.")
