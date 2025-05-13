# TalentScout Hiring Assistant

## Project Overview
TalentScout Hiring Assistant is an intelligent chatbot designed to assist recruitment agencies in the initial screening of candidates. The assistant collects essential candidate information and generates relevant technical questions based on the candidate's declared tech stack.

## Features
- User-friendly Streamlit interface for candidate interaction
- Collection of essential candidate details:
  - Full Name
  - Email Address
  - Phone Number
  - Years of Experience
  - Desired Position(s)
  - Current Location
  - Tech Stack
- Smart data extraction using regex patterns
- Generation of tailored technical questions based on the candidate's tech stack
- Context-aware conversation flow
- Clean display of collected information in the sidebar

## Installation Instructions

### Prerequisites
- Python 3.8 or higher
- OpenAI API key

### Setup
1. Clone the repository or download the project files

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install streamlit openai python-dotenv
```

4. Create a `.env` file in the project root directory with your OpenAI API key:
```
OPENAI_API_KEY=your_openai_api_key_here
```

5. Run the application:
```bash
streamlit run app.py
```

## Usage Guide
1. Launch the application using the command above
2. The assistant will greet you and ask for your name
3. Follow the conversation flow to provide all required information
4. Once all information is collected, the assistant will generate technical questions based on your tech stack
5. Answer the questions and type 'done' when finished
6. The assistant will conclude the conversation
7. Use the "Reset Conversation" button in the sidebar to start over

## Project Structure
- `app.py`: Main application file with Streamlit UI and conversation logic
- `prompts.py`: Contains functions for system prompts and technical question generation
- `utils.py`: Utility functions for data validation

## Technical Details

### Libraries Used
- **Streamlit**: For the web interface
- **OpenAI**: For generating intelligent responses and technical questions
- **python-dotenv**: For loading environment variables
- **re**: For regular expression pattern matching

### Architecture
The application follows a simple architecture:
1. User input collection via Streamlit chat interface
2. Information extraction using regex patterns
3. State management using Streamlit session state
4. Technical question generation using OpenAI API
5. Dynamic response generation based on conversation context

## Challenges & Solutions

### Challenge 1: Robust Information Extraction
**Solution**: Implemented multiple regex patterns for each type of information to handle various input formats and styles.

### Challenge 2: OpenAI API Integration
**Solution**: Created a dedicated function to handle API calls with proper error handling and fallback mechanisms.

### Challenge 3: Maintaining Conversation Context
**Solution**: Used Streamlit's session state to store and track collected information and conversation history.

### Challenge 4: User Experience
**Solution**: Implemented a clean sidebar display of collected information and added a reset button for better user control.

## Future Enhancements
- Multi-language support
- Sentiment analysis during conversations
- Integration with database systems
- Support for file uploads (resumes, portfolios)
- Advanced analytics on candidate responses

## License
This project is for demonstration purposes only.