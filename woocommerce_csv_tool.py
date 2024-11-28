import pandas as pd
import streamlit as st
import itertools

# Web app to create WooCommerce products data
st.title("WooCommerce Product CSV Generator")

# List to store multiple products
if 'products' not in st.session_state:
    st.session_state['products'] = []
products = st.session_state['products']

# Product counter
st.write(f"Total Products Added: {len(products)}")

# File uploader to load existing CSV
uploaded_file = st.file_uploader("Upload an existing product CSV to update", type=["csv"])
if uploaded_file is not None:
    df_existing = pd.read_csv(uploaded_file)
    products.extend(df_existing.to_dict(orient='records'))
    st.success("CSV file loaded successfully and products have been added to the list!")

# SKU input
sku = st.text_input("SKU", key='sku_main_input')

# Dropdown for Product Type
product_type = st.selectbox("Product Type", ["Simple", "Variable"])

# Image upload and link generation
image_pattern = st.text_input("Enter image path pattern (e.g., 'www.miosito.it/wp-content/upload/{mese}/{anno}/')")
product_image = st.file_uploader("Upload Product Image", type=["jpg", "png", "jpeg"])
if product_image and image_pattern:
    image_name = product_image.name
    image_link = image_pattern + image_name
    st.write(f"Generated Image Link: {image_link}")
else:
    image_link = ""

# Basic product information
title = st.text_input("Product Title")
short_description = st.text_area("Short Description")
description = st.text_area("Product Description")

# Category input with memory
if 'categories' not in st.session_state:
    st.session_state['categories'] = set()

category = st.text_input("Product Category (you can add multiple categories separated by commas)")
if category:
    categories = [cat.strip() for cat in category.split(',')]
    st.session_state['categories'].update(categories)
    category = ', '.join(categories)

# Attributes for variations
attributes = []
variations = []
if product_type == "Simple":
    # Price and Weight for Simple products
    price = st.text_input("Price", key='simple_price')
    weight = st.text_input("Weight", key='simple_weight')
elif product_type == "Variable":
    num_attributes = st.number_input("Number of Attributes", min_value=1, max_value=5, step=1, value=1)
    for i in range(int(num_attributes)):
        attribute_name = st.text_input(f"Attribute {i+1} Name", key=f'attr_name_{i}')
        attribute_values = st.text_input(f"Attribute {i+1} Values (comma separated)", key=f'attr_values_{i}')
        attributes.append({"name": attribute_name, "values": attribute_values.split(",")})

    # Generate variations based on attributes
    attribute_combinations = list(itertools.product(*[attr['values'] for attr in attributes]))
    for idx, combination in enumerate(attribute_combinations):
        variation = {attributes[i]['name']: value.strip() for i, value in enumerate(combination)}
        variation['Price'] = st.text_input(f"Price for variation {', '.join(combination)}", key=f"price_{idx}")
        variation['Weight'] = st.text_input(f"Weight for variation {', '.join(combination)}", key=f"weight_{idx}")
        variation['Description'] = st.text_area(f"Description for variation {', '.join(combination)}", key=f"description_{idx}")
        variation_image = st.file_uploader(f"Upload Image for variation {', '.join(combination)}", type=["jpg", "png", "jpeg"], key=f"variation_image_{idx}")
        if variation_image and image_pattern:
            variation_image_name = variation_image.name
            variation_image_link = image_pattern + variation_image_name
            variation['Image Link'] = variation_image_link
        else:
            variation['Image Link'] = ""
        variations.append(variation)

# Add product to list
if st.button("Add Product"):
    if product_type == "Simple":
        product_data = {
            "Product Title": title,
            "Short Description": short_description,
            "Description": description,
            "Category": category,
            "Product Type": product_type,
            "Price": price,
            "Weight": weight,
            "SKU": sku,
            "Image Link": image_link
        }
        products.append(product_data)
    elif product_type == "Variable":
        # Add summary row for variable product
        summary_data = {
            "Product Title": title,
            "Short Description": short_description,
            "Description": description,
            "Category": category,
            "Product Type": product_type,
            "SKU": sku,
            "Image Link": image_link
        }
        for i, attr in enumerate(attributes):
            summary_data[f"Attribute {i+1} Name"] = attr["name"]
            summary_data[f"Attribute {i+1} Values"] = ", ".join(attr["values"])
            summary_data[f"Attribute {i+1} Description"] = ""  # Placeholder for attribute description
        products.append(summary_data)

        # Add each variation as a separate row
        for variation in variations:
            product_data = {
                "Product Title": title,
                "Short Description": "",  # Leave blank for variations
                "Description": "",  # Leave blank for variations
                "Category": "",  # Leave blank for variations
                "Product Type": "Variation",
                "Image Link": variation["Image Link"],
                "Tax Status": "parent",  # Adding hidden value for tax status
                "SKU": "",  # Leave SKU empty for variations
                "Price": variation["Price"],
                "Weight": variation["Weight"]
            }
            for i, attr in enumerate(attributes):
                product_data[f"Attribute {i+1} Name"] = attr["name"]
                product_data[f"Attribute {i+1} Values"] = variation.get(attr["name"], "")
                product_data[f"Attribute {i+1} Description"] = variation["Description"] if i == 0 else ""
            products.append(product_data)
    st.success("Product added successfully!")

# Export to CSV
if st.button("Export to CSV"):
    if products:
        df = pd.DataFrame(products)
        # Add hidden columns with default values
        df["Pubblicato"] = 0  # Set Pubblicato to 0 for all rows
        df["Visibilità"] = 0
        df["In Stock"] = 1
        df["Ordini arretrati"] = 0
        df["Venduto singolarmente"] = 0
        df["Permetti le recensioni ai clienti"] = 0
        df["Attributi 1 visibile"] = df["Product Type"].apply(lambda x: 0 if x == "Variable" else "")
        df["Attributi 1 globale"] = df["Product Type"].apply(lambda x: 0 if x in ["Variable", "Variation"] else "")
        df["Genitore"] = df.apply(lambda row: sku if row["Product Type"] == "Variation" else "", axis=1)
        df["In Primo Piano"] = 0
        df["Stato delle imposte"] = "Taxable"
        df["Aliquote"] = df.apply(lambda row: "parent" if row["Product Type"] == "Variation" else "", axis=1)

        # Reorder columns based on the provided order
        columns_order = [
            "SKU", "Product Type", "Product Title", "Pubblicato", "In Primo Piano", "Visibilità",
            "Short Description", "Description", "Stato delle imposte", "Aliquote", "In Stock",
            "Ordini arretrati", "Venduto singolarmente", "Weight", "Permetti le recensioni ai clienti",
            "Price", "Category", "Genitore"
        ]

        # Adding attribute columns dynamically to the order
        attribute_columns = [
            col for col in df.columns if "Attribute" in col
        ]
        columns_order.extend(attribute_columns)
        columns_order.append("Image Link")

        # Ensure newlines are preserved in descriptions during CSV export
        df = df[columns_order]
        st.download_button(label="Download CSV", data=df.to_csv(index=False, lineterminator='\n').encode('utf-8'), file_name="woocommerce_products.csv", mime="text/csv")
        st.success("CSV file with all products has been generated!")
    else:
        st.warning("No products to export. Please add at least one product.")

# Clear product list
if st.button("Clear Product List"):
    if st.checkbox("Are you sure you want to clear the product list? This action cannot be undone."):
        products.clear()
        st.session_state['products'] = []
        st.write(f"Total Products Added: {len(products)}")
        st.success("Product list has been cleared.")
