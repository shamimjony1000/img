import streamlit as st
import google.generativeai as genai
import pandas as pd
from dotenv import load_dotenv
import os
import json
from PIL import Image
import io

# Load environment variables
load_dotenv()

# Configure Gemini Pro
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-pro')

def process_image(uploaded_file):
    try:
        # Convert UploadedFile to PIL Image
        image = Image.open(uploaded_file)
        
        # Convert PIL Image to bytes for Gemini
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=image.format)
        img_byte_arr = img_byte_arr.getvalue()

        # Prepare the prompt for Gemini
        prompt = """
        Extract all text from this image. If the image contains tabular data:
        1. Identify the rows and columns
        2. Return the data in a structured JSON format with column headers
        3. Preserve the exact layout and relationships between data points
        Format the response as valid JSON that can be parsed.
        """
        
        # Get response from Gemini
        response = model.generate_content([prompt, {"mime_type": f"image/{image.format.lower()}", "data": img_byte_arr}])
        
        # Extract JSON from response
        response_text = response.text
        # Find JSON content between ```json and ``` if present
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        else:
            json_str = response_text.strip()
            
        # Parse JSON to dict
        data = json.loads(json_str)
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        st.error(f"Error processing image: {str(e)}")
        return None

def main():
    st.title("Shamim MD Jony's Image to Excel for Prachine Bangla")
    st.write("Upload an image containing text or tabular data to convert it to Excel format")
    
    # File uploader
    uploaded_file = st.file_uploader("Choose an image file", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file is not None:
        # Display the uploaded image
        st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
        
        # Process button
        if st.button("Process Image"):
            with st.spinner("Processing image..."):
                # Process the image
                df = process_image(uploaded_file)
                
                if df is not None:
                    # Display the extracted data
                    st.write("Extracted Data:")
                    st.dataframe(df)
                    
                    # Create Excel file in memory
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False)
                    excel_data = excel_buffer.getvalue()
                    
                    # Download button
                    st.download_button(
                        label="Download Excel file",
                        data=excel_data,
                        file_name="extracted_data.xlsx",
                        mime="application/vnd.ms-excel"
                    )

if __name__ == "__main__":
    main()