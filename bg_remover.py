import io
import zipfile
from pathlib import Path
import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from rembg import remove
import uuid
import concurrent.futures

MAX_FILES = 5
ALLOWED_TYPES = ["png", "jpg", "jpeg"]
ENHANCE_FACTOR = 1.5  # Adjust as needed
IMAGE_QUALITY = 95  # Adjust as needed


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
    """Displays the user interface for file upload and returns uploaded files."""
    st.sidebar.markdown("## Image Background Remover")

    uploaded_files = st.sidebar.file_uploader(
        "Choose images",
        type=ALLOWED_TYPES,
        accept_multiple_files=True,
        key=st.session_state.get("uploader_key", "file_uploader"),
    )

    background_color = st.sidebar.color_picker(
        "Choose background color", "#FFFFFF"  # Default color is white
    )

    display_footer()
    return uploaded_files, background_color


def display_footer():
    """Displays a custom footer."""
    footer = """<div style="position: fixed; bottom: 0; left: 20px;">
                <p>Developed with ❤ by <a href="https://github.com/balewgize" target="_blank">@balewgize</a></p>
                </div>"""
    st.sidebar.markdown(footer, unsafe_allow_html=True)


def process_and_display_images(uploaded_files, background_color):
    """Processes the uploaded files and displays the original and result images."""
    if not uploaded_files:
        st.warning("Please upload an image.")
        return

    if not st.sidebar.button("Remove Background"):
        return

    if len(uploaded_files) > MAX_FILES:
        st.warning(f"Maximum {MAX_FILES} files will be processed.")
        uploaded_files = uploaded_files[:MAX_FILES]

    with st.spinner("Removing backgrounds..."):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(process_image, file, background_color): file
                for file in uploaded_files
            }
            for future in concurrent.futures.as_completed(futures):
                original, result, name = future.result()
                col1, col2 = st.columns(2)
                with col1:
                    st.image(original, caption="Original")
                with col2:
                    st.image(result, caption="Result")
                download_result(result, name)


def process_image(file, background_color):
    """Processes a single image."""
    original_image = Image.open(file).convert("RGBA")
    original_width, original_height = original_image.size
    result_image = remove_background(file.getvalue())
    result_image = enhance_image(result_image)
    result_image = result_image.resize((original_width, original_height), Image.LANCZOS)  # Upscale to original size
    result_image = apply_background_color(result_image, background_color)
    return original_image, result_image, file.name


def remove_background(image_bytes):
    """Removes the background from an image."""
    result = remove(image_bytes)
    return Image.open(io.BytesIO(result)).convert("RGBA")


def enhance_image(image):
    """Enhances the image for better quality."""
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(ENHANCE_FACTOR)  # Increase contrast
    image = image.filter(ImageFilter.SMOOTH)  # Apply smoothing filter
    return image


def apply_background_color(image, background_color):
    """Applies the selected background color to the image."""
    background = Image.new("RGBA", image.size, background_color)
    composite_image = Image.alpha_composite(background, image)
    return composite_image


def img_to_bytes(img):
    """Converts an Image object to bytes."""
    buf = io.BytesIO()
    img.save(buf, format="PNG", quality=IMAGE_QUALITY)
    return buf.getvalue()


def download_result(image, name):
    """Allows the user to download the result image."""
    st.download_button(
        label="Download Result",
        data=img_to_bytes(image),
        file_name=f"{Path(name).stem}_nobg.png",
        mime="image/png",
    )


def main():
    setup_page()
    initialize_session()
    uploaded_files, background_color = display_ui()
    process_and_display_images(uploaded_files, background_color)


if __name__ == "__main__":
    main()
