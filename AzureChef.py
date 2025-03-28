import PyPDF2
import io
import re
import uuid
import gradio as gr
import os
import azure.cognitiveservices.speech as speechsdk
from azure.storage.blob import BlobServiceClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchableField,
    SearchFieldDataType
)
import google.generativeai as genai
import traceback
# Azure and Gemini Credentials
AZURE_STORAGE_CONNECTION_STRING = "Replace with your actual Azure Storage connection string"
SEARCH_SERVICE_NAME = "Replace with your actual Azure Search service name"
SEARCH_API_KEY = "Replace with your actual Azure Search API key"
SEARCH_INDEX_NAME = "Replace with your actual index name " 
GEMINI_API_KEY = "Replace with your actual Azure Gemini API key"  
AZURE_SPEECH_KEY = "Replace with your actual Azure Speech Service key"  
AZURE_SPEECH_REGION = "Replace with your region"  

class ChefAssistantGradio:
    def __init__(self):
        # Create the new index with filterable category
        self.create_new_index()

        # Initialize Azure Search Client
        self.search_client = SearchClient(
            endpoint=f"https://{SEARCH_SERVICE_NAME}.search.windows.net/",
            index_name=SEARCH_INDEX_NAME,
            credential=AzureKeyCredential(SEARCH_API_KEY))

        # Initialize Gemini
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

        # Index some sample data (you should replace this with your actual data indexing logic)
        self.index_sample_data()
# Initialize Azure Speech Configuration
        self.speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
        self.speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"  # Choose a suitable voice
    
   
    def text_to_speech(self, text):
  
        """Convert text to speech and save as an audio file"""
        try:
            # Validate input text
            if not text or len(text.strip()) == 0:
                print("No text provided for text-to-speech conversion")
                return None

            # Prepare audio output
            audio_filename = f"output_{uuid.uuid4()}.wav"
            
            # Create audio output configuration
            audio_config = speechsdk.audio.AudioOutputConfig(filename=audio_filename)
            
            # Create speech synthesizer
            speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config, 
                audio_config=audio_config
            )
            
            # Synthesize text to speech
            result = speech_synthesizer.speak_text_async(text).get()
            
            # Check result
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                print(f"Speech synthesized to [{audio_filename}]")
                return audio_filename
            else:
                print(f"Error synthesizing. Result: {result.reason}")
                print(f"Error details: {result.error_details}")
                return None
        
        except Exception as e:
            print(f"Text-to-speech error: {str(e)}")
            traceback.print_exc()  # This will print the full traceback
            return None
        
    def create_new_index(self):
        """Create a new index with filterable category field"""
        index_client = SearchIndexClient(
            endpoint=f"https://{SEARCH_SERVICE_NAME}.search.windows.net/",
            credential=AzureKeyCredential(SEARCH_API_KEY))

        # Define the index fields with filterable category
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(name="recipe_name", type=SearchFieldDataType.String),
            SearchableField(name="ingredients", type=SearchFieldDataType.String),
            SearchableField(name="quantities", type=SearchFieldDataType.String),
            SimpleField(name="cooking_time", type=SearchFieldDataType.String),
            SearchableField(name="steps", type=SearchFieldDataType.String),
            SimpleField(name="cuisine", type=SearchFieldDataType.String),
            SimpleField(name="diet_type", type=SearchFieldDataType.String),
            SimpleField(name="category", type=SearchFieldDataType.String, filterable=True)
        ]

        # Create the index
        index = SearchIndex(name=SEARCH_INDEX_NAME, fields=fields)
        try:
            index_client.create_index(index)
            print(f"Created new index '{SEARCH_INDEX_NAME}' with filterable category")
        except Exception as e:
            print(f"Error creating index: {str(e)}")

   
    def index_sample_data(self):
        """Index recipes from PDF files in the data directory"""
        data_dir = "Replace with your actual data directory path"
        
        # Initialize Azure Blob Service Client
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client("recipes")
        
        # Process each PDF file
        pdf_files = [f for f in os.listdir(data_dir) if f.endswith('.pdf')]
        
        for pdf_file in pdf_files:
            try:
                pdf_path = os.path.join(data_dir, pdf_file)
                category = os.path.splitext(pdf_file)[0]  # e.g. "appetizers"
                
                # Extract text from PDF
                with open(pdf_path, "rb") as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    extracted_text = ""
                    
                    for page in pdf_reader.pages:
                        extracted_text += page.extract_text() + "\n\n"
                
                # Parse recipes from the extracted text
                recipes = self.parse_recipe(extracted_text, category)
                
                if recipes:
                    # Upload to Azure Search
                    result = self.search_client.upload_documents(documents=recipes)
                    print(f"Indexed {len(recipes)} recipes from {category}")
                    
            except Exception as e:
                print(f"Error processing {pdf_file}: {str(e)}")
#parce recipe function
    def parse_recipe(self, text, category):
        """Parse recipe text into structured data"""
        recipe_blocks = re.split(r'(?:Recipe Name:|RECIPE NAME:)', text)
        recipes = []
        
        for block in recipe_blocks:
            if not block.strip():
                continue

            try:
                recipe_id = str(uuid.uuid4())
                
                # Extract components with flexible patterns
                recipe_name = re.search(r'^(.*?)(?:Ingredients:|INGREDIENTS:|$)', block, re.IGNORECASE | re.DOTALL)
                recipe_name = recipe_name.group(1).strip() if recipe_name else "Unknown Recipe"

                ingredients = re.search(r'(?:Ingredients:|INGREDIENTS:)(.*?)(?:Quantities:|QUANTITIES:|$)', block, re.IGNORECASE | re.DOTALL)
                ingredients = ingredients.group(1).strip() if ingredients else ""

                quantities = re.search(r'(?:Quantities:|QUANTITIES:)(.*?)(?:Cooking Time:|COOKING TIME:|$)', block, re.IGNORECASE | re.DOTALL)
                quantities = quantities.group(1).strip() if quantities else ""

                cooking_time = re.search(r'(?:Cooking Time:|COOKING TIME:)(.*?)(?:Steps:|STEPS:|$)', block, re.IGNORECASE | re.DOTALL)
                cooking_time = cooking_time.group(1).strip() if cooking_time else ""

                steps = re.search(r'(?:Steps:|STEPS:)(.*?)(?:Cuisine:|CUISINE:|$)', block, re.IGNORECASE | re.DOTALL)
                steps = steps.group(1).strip() if steps else ""

                cuisine = re.search(r'(?:Cuisine:|CUISINE:)(.*?)(?:Diet Type:|DIET TYPE:|$)', block, re.IGNORECASE | re.DOTALL)
                cuisine = cuisine.group(1).strip() if cuisine else ""

                diet_type = re.search(r'(?:Diet Type:|DIET TYPE:)(.*?)(?:$)', block, re.IGNORECASE | re.DOTALL)
                diet_type = diet_type.group(1).strip() if diet_type else ""

                if recipe_name != "Unknown Recipe" and (ingredients or steps):
                    recipe = {
                        "id": recipe_id,
                        "recipe_name": recipe_name,
                        "ingredients": ingredients,
                        "quantities": quantities,
                        "cooking_time": cooking_time,
                        "steps": steps,
                        "cuisine": cuisine,
                        "diet_type": diet_type,
                        "category": category
                    }
                    recipes.append(recipe)
                    
            except Exception as e:
                print(f"Error parsing recipe block in {category}: {e}")

        return recipes


    def search_recipes(self, query, category, top=5):
        """Search for recipes in Azure AI Search"""
        try:
            if category and category != "All Categories":
                search_results = list(self.search_client.search(
                    query, 
                    filter=f"category eq '{category}'", 
                    top=top
                ))
            else:
                search_results = list(self.search_client.search(query, top=top))

            return search_results
        except Exception as e:
            print(f"Error searching recipes: {str(e)}")
            return []

    def generate_recipe_markdown(self, search_results, query):
        """Generate formatted markdown for recipe results"""
        if not search_results:
            return "Sorry, no recipes found for your query. Try different keywords!"

        markdown_output = f"## Recipe Results for '{query}'\n\n"
        
        for i, result in enumerate(search_results, 1):
            markdown_output += f"### {i}. {result['recipe_name']}\n\n"
            markdown_output += f"**Category**: {result['category']}\n\n"
            markdown_output += f"**Ingredients**:\n{result['ingredients']}\n\n"
            markdown_output += f"**Quantities**:\n{result['quantities']}\n\n"
            markdown_output += f"**Cooking Time**: {result['cooking_time']}\n\n"
            markdown_output += f"**Preparation Steps**:\n{result['steps']}\n\n"
            markdown_output += f"**Cuisine**: {result.get('cuisine', 'N/A')}\n\n"
            markdown_output += f"**Diet Type**: {result['diet_type']}\n\n"
            markdown_output += "---\n\n"

        return markdown_output

    
  
    def generate_ai_response(self, query, search_results):
        """Generate AI-enhanced response with text-to-speech support"""
        if not search_results:
            no_results_text = "I couldn't find any recipes matching your query. Would you like to try a different search?"
            audio_file = self.text_to_speech(no_results_text)
            return no_results_text, audio_file

        # Extract recipe names for listing
        recipe_names = [result['recipe_name'] for result in search_results]

        formatted_results = ""
        for i, result in enumerate(search_results, 1):
            formatted_results += f"**Recipe {i}: {result['recipe_name']}**\n"
            formatted_results += f"- **Category**: {result['category']}\n"
            formatted_results += f"- **Ingredients**: {result['ingredients']}\n"
            formatted_results += f"- **Quantities**: {result['quantities']}\n"
            formatted_results += f"- **Cooking Time**: {result['cooking_time']}\n"
            formatted_results += f"- **Steps**: {result['steps']}\n"
            formatted_results += f"- **Cuisine**: {result.get('cuisine', 'N/A')}\n"
            formatted_results += f"- **Diet Type**: {result['diet_type']}\n\n"

        prompt = f"""
        You are a friendly, knowledgeable chef assistant with a passion for culinary history and recipe exploration.

        User Query: "{query}"

        Recipes Found:
        {formatted_results}

        Historical and Culinary Context:
        - Interpret the query's culinary significance
        - Provide brief historical background of the recipe type or related cuisine
        - Connect the recipe to cultural or traditional cooking practices

        Response Guidelines:
        1. Begin with a warm, engaging introduction
        2. Include a brief culinary or cultural history related to the recipe type
        3. Highlight the first recipe in detail
        4. If multiple recipes match:
            - Mention the names of the first 3 recipes
            - Invite the user to request more details about other recipes
        5. Provide professional cooking tips and variations
        6. Offer nutritional insights or health benefits
        7. Suggest potential substitutions or customizations
        8. End with an inviting question to encourage further interaction
        9. Use markdown formatting
        10. Maintain an enthusiastic, conversational tone

        If Found Multiple Recipes:
        - Names of matched recipes: {", ".join(recipe_names[:3])}
        - Emphasize the user can ask for more details about these or other recipes

        Make the response feel like a conversation with a passionate chef who loves sharing culinary knowledge and stories.
        """

        try:
            # Generate AI response text
            response = self.model.generate_content(prompt)
            ai_response_text = response.text

            # Convert text to speech
            audio_file = self.text_to_speech(ai_response_text)

            # Return both text and audio file
            return ai_response_text, audio_file

        except Exception as e:
            error_text = f"I couldn't generate an AI response at the moment. Let's try again! Error: {str(e)}"
            audio_file = self.text_to_speech(error_text)
            return error_text, audio_file

def create_gradio_interface():
    """Modified Gradio interface to support audio output"""
    chef_assistant = ChefAssistantGradio()

    # Categories dropdown
    categories = [
        "All Categories", "appetizers", "dessert", 
        "juices", "main_dishes", "salade", "snacks"
    ]

    def search_and_generate(query, category):
        # Search recipes
        search_results = chef_assistant.search_recipes(query, category)
        
        # Generate AI-enhanced response and audio
        ai_response, audio_file = chef_assistant.generate_ai_response(query, search_results)
        
        # Explicit audio file check
        if not audio_file:
            print("No audio file generated")
            audio_file = None  # Ensure Gradio gets None if no file
        
        return ai_response, audio_file

    # Custom CSS for the background image and centered title
    custom_css = f"""
    .gradio-container {{
        background-image: url('file=replace_with_your_background_image_path.jpg');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    .gradio-app {{
        background-color: rgba(255, 255, 255, 0.8);
        padding: 20px;
        border-radius: 10px;
    }}
    .centered-title {{
        text-align: center;
        width: 100%;
        font-size: 24px !important;
        margin-bottom: 20px !important;
    }}
    """

    # Gradio Interface
    with gr.Blocks(title="Chef Assistant", theme="default", css=custom_css) as demo:
        # Centered title with custom CSS class
        gr.Markdown(
            """<div class="centered-title">🍳 AzureChef: From Code to Kitchen – AzureChef's Got Your Recipe!</div>""",
            elem_classes=["centered-title"]
        )
        
        with gr.Row():
            query_input = gr.Textbox(label="What would you like to cook?", placeholder="Enter a recipe, ingredient, or cuisine...")
            category_dropdown = gr.Dropdown(choices=categories, label="Category", value="All Categories")
        
        search_btn = gr.Button("Search Recipes", variant="primary")
        
        with gr.Column():
            gr.Markdown("## 👨‍🍳 AzureChef Recommendations")
            ai_response_output = gr.Markdown()
            audio_output = gr.Audio()  # Add audio output component
        
        search_btn.click(
            fn=search_and_generate, 
            inputs=[query_input, category_dropdown], 
            outputs=[ai_response_output, audio_output]
        )

        # Example queries
        gr.Examples(
            examples=[
                ["Chocolate Dessert", "dessert"],
                ["Chicken Dishes", "main_dishes"],
                ["Quick Salad", "salade"],
                ["Vegetarian", "All Categories"]
            ],
            inputs=[query_input, category_dropdown],
            fn=search_and_generate,
            outputs=[ai_response_output, audio_output],
            cache_examples=True
        )

    return demo

if __name__ == "__main__":
    demo = create_gradio_interface()
    demo.launch(share=True)