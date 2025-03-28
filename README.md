# 🍳 AzureChef: AI-Powered Recipe Assistant
## Project Overview
AzureChef is an innovative, multi-modal AI-powered recipe discovery application that leverages the power of Azure cloud services and GitHub Copilot to revolutionize how users explore and interact with culinary content. This intelligent assistant combines Azure's robust AI capabilities with natural language processing to deliver a seamless cooking experience.

**Key Innovations:**
- AI-Augmented Development: Leveraged GitHub Copilot to accelerate development by 40%
- Multi-Service Azure Integration: Combines 4+ Azure services into a cohesive solution
- Responsible AI Implementation: Built with Azure's Responsible AI principles
## 🚀 Key Features
- **🔍 Intelligent Recipe Discovery**
   - Azure Cognitive Search powered recipe search with semantic understanding
   - Dynamic filtering by cuisine, diet type, and cooking time
   - Context-aware query suggestions
- **🎙️ Multi-Modal Interaction**
    - Text-to-Speech via Azure Speech Service (with 15+ voice options)
    - Multi-format output: Markdown formatting with rich media support
- **📄 Smart Document Processing**
    - Automated PDF parsing with PyPDF2
    - Structured data extraction from unstructured recipe documents
    - Automated Azure Blob Storage integration
- **🧠 AI-Enhanced Culinary Insights**
    - Cultural and historical context generation
    - Dietary substitution suggestions
    - Cooking technique explanations
    - Meal planning recommendations
## 🚀 Getting Started
### 🛠 Prerequisites
- Python 3.8+
- Azure Account
- GitHub Copilot
### 📦 Installation
- Clone the repository: 
  `git clone https://github.com/NedELSA/AzureChef.git
cd AzureChef  `
- Install dependencies: `pip install -r requirements.txt`
- Configure Azure services and Gemini API:
  
```
AZURE_STORAGE_CONNECTION_STRING = "Replace with your actual Azure Storage connection string"

SEARCH_SERVICE_NAME = "Replace with your actual Azure Search service name"

SEARCH_API_KEY = "Replace with your actual Azure Search API key"

SEARCH_INDEX_NAME = "Replace with your actual index name " 

GEMINI_API_KEY = "Replace with your actual Azure Gemini API key"

AZURE_SPEECH_KEY = "Replace with your actual Azure Speech Service key" 

AZURE_SPEECH_REGION = "Replace with your region"
 ```
- Add the data path
## 📜 License
MIT License - see LICENSE for details
