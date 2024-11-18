import streamlit as st
import google.generativeai as genai
import pandas as pd
from dotenv import load_dotenv
import os
import json
from PIL import Image
import io



# Configure Gemini Pro
genai.configure(api_key="AIzaSyCLyDgZNcE_v4wLMFF8SoimKga9bbLSun0")
model = genai.GenerativeModel('gemini-1.5-pro')

def process_image(uploaded_file):
    try:
        # Convert UploadedFile to PIL Image
        image = Image.open(uploaded_file)
        
        # Convert PIL Image to bytes for Gemini
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=image.format)
        img_byte_arr = img_byte_arr.getvalue()

        # Updated prompt to include Pack Size column
        prompt = """
        Extract the medicine price list data from this image into a structured format.
        For each row, capture ONLY these specific columns in exactly this order:
        1. SL (Serial Number) - First column
        2. Product (Medicine Name) - Second column
        3. Generic (Composition) - Third column
        4. Strength - Fourth column
        5. Pack Size - Fifth column
        6. Trade Price - Sixth column
        7. Vatable Price - Seventh column

        IMPORTANT: Extract exactly these 7 columns in this order. Ignore any columns after the 7th column.

        Return the data in this JSON format:
        {
            "data": [
                {
                    "sl": "",
                    "product": "",
                    "generic": "",
                    "strength": "",
                    "pack_size": "",
                    "trade_price": "",
                    "vatable_price": ""
                }
            ]
        }
        
        Critical instructions:
        - Extract ONLY the first 7 columns from the table
        - Preserve all numerical values exactly as shown
        - Include all rows from the image
        - Maintain the exact sequence of these 7 columns
        - For Pack Size, include both number and unit (e.g., '30's', '100 ml')
        """
        
        # Get response from Gemini
        response = model.generate_content([prompt, {"mime_type": f"image/{image.format.lower()}", "data": img_byte_arr}])
        
        # Extract JSON from response
        response_text = response.text
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        else:
            json_str = response_text.strip()
            
        # Parse JSON to dict
        data = json.loads(json_str)
        
        # Convert to DataFrame
        df = pd.DataFrame(data['data'])
        
        # Clean up the DataFrame
        df = df.replace('', pd.NA).dropna(how='all', axis=1)
        
        # Rename columns to match the desired format
        column_mapping = {
            'sl': 'SL',
            'product': 'Product',
            'generic': 'Generic',
            'strength': 'Strength',
            'pack_size': 'Pack Size',
            'trade_price': 'Trade Price',
            'vatable_price': 'Vatable Price'
        }
        df = df.rename(columns=column_mapping)
        
        return df
    
    except Exception as e:
        st.error(f"Error processing image: {str(e)}")
        return None

def main():
    st.title("Medicine Price List Extractor")
    st.write("Upload an image of the medicine price list to extract data in the following order:")
    st.write("1. SL (Serial Number)")
    st.write("2. Product")
    st.write("3. Generic")
    st.write("4. Strength")
    st.write("5. Pack Size")
    st.write("6. Trade Price")
    st.write("7. Vatable Price")
    
    # File uploader
    uploaded_file = st.file_uploader("Choose an image file", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file is not None:
        # Display the uploaded image
        st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
        
        # Process button
        if st.button("Extract Price List"):
            with st.spinner("Processing image..."):
                # Process the image
                df = process_image(uploaded_file)
                
                if df is not None:
                    # Display the extracted data
                    st.write("Extracted Price List:")
                    st.dataframe(df)
                    
                    # Create Excel file in memory
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='Price List')
                        
                        # Auto-adjust column widths
                        worksheet = writer.sheets['Price List']
                        for idx, col in enumerate(df.columns):
                            max_length = max(
                                df[col].astype(str).apply(len).max(),
                                len(col)
                            )
                            worksheet.column_dimensions[chr(65 + idx)].width = max_length + 2
                    
                    excel_data = excel_buffer.getvalue()
                    
                    # Download button
                    st.download_button(
                        label="Download Price List Excel",
                        data=excel_data,
                        file_name="medicine_price_list.xlsx",
                        mime="application/vnd.ms-excel"
                    )

if __name__ == "__main__":
    main()
