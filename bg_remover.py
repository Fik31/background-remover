import io
import zipfile
from pathlib import Path
import streamlit as st
from PIL import Image
from rembg import remove
import uuid
import concurrent.futures

MAX_FILES = 5
ALLOWED_TYPES = ["png", "jpg", "jpeg"]


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

    display_footer()
    return uploaded_files


def display_footer():
    """Displays a custom footer."""
    footer = """<div style="position: fixed; bottom: 0; left: 20px;">
                <p>Developed with ❤ by <a href="https://github.com/balewgize" target="_blank">@balewgize</a></p>
                </div>"""
    st.sidebar.markdown(footer, unsafe_allow_html=True)


def process_and_display_images(uploaded_files):
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
            futures = {executor.submit(process_image, file): file for file in uploaded_files}
            for future in concurrent.futures.as_completed(futures):
                original, result, name = future.result()
                col1, col2 = st.columns(2)
                with col1:
                    st.image(original, caption="Original")
                with col2:
                    st.image(result, caption="Result")
                download_result(result, name)


def process_image(file):
    """Processes a single image."""
    original_image = Image.open(file).convert("RGBA")
    result_image = remove_background(file.getvalue())
    return original_image, result_image, file.name


def remove_background(image_bytes):
    """Removes the background from an image."""
    result = remove(image_bytes)
    return Image.open(io.BytesIO(result)).convert("RGBA")


def img_to_bytes(img):
    """Converts an Image object to bytes."""
    buf = io.BytesIO()
    img.save(buf, format="PNG")
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
    uploaded_files = display_ui()
    process_and_display_images(uploaded_files)


if __name__ == "__main__":
    main()
