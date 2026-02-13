# Version: v1.2.0
# Description: UI Optimized Metadata Migrator with fixed-width previews and multi-line text areas.

import streamlit as st
from PIL import Image
from PIL.PngImagePlugin import PngInfo
import piexif
import io

# Set page configuration
st.set_page_config(layout="wide", page_title="Metadata Migrator Pro")

def get_metadata(img, file_type):
    """Extract metadata based on file type."""
    metadata = {}
    if file_type in ["jpg", "jpeg"]:
        try:
            exif_dict = piexif.load(img.info.get("exif", b""))
            for ifd in ("0th", "Exif"):
                for tag in exif_dict[ifd]:
                    tag_name = piexif.TAGS[ifd][tag]["name"]
                    value = exif_dict[ifd][tag]
                    if isinstance(value, bytes):
                        try:
                            value = value.decode("utf-8")
                        except:
                            continue
                    metadata[f"{ifd}:{tag_name}"] = str(value)
        except Exception as e:
            st.warning(f"Could not read JPEG EXIF: {e}")
    elif file_type == "png":
        for key, value in img.info.items():
            if isinstance(value, (str, int)):
                metadata[f"PNG:{key}"] = str(value)
    return metadata

def main():
    # --- UI Header ---
    st.title("Image Metadata Migrator v1.2.0")
    st.markdown("Easily migrate and edit metadata between images with an optimized interface.")
    
    st.divider()

    col1, col2 = st.columns(2)
    
    source_metadata = {}
    edited_metadata = {}

    # --- Step 1: Source Selection ---
    with col1:
        st.header("1. Source Image")
        source_file = st.file_uploader("Upload Source (JPG/PNG)", type=["jpg", "jpeg", "png"], key="source")
        
        if source_file:
            source_type = source_file.name.split(".")[-1].lower()
            source_img = Image.open(source_file)
            
            # Optimized Image Preview: Fixed width to prevent excessive scrolling
            st.image(source_img, caption=f"Source Preview ({source_type.upper()})", width=300)
            
            source_metadata = get_metadata(source_img, source_type)
            
            if source_metadata:
                st.subheader("Edit Metadata Details")
                st.write("Modify the values below. Each box shows approximately 5-10 lines.")
                for key, value in source_metadata.items():
                    # Optimized Text Area: Multi-line support with fixed height
                    edited_metadata[key] = st.text_area(
                        label=f"Field: {key}",
                        value=value,
                        height=150, # Sufficient for 5-10 lines of text
                        key=f"input_{key}"
                    )
            else:
                st.info("No editable metadata detected in source.")

    # --- Step 2: Target Selection & Processing ---
    with col2:
        st.header("2. Target Image")
        target_file = st.file_uploader("Upload Target (JPG/PNG)", type=["jpg", "jpeg", "png"], key="target")
        
        if target_file:
            target_type = target_file.name.split(".")[-1].lower()
            # Handle RGB conversion for JPEGs
            target_img = Image.open(target_file)
            if target_type in ["jpg", "jpeg"] and target_img.mode != "RGB":
                target_img = target_img.convert("RGB")
                
            # Optimized Image Preview
            st.image(target_img, caption=f"Target Preview ({target_type.upper()})", width=300)
            
            st.divider()
            
            if st.button("🚀 Process & Inject Metadata", use_container_width=True):
                output_buffer = io.BytesIO()
                
                try:
                    if target_type in ["jpg", "jpeg"]:
                        # Construct EXIF structure
                        new_exif = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}}
                        for key, val in edited_metadata.items():
                            if ":" in key:
                                ifd, tag_name = key.split(":")
                                if ifd in ["0th", "Exif"]:
                                    tag_id = next(attr for attr in piexif.TAGS[ifd] if piexif.TAGS[ifd][attr]["name"] == tag_name)
                                    # Encode back to bytes for EXIF
                                    new_exif[ifd][tag_id] = val.encode("utf-8")
                        
                        exif_bytes = piexif.dump(new_exif)
                        target_img.save(output_buffer, format="JPEG", exif=exif_bytes)
                    
                    elif target_type == "png":
                        # Construct PNG chunks
                        png_info = PngInfo()
                        for key, val in edited_metadata.items():
                            clean_key = key.split(":")[-1]
                            png_info.add_text(clean_key, str(val))
                        
                        target_img.save(output_buffer, format="PNG", pnginfo=png_info)
                    
                    st.success("Success! Your image is ready.")
                    st.download_button(
                        label="📥 Download Resulting Image",
                        data=output_buffer.getvalue(),
                        file_name=f"migrated_{target_file.name}",
                        mime=f"image/{target_type}",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Processing Error: {e}")

if __name__ == "__main__":
    main()