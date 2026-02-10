import streamlit as st
from PIL import Image
from PIL.ExifTags import TAGS
import json
import base64
from io import BytesIO

# --- Page Configuration ---
# Version: 1.3.0
# Update: Upgraded Streamlit layout parameters. Replaced deprecated 'use_container_width' with 'width="stretch"'.
st.set_page_config(page_title="Meta Data Reader v1.3.0", layout="wide")

# Initialize session state for uploader key if it doesn't exist
if 'uploader_key' not in st.session_state:
    st.session_state['uploader_key'] = 0

def get_image_base64(image):
    """Convert PIL image to base64 string for direct HTML injection."""
    buffered = BytesIO()
    # Ensure it's saved as PNG to maintain metadata compatibility during preview
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def clear_gallery():
    """Increment the key to force-reset the file_uploader component."""
    st.session_state['uploader_key'] += 1

# --- Sidebar: Control Center ---
with st.sidebar:
#    st.header("📂 Control Center")
    st.markdown("Version: 1.3.0")
    
    # Using the dynamic key from session_state for resetting the uploader
    uploaded_files = st.file_uploader("Upload images to read metadata", 
                                      type=["png", "jpg", "jpeg", "webp"], 
                                      accept_multiple_files=True,
                                      key=f"uploader_{st.session_state['uploader_key']}")
    
#    st.write("---")
    # Button to trigger the reset logic - Updated to width='stretch' per 2026 API standards
    if st.button("🗑️ Clear Gallery", width='stretch', on_click=clear_gallery):
        st.toast("Gallery cleared successfully!")

# --- Main Panel: Gallery ---
#st.title("🖼️ Image Gallery & Meta Data")

if uploaded_files:
    st.write(f"📊 Displaying {len(uploaded_files)} image(s)")
    st.write("---")
    
    for uploaded_file in uploaded_files:
        col1, col2 = st.columns([1, 2])
        
        try:
            # Open image using PIL
            img = Image.open(uploaded_file)
            
            # --- Left Column: Image Preview ---
            with col1:
                img_base64 = get_image_base64(img)
                st.markdown(
                    f'<img src="data:image/png;base64,{img_base64}" style="width:100%; border-radius: 12px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">',
                    unsafe_allow_html=True
                )
                st.caption(f"File Name: {uploaded_file.name}")

            # --- Right Column: Metadata Extraction ---
            with col2:
                st.subheader("📝 Metadata Details")
                
                # 1. Read Textual Information (Common in PNG)
                png_info = img.info
                if png_info:
                    with st.expander("✨ Key Information (Text/Prompt)", expanded=True):
                        # Detect common keys for AI generated prompts (e.g., Stable Diffusion, Midjourney)
                        prompt = png_info.get("Prompt", png_info.get("parameters", "No specific prompt found"))
                        st.text_area("Detected Prompt", value=prompt, height=150, key=f"text_{uploaded_file.name}_{st.session_state['uploader_key']}")
                        
                        if len(png_info) > 1:
                            st.json(png_info)
                
                # 2. Read Technical EXIF Data (Common in JPG/WebP)
                exif_data = img._getexif()
                if exif_data:
                    with st.expander("📸 Technical Parameters (EXIF)"):
                        readable_exif = {}
                        for k, v in exif_data.items():
                            tag = TAGS.get(k, k)
                            if isinstance(v, bytes):
                                try:
                                    readable_exif[tag] = v.decode(errors="ignore")
                                except:
                                    readable_exif[tag] = str(v)
                            else:
                                readable_exif[tag] = v
                        st.json(readable_exif)
                
                if not png_info and not exif_data:
                    st.warning("No recognizable metadata found in this file.")

        except Exception as e:
            st.error(f"Error parsing {uploaded_file.name}: {e}")
        
        st.write("---")

else:
    # Empty State Guidance
    st.info("The gallery is currently empty. Please use the sidebar to upload images.")
    st.markdown("""
    ### 🚀 Getting Started
    1. Navigate to the **Upload** section in the left sidebar.
    2. **Drag and drop** your images (PNG, JPG, WebP supported).
    3. The system will automatically parse and display embedded prompts and EXIF data.
    """)

# --- Footer ---
# st.sidebar.markdown("---")
# st.sidebar.caption("Meta Data Reader - Version 1.3.0")