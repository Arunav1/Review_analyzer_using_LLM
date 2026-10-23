import streamlit as st
from google import genai
from dotenv import load_dotenv

load_dotenv()

def generate_receipe(ingradients, cuisine, diet):
    prompt = f'''
    Generate one food receipe using these ingradients: {','.join(ingradients)}
    Receipe should not be more than 100 words, 
    Cuisine: {cuisine}, 
    diet: {diet}
    '''
    
    client = genai.Client()
    
    response = client.models.generate_content(
        model = "gemini-3.5-flash",
        contents = prompt
    )
    
    return response.text

st.title("Receipe Generator App")
st.write("Generate a receipe using ingradients you have !")


ingradients = st.multiselect(
    "Select your ingradients:", 
    ["potato", "tomato", "onion", "rice", "chicken", "egg", "cheese", "paneer", "garlic", "pasta"]
)

diet = st.selectbox(
    "choose your diet:", 
    ["vegeterian", "non-vegeterian", "keto", "vegan", "jain"]
)

cuisine = st.selectbox(
    "choose the cuisine:", 
    ["Indian", "Italian", "Chinese", "Mexican", "Thai"]
)

if st.button("Generate Receipe"):
    if not ingradients:
        st.warning("please select at least one ingradient")
    else:
        with st.spinner("Generate your receipe.."):
            try:
                receipe = generate_receipe(
                    ingradients, 
                    cuisine, 
                    diet
                )
                st.subheader("Your Receipe")
                st.write(receipe)
            except Exception as e:
                st.error(f"Something went wrong: {e}")
