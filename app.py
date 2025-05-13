import streamlit as st
from prompts import get_system_prompt, generate_tech_questions
from utils import validate_email, validate_phone
from dotenv import load_dotenv
import openai
import os
import re
load_dotenv()

def extract_name(text):
    patterns = [
        r"(?:my name is|i am|i'm) ([a-zA-Z\s]+)",
        r"([a-zA-Z\s]+) (?:here|speaking)",
        r"^([a-zA-Z\s]+)$"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            name = match.group(1).strip().title()
            return name if len(name) > 1 else None
    
    return None

def extract_email(text):
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(pattern, text)
    if match:
        email = match.group(0)
        if validate_email(email):
            return email
    return None

def extract_phone(text):
    pattern = r'(?:\+\d{1,3})?[\s\-\.]?\(?\d{1,4}\)?[\s\-\.]*\d{1,4}[\s\-\.]*\d{1,9}'
    match = re.search(pattern, text)
    if match:
        phone = match.group(0)
        if validate_phone(phone):
            return phone
    return None

def extract_experience(text):
    patterns = [
        r'(\d+)\s*(?:years|year|yrs|yr)(?:\s*of\s*experience|\s*experience)?',
        r'experience(?:\s*of)?\s*(\d+)\s*(?:years|year|yrs|yr)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return match.group(1)
    
    return None

def extract_confirmation(text):
    patterns = [
        r'\b(yes|yeah|yep|yup|sure|ok|okay|go ahead|proceed)\b',
        r'\b(no|nope|nah|not now|later)\b'
    ]
    
    text = text.lower()
    if re.search(patterns[0], text):
        return True
    elif re.search(patterns[1], text):
        return False
    return None

def parse_mcqs(questions_text):
    """Parse the MCQ questions from the text"""
    questions = []
    current_question = None
    options = []
    
    lines = questions_text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # New question starts with a number or "Question" prefix
        if re.match(r'^\d+\.|\bQ(uestion)?\s*\d+[\.\:]|^\[\d+\]', line):
            # Save previous question if exists
            if current_question and options:
                questions.append({
                    'question': current_question,
                    'options': options.copy(),
                    'correct_answer': None  # Will be set randomly or parsed later
                })
                
            # Extract the new question
            current_question = re.sub(r'^\d+\.|\bQ(uestion)?\s*\d+[\.\:]|^\[\d+\]', '', line).strip()
            options = []
        
        # Option line
        elif re.match(r'^[A-D][\)\.]|^- [A-D][\)\.]', line):
            option_text = re.sub(r'^[A-D][\)\.]\s*|- [A-D][\)\.]\s*', '', line).strip()
            options.append(option_text)
    
    # Add the final question
    if current_question and options:
        questions.append({
            'question': current_question,
            'options': options.copy(),
            'correct_answer': None  # Will be set randomly or parsed later
        })
    
    return questions

def extract_mcq_answer(text):
    """Extract option selection (A, B, C, D) from user input"""
    pattern = r'\b([A-Da-d])\b'
    match = re.search(pattern, text)
    if match:
        return match.group(1).upper()
    return None

def generate_response(user_input):
    if not st.session_state.conversation_started:
        if "hi" in user_input.lower() or "hello" in user_input.lower() or "hey" in user_input.lower():
            st.session_state.conversation_started = True
            return "Hello! Welcome to TalentScout. Could you please tell me your full name?"
        else:
            return "Hello! Please say 'hi' to start the conversation."
    
    elif not st.session_state.collected_info["name"]:
        name = extract_name(user_input)
        if name:
            st.session_state.collected_info["name"] = name
            return f"Nice to meet you, {name}! Could you please share your email address?"
        else:
            return "I didn't catch your name. Could you please tell me your full name?"
    
    elif not st.session_state.collected_info["email"]:
        email = extract_email(user_input)
        if email:
            st.session_state.collected_info["email"] = email
            return "Thanks! Now, could you please provide your phone number?"
        else:
            return "I need your email address to proceed. Please provide a valid email (example: name@example.com)."
    
    elif not st.session_state.collected_info["phone"]:
        phone = extract_phone(user_input)
        if phone:
            st.session_state.collected_info["phone"] = phone
            return "Great! How many years of professional experience do you have? (If you're a fresher, please say 'fresher' or '0')"
        else:
            return "I need your phone number to proceed. Please provide a valid phone number."
    
    elif not st.session_state.collected_info["experience"]:
        experience = extract_experience(user_input)
        if experience or "fresher" in user_input.lower():
            st.session_state.collected_info["experience"] = experience if experience else "0"
            return "Thanks! What is your current location?"
        else:
            return "I need to know your years of experience. Please specify a number (e.g., '3 years' or 'fresher')."
    
    elif not st.session_state.collected_info["location"]:
        location = user_input.strip()
        if location and len(location) > 1:
            st.session_state.collected_info["location"] = location
            return "What position are you applying for?"
        else:
            return "I need your current location to proceed. Please provide your city/country."
    
    elif not st.session_state.collected_info["position"]:
        position = user_input.strip()
        if position and len(position) > 1:
            st.session_state.collected_info["position"] = position
            questions_text = generate_tech_questions(position)
            
            # Parse the MCQs
            st.session_state.mcq_questions = parse_mcqs(questions_text)
            
            # Fallback questions if parsing fails or no questions generated
            if not st.session_state.mcq_questions:
                st.session_state.mcq_questions = [
                    {
                        'question': f"Which of the following is most important for a {position} role?",
                        'options': [
                            f"Technical expertise in {position}",
                            "Communication skills",
                            "Time management",
                            "Problem-solving ability"
                        ],
                        'correct_answer': None
                    },
                    {
                        'question': f"What methodology is commonly used in {position} projects?",
                        'options': [
                            "Agile",
                            "Waterfall",
                            "Scrum",
                            "Kanban"
                        ],
                        'correct_answer': None
                    },
                    {
                        'question': f"Which skill is most valuable for a {position}?",
                        'options': [
                            "Team collaboration",
                            "Attention to detail",
                            "Fast learning",
                            "Independent work"
                        ],
                        'correct_answer': None
                    },
                    {
                        'question': f"Which tool is most relevant for a {position}?",
                        'options': [
                            "Microsoft Office",
                            "Adobe Creative Suite",
                            "Programming IDEs",
                            "Project management software"
                        ],
                        'correct_answer': None
                    },
                    {
                        'question': f"What's the best approach to problem-solving as a {position}?",
                        'options': [
                            "Ask colleagues",
                            "Research solutions",
                            "Trial and error",
                            "Follow established procedures"
                        ],
                        'correct_answer': None
                    }
                ]
            
            # Limit to max 15 questions
            if len(st.session_state.mcq_questions) > 15:
                st.session_state.mcq_questions = st.session_state.mcq_questions[:15]
                
            # Set correct answers (in a real application, these would come from the API)
            import random
            for q in st.session_state.mcq_questions:
                q['correct_answer'] = random.choice(['A', 'B', 'C', 'D'])
            
            st.session_state.current_question_index = 0
            st.session_state.max_possible_score = len(st.session_state.mcq_questions)
            st.session_state.user_answers = []
            
            return f"Thank you for providing your information! I'd like to conduct a small screening test for the {position} position. Are you okay with that? (Please say 'yes' or 'no')"
        else:
            return "Please specify the position you're applying for."
    
    elif not st.session_state.test_confirmed:
        confirmation = extract_confirmation(user_input)
        if confirmation is True:
            st.session_state.test_confirmed = True
            current_q = st.session_state.mcq_questions[0]
            
            options_text = ""
            for i, opt in enumerate(current_q['options']):
                options_text += f"\n- {chr(65+i)}) {opt}"
            
            return f"Great! Let's begin the assessment.\n\nQuestion 1: {current_q['question']}{options_text}\n\nPlease select A, B, C, or D."
        elif confirmation is False:
            return "No problem. We can schedule this for later. A recruiter will contact you shortly. Have a great day!"
        else:
            return "I didn't understand. Are you okay with taking a small screening test for this position? (Please say 'yes' or 'no')"
    
    else:
        if st.session_state.current_question_index < len(st.session_state.mcq_questions):
            answer = extract_mcq_answer(user_input)
            
            if answer in ['A', 'B', 'C', 'D']:
                current_q = st.session_state.mcq_questions[st.session_state.current_question_index]
                correct = current_q['correct_answer'] == answer
                
                st.session_state.user_answers.append({
                    'question_index': st.session_state.current_question_index,
                    'user_answer': answer,
                    'correct': correct
                })
                
                st.session_state.current_question_index += 1
                
                if st.session_state.current_question_index < len(st.session_state.mcq_questions):
                    next_q = st.session_state.mcq_questions[st.session_state.current_question_index]
                    
                    options_text = ""
                    for i, opt in enumerate(next_q['options']):
                        options_text += f"\n- {chr(65+i)}) {opt}"
                    
                    return f"Thank you!\n\nQuestion {st.session_state.current_question_index + 1}: {next_q['question']}{options_text}\n\nPlease select A, B, C, or D."
                else:
                    # Calculate score
                    correct_answers = sum(1 for ans in st.session_state.user_answers if ans['correct'])
                    percentage = (correct_answers / st.session_state.max_possible_score) * 100
                    st.session_state.final_percentage = round(percentage, 1)
                    st.session_state.assessment_complete = True
                    
                    if percentage >= 60:
                        return f"Congratulations! You've completed the assessment with a score of {st.session_state.final_percentage}%. This is above our cutoff of 60%. A recruiter will contact you soon for the next steps. Thank you for your time!"
                    else:
                        return f"Thank you for completing the assessment. Your score is {st.session_state.final_percentage}%. Our cutoff score is 60%. We appreciate your interest and time."
            else:
                return "Please select a valid option (A, B, C, or D)."
        
        else:
            return "Your assessment is already complete. A recruiter will contact you shortly."

def set_custom_css():
    st.markdown("""
    <style>
 html, body, [class*="css"], div, p, span, h1, h2, h3, h4, h5, h6, 
.stTextInput, .stTextArea, .stButton, .stAlert, .stInfo, .stError, .stWarning, .stSuccess,
input, button, textarea, select, option, label, a, code, pre,
.stSidebar, .stMarkdown, .stText, .stCode, .stHeader, .stImage, .stNumber, .stProgress, .stChat, 
.stRadio, .stCheckbox, .stDataFrame, .stTable, .stJson, .stSlider, .stWidgetLabel,
.stPlotlyChart, .stSelectbox, .stMultiselect, .stDateInput, .stTimeInput, .stFileUploader,
.stExpander, .stTabs, .stTab, .stColorPicker, .stDownloadButton, .stForm {
    font-family: 'Times New Roman', Times, serif !important;
}
.assistant-message {
    background-color: #d1e6ff;
    color: #000000;
    border-radius: 15px;
    padding: 12px 15px;
    margin: 10px 0;
    max-width: 85%;
    float: left;
    clear: both;
    border-bottom-left-radius: 5px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    font-family: 'Times New Roman', Times, serif;
}

.user-message {
    background-color: #c7f0c7;
    color: #000000;
    border-radius: 15px;
    padding: 12px 15px;
    margin: 10px 0 10px auto;
    max-width: 85%;
    float: right;
    clear: both;
    border-bottom-right-radius: 5px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    font-family: 'Times New Roman', Times, serif;
}

.chat-container::after {
    content: "";
    clear: both;
    display: table;
}

div[data-testid="stVerticalBlock"] {
    gap: 15px !important;
}

div.stButton > button:first-child {
    background-color: #4CAF50;
    color: white;
    border: none;
    padding: 10px 18px;
    border-radius: 4px;
    transition: all 0.3s;
    font-family: 'Times New Roman', Times, serif;
    margin: 10px 0;
}

div.stButton > button:hover {
    background-color: #45a049;
    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
}

.stTextInput input, .stTextArea textarea {
    font-family: 'Times New Roman', Times, serif !important;
    padding: 10px !important;
    margin: 8px 0 !important;
    border-radius: 4px !important;
}

.score-meter {
    width: 100%;
    height: 24px;
    background-color: #e0e0e0;
    border-radius: 12px;
    margin: 15px 0;
    overflow: hidden;
}

.score-fill {
    height: 100%;
    border-radius: 12px;
    transition: width 1s ease-in-out;
}

.pass {
    background-color: #4CAF50;
}

.fail {
    background-color: #f44336;
}

.mcq-options {
    margin: 15px 0;
}

.mcq-option {
    margin: 8px 0;
    padding: 5px 0;
}

.sidebar .sidebar-content {
    font-family: 'Times New Roman', Times, serif !important;
    padding: 10px;
}

.sidebar h1, .sidebar h2, .sidebar h3, .sidebar h4 {
    margin-top: 20px;
    margin-bottom: 15px;
}

.detailed-scores {
    margin-top: 15px;
}

.score-item {
    margin: 8px 0;
    padding: 5px;
    border-radius: 4px;
}

.reset-button-container {
    margin-top: 40px;
    margin-bottom: 20px;
}

@media (prefers-color-scheme: dark) {
    .assistant-message {
        background-color: #2a4d7c;
        color: #ffffff;
        box-shadow: 0 1px 2px rgba(255,255,255,0.1);
    }

    .user-message {
        background-color: #1e4620;
        color: #ffffff;
        box-shadow: 0 1px 2px rgba(255,255,255,0.1);
    }

    .score-meter {
        background-color: #333333;
    }
    
    .stTextInput input, .stTextArea textarea {
        background-color: #262730 !important;
        color: #ffffff !important;
    }
    
    .score-meter {
        width: 100%;
        height: 20px;
        background-color: #e0e0e0;
        border-radius: 10px;
        margin-top: 10px;
        overflow: hidden;
    }
    
    .score-fill {
        height: 100%;
        border-radius: 10px;
        transition: width 1s ease-in-out;
    }
    
    .pass {
        background-color: #4CAF50;
    }
    
    .fail {
        background-color: #f44336;
    }
    
    .celebration {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 9999;
        animation: fadeOut 3s forwards;
    }
    
    @keyframes fadeOut {
        0% { opacity: 1; }
        80% { opacity: 1; }
        100% { opacity: 0; }
    }
    
    .confetti {
        position: absolute;
        width: 10px;
        height: 10px;
        background-color: #f44336;
        border-radius: 0;
        animation: fall 3s forwards;
    }
    
    @keyframes fall {
        0% { transform: translateY(-100px) rotate(0deg); opacity: 1; }
        100% { transform: translateY(calc(100vh + 100px)) rotate(720deg); opacity: 0; }
    }
    
    .reset-button-container {
        margin-top: 30px;
    }
    
    .mcq-options {
        margin-top: 8px;
        margin-bottom: 8px;
    }
    
    .mcq-option {
        margin-top: 2px;
        margin-bottom: 2px;
    }
    
    @media (prefers-color-scheme: dark) {
        .assistant-message {
            background-color: #2a4d7c;
            color: #ffffff;
            box-shadow: 0 1px 2px rgba(255,255,255,0.1);
        }
        
        .user-message {
            background-color: #1e4620;
            color: #ffffff;
            box-shadow: 0 1px 2px rgba(255,255,255,0.1);
        }
        
        .score-meter {
            background-color: #333333;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def display_score_animation():
    st.markdown("""
    <div id="confetti-container" class="celebration"></div>
    
    <script>
    function createConfetti() {
        const container = document.getElementById('confetti-container');
        const colors = ['#f44336', '#2196f3', '#ffeb3b', '#4caf50', '#9c27b0'];
        
        for (let i = 0; i < 100; i++) {
            setTimeout(() => {
                const confetti = document.createElement('div');
                confetti.className = 'confetti';
                confetti.style.left = Math.random() * 100 + 'vw';
                confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
                confetti.style.width = (Math.random() * 10 + 5) + 'px';
                confetti.style.height = (Math.random() * 10 + 5) + 'px';
                confetti.style.animationDuration = (Math.random() * 2 + 2) + 's';
                container.appendChild(confetti);
                
                setTimeout(() => {
                    confetti.remove();
                }, 3000);
            }, i * 50);
        }
    }
    
    if (window.score_percentage >= 60) {
        createConfetti();
    }
    </script>
    """, unsafe_allow_html=True)

def custom_chat_message(role, content):
    if role == "assistant":
        st.markdown(f'<div class="chat-container"><div class="assistant-message">{content}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-container"><div class="user-message">{content}</div></div>', unsafe_allow_html=True)

def main():
    st.set_page_config(page_title="TalentScout Hiring Assistant", page_icon="🤖")
    set_custom_css()
    
    st.title("TalentScout Hiring Assistant")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
        greeting = "Hello! Welcome to TalentScout. Please say 'hi' to start the conversation."
        st.session_state.messages.append({"role": "assistant", "content": greeting})
        st.session_state.conversation_started = False
    
    if "collected_info" not in st.session_state:
        st.session_state.collected_info = {
            "name": None,
            "email": None,
            "phone": None,
            "position": None,
            "experience": None,
            "location": None
        }
        st.session_state.test_confirmed = False
        st.session_state.assessment_complete = False
        st.session_state.final_percentage = 0
    
    with st.sidebar:
        st.header("Assessment Score")
        
        if st.session_state.collected_info["name"]:
            st.write(f"**Candidate:** {st.session_state.collected_info['name']}")
        if st.session_state.collected_info["position"]:
            st.write(f"**Position:** {st.session_state.collected_info['position']}")
        
        if st.session_state.test_confirmed and not st.session_state.assessment_complete:
            if hasattr(st.session_state, 'current_question_index') and hasattr(st.session_state, 'mcq_questions'):
                progress = st.session_state.current_question_index / len(st.session_state.mcq_questions)
                st.progress(progress, text=f"Question {st.session_state.current_question_index}/{len(st.session_state.mcq_questions)}")
        
        if st.session_state.assessment_complete:
            st.subheader(f"Final Score: {st.session_state.final_percentage}%")
            passed = st.session_state.final_percentage >= 60
            result_text = "PASSED" if passed else "FAILED"
            result_color = "green" if passed else "red"
            
            st.markdown(f"<h3 style='color:{result_color};'>Status: {result_text}</h3>", unsafe_allow_html=True)
            
            score_class = "pass" if passed else "fail"
            st.markdown(f"""
            <div class="score-meter">
                <div class="score-fill {score_class}" style="width:{st.session_state.final_percentage}%"></div>
            </div>
            <p>Cutoff: 60%</p>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <script>
                window.score_percentage = {st.session_state.final_percentage};
            </script>
            """, unsafe_allow_html=True)
            
            if hasattr(st.session_state, 'user_answers'):
                with st.expander("Detailed Scores", expanded=False):
                    for i, answer_data in enumerate(st.session_state.user_answers):
                        q_index = answer_data['question_index']
                        question = st.session_state.mcq_questions[q_index]['question']
                        result = "✅ Correct" if answer_data['correct'] else "❌ Incorrect"
                        st.write(f"**Q{q_index+1}:** {question[:40]}... - **Your answer:** {answer_data['user_answer']} - {result}")
        
        st.markdown("<div class='reset-button-container'></div>", unsafe_allow_html=True)
        
        with st.form(key='reset_form'):
            reset_submitted = st.form_submit_button("Reset Conversation")
            if reset_submitted:
                st.session_state.messages = []
                st.session_state.collected_info = {k: None for k in st.session_state.collected_info}
                st.session_state.conversation_started = False
                st.session_state.test_confirmed = False
                st.session_state.assessment_complete = False
                st.session_state.final_percentage = 0
                if hasattr(st.session_state, 'user_answers'):
                    del st.session_state.user_answers
                if hasattr(st.session_state, 'mcq_questions'):
                    del st.session_state.mcq_questions
                if hasattr(st.session_state, 'current_question_index'):
                    del st.session_state.current_question_index
                st.session_state.reset_requested = True
    
    if st.session_state.assessment_complete and st.session_state.final_percentage >= 60:
        display_score_animation()
    
    if st.session_state.get('reset_requested', False):
        greeting = "Hello! Welcome to TalentScout. Please say 'hi' to start the conversation."
        st.session_state.messages.append({"role": "assistant", "content": greeting})
        st.session_state.reset_requested = False
        st.rerun()
    
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            custom_chat_message(message["role"], message["content"])
    
    if prompt := st.chat_input("Type your message here..."):
        exit_keywords = ["exit", "quit", "goodbye", "bye", "stop", "end"]
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        custom_chat_message("user", prompt)
        
        if any(keyword in prompt.lower() for keyword in exit_keywords):
            farewell = "Thank you for your time! A recruiter will review your information and get back to you shortly. Have a great day!"
            st.session_state.messages.append({"role": "assistant", "content": farewell})
            custom_chat_message("assistant", farewell)
        else:
            response = generate_response(prompt)
            st.session_state.messages.append({"role": "assistant", "content": response})
            custom_chat_message("assistant", response)
        st.rerun()

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        st.warning("Please set the OPENAI_API_KEY environment variable to use this application.")
    main()