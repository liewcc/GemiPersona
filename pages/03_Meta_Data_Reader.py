import streamlit as st
from PIL import Image
from PIL.ExifTags import TAGS
import json
import base64
import os
from io import BytesIO

# --- Page Configuration ---
# Version: 1.4.1
# Update: Added a warning prompt and a reload button to switch to home.py after saving config.
# Ensure all UI components follow the 2026 'width=stretch' standard.
st.set_page_config(page_title="Meta Data Reader v1.4.1", layout="wide")

# Constants
CONFIG_FILE = "config.json"
HOME_PAGE = "home.py" # Ensure this matches your actual home file name

# Initialize session state for uploader key and update status
if 'uploader_key' not in st.session_state:
    st.session_state['uploader_key'] = 0
if 'config_updated' not in st.session_state:
    st.session_state['config_updated'] = False

def get_image_base64(image):
    """Convert PIL image to base64 string for direct HTML injection."""
    buffered = BytesIO()
    # Ensure it's saved as PNG to maintain metadata compatibility during preview
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def clear_gallery():
    """Increment the key to force-reset the file_uploader component."""
    st.session_state['uploader_key'] += 1
    st.session_state['config_updated'] = False

def update_config_json(new_prompt):
    """Update the last_prompt field in the local config.json file."""
    if not os.path.exists(CONFIG_FILE):
        st.error(f"Error: {CONFIG_FILE} not found in the current directory.")
        return False
    
    try:
        # Read existing config
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # Update field
        config_data['last_prompt'] = new_prompt
        
        # Write back to file
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        
        st.session_state['config_updated'] = True
        return True
    except Exception as e:
        st.error(f"Failed to update config: {e}")
        return False

# --- Sidebar: Control Center ---
with st.sidebar:
    st.markdown("### 📂 Control Center")
    st.markdown("Version: 1.4.1")
    
    # Using the dynamic key from session_state for resetting the uploader
    uploaded_files = st.file_uploader("Upload images to read metadata", 
                                      type=["png", "jpg", "jpeg", "webp"], 
                                      accept_multiple_files=True,
                                      key=f"uploader_{st.session_state['uploader_key']}")
    
    st.write("---")
    # Button to trigger the reset logic
    if st.button("🗑️ Clear Gallery", width='stretch', on_click=clear_gallery):
        st.toast("Gallery cleared successfully!")

# --- Main Panel: Gallery ---
if uploaded_files:
    st.write(f"📊 Displaying {len(uploaded_files)} image(s)")
    st.write("---")
    
    # Global Warning for configuration update
    if st.session_state['config_updated']:
        st.warning("⚠️ **Configuration Updated!** The data in config.json has changed. Please reload the Home page to apply changes.")
        if st.button("🔄 Reload & Return to Home", width='stretch'):
            st.switch_page(HOME_PAGE)
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
                
                detected_prompt = ""
                
                # 1. Read Textual Information (Common in PNG)
                png_info = img.info
                if png_info:
                    with st.expander("✨ Key Information (Text/Prompt)", expanded=True):
                        # Detect common keys for AI generated prompts
                        detected_prompt = png_info.get("Prompt", png_info.get("parameters", ""))
                        
                        st.text_area("Detected Prompt", 
                                     value=detected_prompt, 
                                     height=150, 
                                     key=f"text_{uploaded_file.name}_{st.session_state['uploader_key']}")
                        
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
                        
                        # If prompt wasn't in png_info, check common EXIF tags
                        if not detected_prompt:
                            detected_prompt = readable_exif.get("ImageDescription", "")
                
                # --- Action: Write to Config ---
                if detected_prompt:
                    if st.button(f"📥 Apply Prompt to Config", key=f"btn_{uploaded_file.name}", width='stretch'):
                        if update_config_json(detected_prompt):
                            st.toast("Config updated successfully!")
                            st.rerun() # Refresh to show the warning box
                
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
    4. Use the **'Apply Prompt to Config'** button to save metadata back to your configuration file.
    5. After saving, click the **Reload** button to update your main dashboard.
    """)

# --- Footer ---
st.sidebar.markdown("---")
st.sidebar.caption("Meta Data Reader - Version 1.4.1")