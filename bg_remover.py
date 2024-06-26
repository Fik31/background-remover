import io
import zipfile
from pathlib import Path
import streamlit as st
from PIL import Image, ImageEnhance, ImageDraw, ImageFont
import toml
from rembg import remove
import uuid
import concurrent.futures
import platform

MAX_FILES = 5
ALLOWED_TYPES = ["png", "jpg", "jpeg"]
DEFAULT_BRIGHTNESS = 1.0
DEFAULT_ENHANCEMENT = 1.0
DEFAULT_QUALITY = 95
DEFAULT_SIZE_RATIO = (4, 3)  # Default size ratio (width:height)


def setup_page():
    """Sets up the Streamlit page configuration."""
    st.set_page_config(page_title="Background Remover", page_icon="✂️")
    hide_streamlit_style()


def hide_streamlit_style():
    """Hides default Streamlit styling."""
    st.markdown(
        "<style>footer {visibility: hidden;} #MainMenu {visibility: hidden;}</style>",
        unsafe_allow_html=True,
    )


def initialize_session():
    """Initializes a unique session ID."""
    if "uploader_key" not in st.session_state:
        st.session_state["uploader_key"] = str(uuid.uuid4())


def display_ui():
    """Displays the user interface for file upload and returns uploaded files and settings."""
    st.sidebar.markdown("## Penghapus Latar Belakang Gambar")

    uploaded_files = st.sidebar.file_uploader(
        "Pilih gambar (Maksimal 5 file)",
        type=ALLOWED_TYPES,
        accept_multiple_files=True,
        key=st.session_state.get("uploader_key", "file_uploader"),
    )

    if uploaded_files and len(uploaded_files) > MAX_FILES:
        st.sidebar.warning(f"Maksimal {MAX_FILES} gambar yang akan diproses.")

    # st.sidebar.markdown("**Catatan:** Tipe file yang diperbolehkan: PNG, JPG, dan JPEG.")

    add_background_color = st.sidebar.checkbox("Tambahkan Warna Latar Belakang", value=True)
    background_color = None
    if add_background_color:
        background_color = st.sidebar.color_picker(
            "Pilih warna latar belakang", "#FFFFFF"  # Warna default adalah putih
        )

    brightness = st.sidebar.slider(
        "Kecerahan", min_value=0.1, max_value=2.0, value=DEFAULT_BRIGHTNESS, step=0.1
    )

    enhancement = st.sidebar.slider(
        "Peningkatan", min_value=0.1, max_value=2.0, value=DEFAULT_ENHANCEMENT, step=0.1
    )

    quality = st.sidebar.slider(
        "Kualitas Gambar (%)", min_value=1, max_value=100, value=DEFAULT_QUALITY
    )

    change_size_ratio = st.sidebar.checkbox("Ubah Rasio Ukuran", value=False)

    size_ratio_options = [
        (4, 3, "4:3 (Landscape)"),
        (16, 9, "16:9 (Landscape)"),
        (3, 2, "3:2 (Landscape)"),
        (2, 3, "2:3 (Potrait)"),
        (3, 4, "3:4 (Potrait)"),
        (9, 16, "9:16 (Potrait)"),
        (2, 1, "2:1 (Landscape)"),
        (1, 2, "1:2 (Potrait)"),
        (1, 1, "1:1 (Square)"),
    ]

    size_ratio = DEFAULT_SIZE_RATIO
    if change_size_ratio:
        size_ratio = st.sidebar.selectbox(
            "Rasio Ukuran",
            options=size_ratio_options,
            format_func=lambda ratio: ratio[2],
            index=0,  # Indeks default
        )

    display_footer()
    return (
        uploaded_files,
        add_background_color,
        background_color,
        brightness,
        enhancement,
        quality,
        size_ratio,
    )


def display_footer():
    """Displays a custom footer."""
    footer = """<div style="position: fixed; bottom: 0; left: 20px;">
                <p>Developed by 15.4B.07 Informatika</p>
                </div>"""
    st.sidebar.markdown(footer, unsafe_allow_html=True)


def process_and_display_images(
    uploaded_files,
    add_background_color,
    background_color,
    brightness,
    enhancement,
    quality,
    size_ratio,
):
    """Processes the uploaded files and displays the original and result images."""
    if not uploaded_files:
        st.warning("Silakan unggah gambar.")
        return

    if not st.sidebar.button("Hapus Latar Belakang"):
        return

    if len(uploaded_files) > MAX_FILES:
        st.warning(f"Maksimal {MAX_FILES} gambar akan diproses.")
        uploaded_files = uploaded_files[:MAX_FILES]

    with st.spinner("Menghapus latar belakang..."):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(
                    process_image,
                    file,
                    add_background_color,
                    background_color,
                    brightness,
                    enhancement,
                    quality,
                    size_ratio,
                ): file
                for file in uploaded_files
            }
            for future in concurrent.futures.as_completed(futures):
                original, result, name = future.result()
                col1, col2 = st.columns(2)
                with col1:
                    st.image(original, caption="Asli")
                with col2:
                    st.image(result, caption="Hasil")
                download_result(result, name)


def process_image(
    file,
    add_background_color,
    background_color,
    brightness,
    enhancement,
    quality,
    size_ratio,
):
    """Processes a single image."""
    original_image = Image.open(file).convert("RGBA")
    original_width, original_height = original_image.size
    result_image = remove_background(file.getvalue())
    result_image = enhance_image(result_image, brightness, enhancement)
    if size_ratio == "original":
        new_size = (original_width, original_height)
    else:
        new_size = None  # Default new size is None (no resizing)
        if size_ratio != DEFAULT_SIZE_RATIO:  # If size ratio is not default
            if len(size_ratio) == 3:  # If ratio has three elements
                ratio_width, ratio_height, _ = size_ratio
            else:  # If ratio has two elements
                ratio_width, ratio_height = size_ratio
            new_width = int((original_height / ratio_height) * ratio_width)
            new_size = (new_width, original_height)
    if new_size is not None:
        result_image = result_image.resize(new_size, Image.LANCZOS)  # Resize image
    if add_background_color:
        result_image = apply_background_color(result_image, background_color)
    return original_image, result_image, file.name



def remove_background(image_bytes):
    """Removes the background from an image."""
    result = remove(image_bytes)
    return Image.open(io.BytesIO(result)).convert("RGBA")


def enhance_image(image, brightness, enhancement):
    """Enhances the image for better quality."""
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(brightness)  # Adjust brightness
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(enhancement)  # Adjust contrast
    return image


def apply_background_color(image, background_color):
    """Applies the selected background color to the image."""
    background = Image.new("RGBA", image.size, background_color)
    composite_image = Image.alpha_composite(background, image)
    return composite_image


def img_to_bytes(img):
    """Converts an Image object to bytes."""
    buf = io.BytesIO()
    img.save(buf, format="PNG", quality=DEFAULT_QUALITY)
    return buf.getvalue()


def download_result(image, name):
    """Allows the user to download the result image."""
    st.download_button(
        label="Unduh Hasil",
        data=img_to_bytes(image),
        file_name=f"{Path(name).stem}_nobg.png",
        mime="image/png",
    )


def main():
    setup_page()
    initialize_session()
    (
        uploaded_files,
        add_background_color,
        background_color,
        brightness,
        enhancement,
        quality,
        size_ratio,
    ) = display_ui()
    process_and_display_images(
        uploaded_files,
        add_background_color,
        background_color,
        brightness,
        enhancement,
        quality,
        size_ratio,
    )


if __name__ == "__main__":
    main()
