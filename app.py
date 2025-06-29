import streamlit as st
import firebase_admin
from firebase_admin import credentials, storage, firestore
from datetime import datetime
import uuid
from PIL import Image
import io
import json

# Firebase Initialization - Fixed Version
if not firebase_admin._apps:
    try:
        # Method 1: If FIREBASE_KEY is a JSON string in secrets
        if "FIREBASE_KEY" in st.secrets:
            # Try to parse as JSON string first
            try:
                firebase_key = json.loads(st.secrets["FIREBASE_KEY"])
                cred = credentials.Certificate(firebase_key)
            except json.JSONDecodeError:
                # If it fails, maybe it's already a dict in secrets.toml
                firebase_key = dict(st.secrets["FIREBASE_KEY"])
                cred = credentials.Certificate(firebase_key)
        
        # Method 2: If individual keys are stored separately in secrets
        elif "type" in st.secrets:
            firebase_key = {
                "type": st.secrets["type"],
                "project_id": st.secrets["project_id"],
                "private_key_id": st.secrets["private_key_id"],
                "private_key": st.secrets["private_key"].replace('\\n', '\n'),  # Fix newlines
                "client_email": st.secrets["client_email"],
                "client_id": st.secrets["client_id"],
                "auth_uri": st.secrets["auth_uri"],
                "token_uri": st.secrets["token_uri"],
                "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
                "client_x509_cert_url": st.secrets["client_x509_cert_url"]
            }
            cred = credentials.Certificate(firebase_key)
        
        else:
            st.error("❌ Firebase credentials not found in secrets!")
            st.stop()
            
        # Initialize Firebase
        firebase_admin.initialize_app(cred, {
            'storageBucket': 'apple-store-d26b3.appspot.com'
        })
        
    except Exception as e:
        st.error(f"❌ Firebase initialization error: {str(e)}")
        st.error("Please check your Firebase configuration in Streamlit secrets.")
        st.stop()

# Firestore & Storage references
db = firestore.client()
bucket = storage.bucket()

# Rest of your code remains the same...
st.title("🍎 Apple Dataset Collector")
st.markdown("### सेब की तस्वीरें जमा करें - Apple Images Collection")

# Introduction and Purpose
st.markdown("""
---
### 🎯 **Why are we collecting apple images? / हम सेब की तस्वीरें क्यों जमा कर रहे हैं?**

**English:** We are building a comprehensive apple dataset to help train AI models that can identify different apple varieties. Your contribution will help improve agricultural technology and assist farmers in identifying apple types.

**हिंदी:** हम एक व्यापक सेब डेटासेट बना रहे हैं जो AI मॉडल को विभिन्न सेब की किस्मों को पहचानने में मदद करेगा। आपका योगदान कृषि तकनीक को बेहतर बनाने और किसानों को सेब की किस्में पहचानने में सहायता करेगा।

---
""")

# Instructions in Hindi
st.markdown("""
### 📱 **How to upload images / तस्वीर अपलोड कैसे करें:**

**हिंदी निर्देश:**
1. **📷 कैमरा से तस्वीर लें:** नीचे "Take Photo" बटन दबाएं या अपनी गैलरी से तस्वीर चुनें
2. **🍏 सेब की किस्म बताएं:** जैसे - फूजी, गाला, कश्मीरी, शिमला आदि
3. **📍 जगह का नाम (वैकल्पिक):** आपका शहर या राज्य का नाम
4. **🚀 सबमिट करें:** "Submit" बटन दबाएं

**Tips for good photos / अच्छी तस्वीर के लिए टिप्स:**
- 🌞 अच्छी रोशनी में तस्वीर लें
- 🍎 सेब को साफ-साफ दिखाएं
- 📏 सेब को पास से लें (close-up)
- 🎯 एक बार में एक ही सेब की तस्वीर लें

---
""")

# Image Upload Options
st.subheader("📸 Upload Apple Image / सेब की तस्वीर अपलोड करें")

# Tab for different upload methods
tab1, tab2 = st.tabs(["📱 Camera / कैमरा", "📁 Upload File / फाइल अपलोड"])

uploaded_file = None

with tab1:
    st.markdown("**📷 Take a photo using your device camera / अपने डिवाइस के कैमरा से तस्वीर लें**")
    camera_image = st.camera_input("Take a picture of an apple / सेब की तस्वीर लें")
    
    if camera_image:
        # Image rotation controls
        st.markdown("**🔄 Rotate image if needed / जरूरत पड़ने पर तस्वीर घुमाएं:**")
        
        col_rot1, col_rot2, col_rot3, col_rot4 = st.columns(4)
        
        with col_rot1:
            rotate_left = st.button("↺ 90° Left / बाएं", key="cam_left")
        with col_rot2:
            rotate_right = st.button("↻ 90° Right / दाएं", key="cam_right")
        with col_rot3:
            rotate_180 = st.button("↕ 180° Flip / पलटें", key="cam_flip")
        with col_rot4:
            reset_rotation = st.button("🔄 Reset / रीसेट", key="cam_reset")
        
        # Initialize rotation state
        if 'camera_rotation' not in st.session_state:
            st.session_state.camera_rotation = 0
        
        # Handle rotation buttons
        if rotate_left:
            st.session_state.camera_rotation = (st.session_state.camera_rotation - 90) % 360
        if rotate_right:
            st.session_state.camera_rotation = (st.session_state.camera_rotation + 90) % 360
        if rotate_180:
            st.session_state.camera_rotation = (st.session_state.camera_rotation + 180) % 360
        if reset_rotation:
            st.session_state.camera_rotation = 0
        
        # Apply rotation and show preview
        if st.session_state.camera_rotation != 0:
            original_image = Image.open(camera_image)
            rotated_image = original_image.rotate(-st.session_state.camera_rotation, expand=True)
            
            # Convert rotated image back to bytes
            img_byte_array = io.BytesIO()
            rotated_image.save(img_byte_array, format='JPEG')
            img_byte_array.seek(0)
            
            # Create a file-like object for upload
            class RotatedImageFile:
                def __init__(self, byte_data):
                    self.byte_data = byte_data
                    
                def getvalue(self):
                    return self.byte_data.getvalue()
                    
                def read(self):
                    return self.byte_data.getvalue()
            
            uploaded_file = RotatedImageFile(img_byte_array)
            
            # Show current rotation
            st.info(f"🔄 Current rotation: {st.session_state.camera_rotation}° / वर्तमान घुमाव: {st.session_state.camera_rotation}°")
            st.image(rotated_image, caption="Rotated Image / घुमाई गई तस्वीर", width=300)
        else:
            uploaded_file = camera_image
            st.image(camera_image, caption="Original Image / मूल तस्वीर", width=300)

with tab2:
    st.markdown("**📁 Choose an image from your device / अपने डिवाइस से तस्वीर चुनें**")
    file_upload = st.file_uploader(
        "Select apple image / सेब की तस्वीर चुनें", 
        type=["jpg", "jpeg", "png"],
        help="हिंदी: JPG, JPEG या PNG फॉर्मेट में तस्वीर चुनें"
    )
    
    if file_upload:
        # Image rotation controls for uploaded files too
        st.markdown("**🔄 Rotate image if needed / जरूरत पड़ने पर तस्वीर घुमाएं:**")
        
        col_rot1, col_rot2, col_rot3, col_rot4 = st.columns(4)
        
        with col_rot1:
            rotate_left_upload = st.button("↺ 90° Left / बाएं", key="upload_left")
        with col_rot2:
            rotate_right_upload = st.button("↻ 90° Right / दाएं", key="upload_right")
        with col_rot3:
            rotate_180_upload = st.button("↕ 180° Flip / पलटें", key="upload_flip")
        with col_rot4:
            reset_rotation_upload = st.button("🔄 Reset / रीसेट", key="upload_reset")
        
        # Initialize rotation state for uploads
        if 'upload_rotation' not in st.session_state:
            st.session_state.upload_rotation = 0
        
        # Handle rotation buttons for uploads
        if rotate_left_upload:
            st.session_state.upload_rotation = (st.session_state.upload_rotation - 90) % 360
        if rotate_right_upload:
            st.session_state.upload_rotation = (st.session_state.upload_rotation + 90) % 360
        if rotate_180_upload:
            st.session_state.upload_rotation = (st.session_state.upload_rotation + 180) % 360
        if reset_rotation_upload:
            st.session_state.upload_rotation = 0
        
        # Apply rotation and show preview for uploads
        if st.session_state.upload_rotation != 0:
            original_image = Image.open(file_upload)
            rotated_image = original_image.rotate(-st.session_state.upload_rotation, expand=True)
            
            # Convert rotated image back to bytes
            img_byte_array = io.BytesIO()
            rotated_image.save(img_byte_array, format='JPEG')
            img_byte_array.seek(0)
            
            # Create a file-like object for upload
            class RotatedImageFile:
                def __init__(self, byte_data):
                    self.byte_data = byte_data
                    
                def getvalue(self):
                    return self.byte_data.getvalue()
                    
                def read(self):
                    return self.byte_data.getvalue()
            
            uploaded_file = RotatedImageFile(img_byte_array)
            
            # Show current rotation
            st.info(f"🔄 Current rotation: {st.session_state.upload_rotation}° / वर्तमान घुमाव: {st.session_state.upload_rotation}°")
            st.image(rotated_image, caption="Rotated Image / घुमाई गई तस्वीर", width=300)
        else:
            uploaded_file = file_upload
            st.image(file_upload, caption="Original Image / मूल तस्वीर", width=300)

# Form Input
st.subheader("📝 Image Details / तस्वीर की जानकारी")

col1, col2 = st.columns(2)

with col1:
    variety = st.text_input(
        "🍏 Apple Variety / सेब की किस्म", 
        placeholder="e.g., Fuji, Gala, Kashmiri, Shimla",
        help="हिंदी: सेब की किस्म का नाम लिखें जैसे फूजी, गाला, कश्मीरी"
    )

with col2:
    location = st.text_input(
        "📍 Location / स्थान (optional/वैकल्पिक)", 
        placeholder="City, State / शहर, राज्य",
        help="हिंदी: आपका शहर या राज्य का नाम (यह भरना जरूरी नहीं)"
    )

# Preview uploaded image
if uploaded_file:
    st.subheader("🖼️ Final Image Preview / अंतिम तस्वीर का पूर्वावलोकन")
    # Only show preview if it's not already shown in rotation section
    if ('camera_rotation' not in st.session_state or st.session_state.camera_rotation == 0) and \
       ('upload_rotation' not in st.session_state or st.session_state.upload_rotation == 0):
        image = Image.open(uploaded_file)
        st.image(image, caption="Selected Image / चुनी गई तस्वीर", width=300)

# Submit button
if uploaded_file and st.button("🚀 Submit Image / तस्वीर सबमिट करें", type="primary"):
    if not variety.strip():
        st.error("❌ Please enter apple variety / कृपया सेब की किस्म भरें")
    else:
        try:
            with st.spinner("⏳ Uploading image... / तस्वीर अपलोड हो रही है..."):
                # Convert image to bytes if needed
                if hasattr(uploaded_file, 'getvalue'):
                    image_bytes = uploaded_file.getvalue()
                else:
                    # For camera input
                    image_bytes = uploaded_file.read()
                
                # Unique file name
                file_name = f"apples/{uuid.uuid4()}.jpg"
                
                # Upload to Firebase Storage
                blob = bucket.blob(file_name)
                blob.upload_from_string(image_bytes, content_type='image/jpeg')
                blob.make_public()  # Optional: make image accessible via URL
                image_url = blob.public_url
                
                # Save metadata to Firestore
                doc = {
                    "variety": variety.strip(),
                    "location": location.strip() if location.strip() else "Not specified",
                    "timestamp": datetime.utcnow(),
                    "image_url": image_url,
                    "file_name": file_name
                }
                db.collection("apple_images").add(doc)
                
                # Success message
                st.success("✅ Image uploaded successfully! / तस्वीर सफलतापूर्वक अपलोड हो गई!")
                st.balloons()
                
                # Show uploaded image
                st.image(image_url, caption=f"📸 Uploaded: {variety} / अपलोड की गई: {variety}", width=300)
                
                # Thank you message
                st.markdown("""
                ### 🙏 Thank you for your contribution! / आपके योगदान के लिए धन्यवाद!
                
                **English:** Your image has been successfully added to our apple dataset. This will help improve AI models for agricultural applications.
                
                **हिंदी:** आपकी तस्वीर हमारे सेब डेटासेट में सफलतापूर्वक जोड़ दी गई है। यह कृषि अनुप्रयोगों के लिए AI मॉडल को बेहतर बनाने में मदद करेगी।
                """)
                
        except Exception as e:
            st.error(f"❌ Error uploading image / तस्वीर अपलोड करते समय त्रुटि: {str(e)}")

# Footer
st.markdown("""
---
### 📊 **Dataset Statistics / डेटासेट आंकड़े**
Help us reach our goal of collecting diverse apple images from across India!
हमारे भारत भर से विविध सेब की तस्वीरें जमा करने के लक्ष्य में हमारी मदद करें!
""")

# Display current count (optional - requires additional Firestore query)
try:
    # Get count of documents in collection
    docs = db.collection("apple_images").limit(1).stream()
    count = len(list(docs))
    if count > 0:
        st.metric("📈 Total Images Collected / कुल एकत्रित तस्वीरें", count)
except:
    pass  # Handle if counting fails

st.markdown("""
---
**Contact[7876471141] / संपर्क:** For any queries, please reach out to our team.
किसी भी प्रश्न के लिए, कृपया हमारी टीम से संपर्क करें।
            TEAM UNISOLE
""")