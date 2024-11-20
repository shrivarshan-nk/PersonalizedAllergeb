import streamlit as st
from PIL import Image
import easyocr
import pandas as pd
import re
from rapidfuzz import fuzz, process



# Initialize EasyOCR reader
reader = easyocr.Reader(['en'])

# Load datasets directly from your local files
@st.cache_data
def load_data():
    # Update the file paths to the locations of your datasets
    allergen_file = "C:/Users/shriv/PersonalisedAllergen/food1.xlsx"  # Replace with your file path
    chemical_file = "C:/Users/shriv/PersonalisedAllergen/food.xlsx"  # Replace with your file path
    
    allergens = pd.read_excel(allergen_file).to_dict(orient='records')
    chemicals = pd.read_excel(chemical_file).to_dict(orient='records')
    return allergens, chemicals

# Load the allergen and chemical datasets
allergen_dataset, chemical_dataset = load_data()

# Preprocess OCR text
def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z,]', ' ', text)
    ingredients = re.split(r',| and |&', text)
    ingredients = [ingredient.strip() for ingredient in ingredients]
    return ingredients

# Match ingredients against a dataset
def match_ingredients(ingredients, dataset, proc, threshold=80):
    matched_items = []
    
    for item in dataset:
        if proc==0:
            match = process.extractOne(item['Name'], ingredients, scorer=fuzz.partial_ratio)
            if match and match[1] >= threshold:
                matched_items.append((item['Name'], match[0], match[1], item))
        else:
            match_ing = process.extractOne(item['Mentioned As in Ingredients'], ingredients, scorer=fuzz.partial_ratio)
            if match_ing and match_ing[1] >= threshold:
                matched_items.append((item['Mentioned As in Ingredients'], match_ing[0], match_ing[1], item))
    return matched_items

# Streamlit app
st.title("📢 Robust Allergen and Additive Scanner")
st.write("""
### Ensure Your Food is Safe!
Upload an image of the ingredient list, and we'll notify you of allergens and harmful chemicals.
""")

# Sidebar for user allergen input
st.sidebar.header("Your Allergen Profile")
user_allergens = st.sidebar.multiselect(
    "Select your allergens:",
    options=[item['Name'] for item in allergen_dataset],
    default=[]
)

# File uploader for ingredient list image
uploaded_file = st.file_uploader("📷 Upload Ingredient List Image", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption='Uploaded Image', use_container_width=True)

    if st.button("🔍 Scan Ingredients"):
        with st.spinner("Processing..."):
            # Extract text using OCR
            extracted_text = reader.readtext(image, detail=0)
            extracted_text = " ".join(extracted_text)

            st.subheader("📝 Extracted Ingredients:")
            st.write(extracted_text)

            # Preprocess text
            ingredients = preprocess_text(extracted_text)
            st.subheader("📃 Parsed Ingredients:")
            st.write(ingredients)

            # Match against allergens
            if user_allergens:
                allergen_matches = match_ingredients(ingredients, 
                                                      [item for item in allergen_dataset if item['Name'] in user_allergens],proc=0)
                if allergen_matches:
                    st.error("⚠️ **Allergen(s) Detected!**")
                    for allergen, matched_ingredient, score, details in allergen_matches:
                        st.write(f"- **{allergen.title()}** detected as (Confidence: {score}%)")
                        st.write(f"  - Type: {details['Type']}")
                        st.write(f"  - Possible Allergies: {details['Possible Allergies']}")
                else:
                    st.success("✅ **No Allergens Detected!**")

            # Match against chemicals/additives
            additive_matches = match_ingredients(ingredients, chemical_dataset,proc=1)
            if additive_matches:
                st.warning("⚠️ **Potentially Harmful Additives Found:**")
                for name, matched_ingredient, score, details in additive_matches:
                    st.write(f"- **{name}** detected as *{matched_ingredient}* (Confidence: {score}%)")
                    st.write(f"  - Type: {details['Type']}")
                    st.write(f"  - Ingredient Source: {details['Source']}")
                    st.write(f"  - Potential Harm: {details['Potential Harm']}")
            else:
                st.info("✅ **No Harmful Additives Found.**")

else:
    st.info("Please upload an image of the ingredient list to get started.")
