
import streamlit as st
import pandas as pd
import requests
import base64
import io
from datetime import datetime
from zoneinfo import ZoneInfo

# =========================================================
# 1. CẤU HÌNH ỨNG DỤNG
# =========================================================

st.set_page_config(
    page_title="PC09 - NINH BÌNH",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.title("🚨 PC09 - CÔNG AN TỈNH NINH BÌNH")

FILE_PATH = "data_pc09.csv"

# Các cột dữ liệu
COLUMNS = [
    "STT",
    "Số vụ",
    "Địa bàn",
    "Ngày tháng",
    "Nơi xảy ra",
    "Tên vụ việc",
    "Cơ quan yêu cầu",
    "Hoạt động tiến hành",
    "Tính chất vụ việc",
    "Tình trạng",
    "Nội dung vụ việc",
    "Các dấu vết chính",
    "Tài liệu",
    "Nhận định",
    "Cán bộ thực hiện",
    "Cấp khám nghiệm",
    "Loại dấu vết",
    "Kết quả khám nghiệm"
]

# =========================================================
# 2. CẤU HÌNH GITHUB API
# =========================================================

try:
    ITHUB_TOKEN = str(st.secrets["GITHUB_TOKEN"]).strip()
    REPO_NAME = st.secrets["REPO_NAME"].strip().strip("/")

    if not GITHUB_TOKEN or not REPO_NAME:
        st.error("GITHUB_TOKEN hoặc REPO_NAME chưa được cấu hình.")
        st.stop()

    if "://" in REPO_NAME or len(REPO_NAME.split("/")) != 2:
        st.error(
            "REPO_NAME không đúng định dạng. "
            "Cần nhập: TEN_TAI_KHOAN/TEN_REPOSITORY"
        )
        st.stop()

except Exception:
    st.error(
        "Không tìm thấy cấu hình GitHub Secrets. "
        "Vui lòng kiểm tra GITHUB_TOKEN và REPO_NAME."
    )
    st.stop()

# ĐỊA CHỈ API CHUẨN
API_URL = (
    f"https://api.github.com/repos/"
    f"{REPO_NAME}/contents/{FILE_PATH}"
)

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

TIMEOUT = 20


# =========================================================
# 3. HÀM XỬ LÝ LỖI GITHUB
# =========================================================

def github_error(response):
    """Chuyển mã lỗi GitHub thành thông báo dễ hiểu."""

    try:
        message = response.json().get("message", "")
    except Exception:
        message = response.text[:300]

    if response.status_code == 401:
        return "GitHub Token không hợp lệ hoặc đã hết hạn."

    if response.status_code == 403:
        return (
            "GitHub từ chối truy cập. "
            "Kiểm tra quyền Contents: Read and write của Token."
        )

    if response.status_code == 404:
        return (
            "Không tìm thấy repository hoặc file data_pc09.csv. "
            "Kiểm tra REPO_NAME và FILE_PATH."
        )

    if response.status_code == 409 or response.status_code == 422:
        return (
            "Dữ liệu có thể đã được thay đổi bởi một phiên khác. "
            "Hãy tải lại ứng dụng và thử lại."
        )

    if response.status_code == 429:
        return "GitHub giới hạn số lần truy cập. Vui lòng thử lại sau."

    return (
        f"GitHub trả về mã lỗi {response.status_code}: {message}"
    )


# =========================================================
# 4. HÀM ĐỌC DỮ LIỆU TỪ GITHUB
# =========================================================

def load_data_from_github():

    try:
        response = requests.get(
            API_URL,
            headers=HEADERS,
            timeout=TIMEOUT
        )

        if response.status_code != 200:
            return None, None, github_error(response)

        file_json = response.json()

        # Giải mã nội dung CSV
        content_bytes = base64.b64decode(
            file_json["content"],
            validate=False
        )

        # Đọc CSV bằng Pandas
        if not content_bytes.strip():
            return None, None, "File CSV đang trống."

        df = pd.read_csv(
            io.BytesIO(content_bytes),
            dtype=str,
            keep_default_na=False,
            encoding="utf-8-sig"
        )

        # Kiểm tra cấu trúc CSV
        missing_columns = [
            col for col in COLUMNS
            if col not in df.columns
        ]

        if missing_columns:
            return (
                None,
                None,
                "File CSV thiếu các cột: "
                + ", ".join(missing_columns)
            )

        return df, file_json["sha"], None

    except requests.exceptions.Timeout:
        return None, None, "Kết nối GitHub quá thời gian chờ."

    except requests.exceptions.ConnectionError:
        return (
            None,
            None,
            "Không kết nối được GitHub. "
            "Kiểm tra kết nối Internet hoặc máy chủ GitHub."
        )

    except Exception as e:
        return None, None, f"Lỗi đọc dữ liệu: {str(e)}"


# =========================================================
# 5. HÀM GHI DỮ LIỆU LÊN GITHUB
# =========================================================

def save_data_to_github(df, sha):

    try:
        # Chuyển DataFrame thành CSV
        csv_buffer = io.StringIO()

        df.to_csv(
            csv_buffer,
            index=False,
            encoding="utf-8"
        )

        csv_content = csv_buffer.getvalue()

        encoded_content = base64.b64encode(
            csv_content.encode("utf-8")
        ).decode("utf-8")

        update_data = {
            "message": "Cap nhat du lieu PC09",
            "content": encoded_content,
            "sha": sha
        }

        response = requests.put(
            API_URL,
            headers=HEADERS,
            json=update_data,
            timeout=TIMEOUT
        )

        if response.status_code in (200, 201):
            return True, "Cập nhật dữ liệu thành công!"

        return False, github_error(response)

    except requests.exceptions.Timeout:
        return False, "Ghi dữ liệu quá thời gian chờ."

    except requests.exceptions.ConnectionError:
        return False, "Không kết nối được GitHub để ghi dữ liệu."

    except Exception as e:
        return False, f"Lỗi ghi dữ liệu: {str(e)}"


# =========================================================
# 6. HÀM LẤY SỐ THỨ TỰ TIẾP THEO
# =========================================================

def get_next_stt(df):

    if df.empty:
        return 1

    if "STT" not in df.columns:
        return 1

    numbers = pd.to_numeric(
        df["STT"],
        errors="coerce"
    )

    if numbers.notna().any():
        return int(numbers.max()) + 1

    return len(df) + 1


# =========================================================
# 7. HÀM CHUẨN HÓA DỮ LIỆU
# =========================================================

def clean_text(value):
    if value is None:
        return ""

    return str(value).strip()


# =========================================================
# 8. GIAO DIỆN CHÍNH
# =========================================================

tab1, tab2 = st.tabs([
    "📝 NHẬP HỒ SƠ",
    "🔍 TRA CỨU VỤ VIỆC"
])


# =========================================================
# TAB 1: NHẬP LIỆU VỤ VIỆC
# =========================================================

with tab1:

    st.subheader("Form Nhập Liệu Vụ Việc")

    with st.form("form_nhap", clear_on_submit=True):

        so_vu = st.text_input("Số vụ")

        dia_ban = st.text_input(
            "Địa bàn (Huyện/Xã)"
        )

        noi_xay_ra = st.text_input("Nơi xảy ra")

        ten_vu = st.text_input("Tên vụ việc")

        cq_yeucau = st.text_input("Cơ quan yêu cầu")

        st.write("**Hoạt động tiến hành:**")

        cb_hientruong = st.checkbox(
            "Khám nghiệm hiện trường"
        )

        cb_tuthi = st.checkbox(
            "Khám nghiệm tử thi"
        )

        cb_dunglai = st.checkbox(
            "Dựng lại hiện trường"
        )

        tinh_chat = st.text_input(
            "Tính chất vụ việc"
        )

        tinh_trang = st.text_input(
            "Tình trạng"
        )

        noi_dung = st.text_area(
            "Nội dung vụ việc"
        )

        dau_vet = st.text_input(
            "Các dấu vết chính"
        )

        tai_lieu = st.text_input(
            "Tài liệu"
        )

        nhan_dinh = st.text_input(
            "Nhận định"
        )

        can_bo = st.text_input(
            "Cán bộ thực hiện"
        )

        cap_kn = st.text_input(
            "Cấp khám nghiệm"
        )

        st.write("**Loại dấu vết thu được:**")

        cb_duongvan = st.checkbox(
            "Đường vân"
        )

        cb_congcu = st.checkbox(
            "Dấu vết công cụ"
        )

        cb_mau = st.checkbox(
            "Dấu vết máu"
        )

        st.write("**Kết quả khám nghiệm:**")

        cb_kq_tinhchat = st.checkbox(
            "Xác định tính chất vụ việc"
        )

        cb_kq_doituong = st.checkbox(
            "Xác định đối tượng"
        )

        submit_btn = st.form_submit_button(
            label="CẬP NHẬT LÊN CƠ SỞ DỮ LIỆU",
            type="primary",
            use_container_width=False
        )

    # Xử lý khi nhấn nút cập nhật
    if submit_btn:

        if not ten_vu.strip() or not dia_ban.strip():

            st.warning(
                "Vui lòng nhập đầy đủ Tên vụ việc và Địa bàn!"
            )

        else:

            with st.spinner("Đang kết nối và cập nhật GitHub..."):

                # Đọc dữ liệu mới nhất và SHA mới nhất
                df, sha, error = load_data_from_github()

                if error:

                    st.error(
                        "Không đọc được dữ liệu gốc: " + error
                    )

                else:

                    # Tạo các danh sách lựa chọn
                    hoat_dong_list = [
                        k for k, v in {
                            "Khám nghiệm hiện trường": cb_hientruong,
                            "Khám nghiệm tử thi": cb_tuthi,
                            "Dựng lại hiện trường": cb_dunglai
                        }.items() if v
                    ]

                    loai_dau_vet_list = [
                        k for k, v in {
                            "Đường vân": cb_duongvan,
                            "Dấu vết công cụ": cb_congcu,
                            "Dấu vết máu": cb_mau
                        }.items() if v
                    ]

                    ket_qua_list = [
                        k for k, v in {
                            "Xác định tính chất vụ việc": cb_kq_tinhchat,
                            "Xác định đối tượng": cb_kq_doituong
                        }.items() if v
                    ]

                    # Lấy số thứ tự
                    stt_moi = get_next_stt(df)

                    # Ngày giờ Việt Nam
                    ngay_hien_tai = datetime.now(
                        ZoneInfo("Asia/Ho_Chi_Minh")
                    ).strftime("%d/%m/%Y")

                    # Tạo bản ghi mới
                    new_record = {
                        "STT": str(stt_moi),
                        "Số vụ": clean_text(so_vu),
                        "Địa bàn": clean_text(dia_ban),
                        "Ngày tháng": ngay_hien_tai,
                        "Nơi xảy ra": clean_text(noi_xay_ra),
                        "Tên vụ việc": clean_text(ten_vu),
                        "Cơ quan yêu cầu": clean_text(cq_yeucau),
                        "Hoạt động tiến hành": "; ".join(hoat_dong_list),
                        "Tính chất vụ việc": clean_text(tinh_chat),
                        "Tình trạng": clean_text(tinh_trang),
                        "Nội dung vụ việc": clean_text(noi_dung),
                        "Các dấu vết chính": clean_text(dau_vet),
                        "Tài liệu": clean_text(tai_lieu),
                        "Nhận định": clean_text(nhan_dinh),
                        "Cán bộ thực hiện": clean_text(can_bo),
                        "Cấp khám nghiệm": clean_text(cap_kn),
                        "Loại dấu vết": "; ".join(loai_dau_vet_list),
                        "Kết quả khám nghiệm": "; ".join(ket_qua_list)
                    }

                    # Thêm bản ghi vào DataFrame
                    new_row = pd.DataFrame(
                        [new_record],
                        columns=COLUMNS
                    )

                    updated_df = pd.concat(
                        [df, new_row],
                        ignore_index=True
                    )

                    # Ghi lên GitHub
                    success, message = save_data_to_github(
                        updated_df,
                        sha
                    )

                    if success:

                        st.success(
                            f"Đã cập nhật thành công vụ việc STT {stt_moi}!"
                        )

                        st.balloons()

                    else:

                        st.error(message)


# =========================================================
# TAB 2: TRA CỨU / TÌM KIẾM
# =========================================================

with tab2:

    st.subheader("Tìm Kiếm Thông Tin Vụ Việc")

    keyword = st.text_input(
        "Nhập Số vụ, Địa bàn hoặc Tên vụ việc cần tìm..."
    )

    if keyword.strip():

        with st.spinner("Đang tìm kiếm dữ liệu..."):

            df, sha, error = load_data_from_github()

        if error:

            st.error(
                "Không thể tải dữ liệu tra cứu: " + error
            )

        elif df is not None and not df.empty:

            keyword = keyword.strip()

            # Tìm kiếm không phân biệt chữ hoa, chữ thường
            mask = (
                df["Tên vụ việc"].astype(str).str.contains(
                    keyword,
                    case=False,
                    na=False,
                    regex=False
                )
                |
                df["Số vụ"].astype(str).str.contains(
                    keyword,
                    case=False,
                    na=False,
                    regex=False
                )
                |
                df["Địa bàn"].astype(str).str.contains(
                    keyword,
                    case=False,
                    na=False,
                    regex=False
                )
            )

            result_df = df[mask]

            if not result_df.empty:

                st.write(
                    f"Tìm thấy **{len(result_df)}** kết quả phù hợp:"
                )

                for _, row in result_df.iterrows():

                    with st.expander(
                        f"STT: {row['STT']} - "
                        f"Vụ: {row['Tên vụ việc']} "
                        f"({row['Địa bàn']})"
                    ):

                        st.write(
                            f"• **Số vụ:** {row['Số vụ']}"
                        )

                        st.write(
                            f"• **Ngày khám nghiệm:** {row['Ngày tháng']}"
                        )

                        st.write(
                            f"• **Nơi xảy ra:** {row['Nơi xảy ra']}"
                        )

                        st.write(
                            f"• **Cơ quan yêu cầu:** {row['Cơ quan yêu cầu']}"
                        )

                        st.write(
                            f"• **Hoạt động tiến hành:** "
                            f"{row['Hoạt động tiến hành']}"
                        )

                        st.write(
                            f"• **Tính chất vụ việc:** "
                            f"{row['Tính chất vụ việc']}"
                        )

                        st.write(
                            f"• **Tình trạng:** {row['Tình trạng']}"
                        )

                        st.write(
                            f"• **Nội dung diễn biến:** "
                            f"{row['Nội dung vụ việc']}"
                        )

                        st.write(
                            f"• **Các dấu vết chính:** "
                            f"{row['Các dấu vết chính']}"
                        )

                        st.write(
                            f"• **Loại dấu vết thu được:** "
                            f"{row['Loại dấu vết']}"
                        )

                        st.write(
                            f"• **Tài liệu:** {row['Tài liệu']}"
                        )

                        st.write(
                            f"• **Nhận định:** {row['Nhận định']}"
                        )

                        st.write(
                            f"• **Cán bộ thực hiện:** "
                            f"{row['Cán bộ thực hiện']}"
                        )

                        st.write(
                            f"• **Cấp khám nghiệm:** {row['Cấp khám nghiệm']}"
                        )

                        st.write(
                            f"• **Kết quả khám nghiệm:** "
                            f"{row['Kết quả khám nghiệm']}"
                        )

            else:

                st.info(
                    "Không tìm thấy dữ liệu nào trùng khớp."
                )

        else:

            st.info("Cơ sở dữ liệu hiện chưa có hồ sơ.")
