import streamlit as st
import sys
import os
import random
from pathlib import Path
from datetime import datetime

# Add backend directory to Python path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if backend_path not in sys.path:
    sys.path.append(backend_path)

from question_generator import QuestionGenerator
from question_store import QuestionStore

# Page config
st.set_page_config(
    page_title="Japanese Learning Assistant",
    page_icon="🎌",
    layout="wide"
)

# Initialize question store
if 'question_store' not in st.session_state:
    st.session_state.question_store = QuestionStore()

# Initialize session state
if 'current_question' not in st.session_state:
    # Initialize with first question
    question_generator = QuestionGenerator()
    generated_content = question_generator.generate_question_json(4, "daily conversation")
    if generated_content and "generated_question" in generated_content:
        st.session_state.current_question = generated_content["generated_question"][0]
        # Save the first question
        st.session_state.question_store.save_question("daily conversation", st.session_state.current_question)
        st.session_state.answered = False
        st.session_state.button_state = "check"

def render_header():
    """Render the header section"""
    st.title("🎌 Japanese Learning Assistant")
    st.markdown("""
    Transform your Japanese learning experience with interactive practice questions.
    Practice JLPT N5 level conversations and test your understanding!
    """)

def format_timestamp(timestamp_str):
    """Format timestamp for display"""
    dt = datetime.fromisoformat(timestamp_str)
    return dt.strftime("%Y-%m-%d %H:%M")

def render_question_sidebar():
    """Render sidebar with previous questions"""
    with st.sidebar:
        st.header("Previous Questions")
        questions = st.session_state.question_store.get_all_questions()
        
        for q in questions:
            # Create a unique key for each button using the question ID
            intro = q['question_data'].get('introduction', '')  # Safely get introduction
            if st.button(
                f"[{format_timestamp(q['timestamp'])}] {intro[:30]}...",
                key=f"q_{q['id']}"
            ):
                st.session_state.current_question = q['question_data']
                st.session_state.answered = False
                st.session_state.button_state = "check"
                st.rerun()

def render_interactive_learning():
    """Render the interactive learning stage"""
    # Initialize question generator
    question_generator = QuestionGenerator()
    
    # Context selection for question generation
    context = st.selectbox(
        "Select Context",
        ["daily conversation", "shopping", "restaurant", "school", "travel"]
    )
    
    # Generate new question button
    if st.button("Generate New Question"):
        # Store the generated question in session state
        question_type = 4  # Default to type 4 for dialogue practice
        generated_content = question_generator.generate_question_json(question_type, context)
        if generated_content and "generated_question" in generated_content:
            st.session_state.current_question = generated_content["generated_question"][0]
            # Save the new question
            st.session_state.question_store.save_question(context, st.session_state.current_question)
            st.session_state.answered = False
            st.session_state.button_state = "check"
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Practice Scenario")
        if "current_question" in st.session_state and st.session_state.current_question:
            # Display introduction and conversation
            st.write("**Situation:**")
            st.write(st.session_state.current_question.get("introduction", ""))
            st.write("**Dialogue:**")
            st.write(st.session_state.current_question.get("conversation", ""))
            st.write("**Question:**")
            st.write(st.session_state.current_question.get("question", ""))
            
            # Randomly shuffle options
            if "shuffled_options" not in st.session_state or st.session_state.get("last_question") != st.session_state.current_question.get("question", ""):
                options = st.session_state.current_question.get("options", []).copy()
                random.shuffle(options)
                st.session_state.shuffled_options = options
                st.session_state.last_question = st.session_state.current_question.get("question", "")
            
            selected = st.radio("Choose your answer:", st.session_state.shuffled_options)
            
            # Add space after radio buttons
            st.write("")
            
            # Button logic
            button_label = "Next Question ➡️" if st.session_state.button_state == "next" else "Check Answer"
            if st.button(button_label):
                if st.session_state.button_state == "check":
                    # Check answer logic
                    st.session_state.answered = True
                    st.session_state.correct = (selected == st.session_state.current_question.get("answer", ""))
                    if st.session_state.correct:
                        st.session_state.button_state = "next"
                else:
                    # Generate new question logic
                    question_type = 4  # Default to type 4 for dialogue practice
                    generated_content = question_generator.generate_question_json(question_type, context)
                    if generated_content and "generated_question" in generated_content:
                        st.session_state.current_question = generated_content["generated_question"][0]
                        # Save the new question
                        st.session_state.question_store.save_question(context, st.session_state.current_question)
                        st.session_state.answered = False
                        st.session_state.button_state = "check"
                st.rerun()
            
            # Add space after button
            st.write("")
            
            # Show feedback below button
            if "answered" in st.session_state and st.session_state.answered:
                if st.session_state.correct:
                    st.markdown("### 🎯 Perfect!")
                    st.markdown("""
                    <div style='padding: 10px; border-radius: 5px; background-color: #d4edda; color: #155724; margin: 20px 0;'>
                        ✨ Great understanding! Ready for the next question?
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("### 📚 Keep Learning!")
                    st.markdown(f"""
                    <div style='padding: 10px; border-radius: 5px; background-color: #fff3cd; color: #856404; margin: 20px 0;'>
                        💡 Correct answer: {st.session_state.current_question.get("answer", "")}
                    </div>
                    """, unsafe_allow_html=True)
        
    with col2:
        st.subheader("Audio")
        st.info("🎵 Audio feature coming soon!")
        
        st.subheader("Feedback")
        st.info("🤖 Detailed feedback and explanations coming soon!")

def main():
    render_header()
    render_question_sidebar()
    render_interactive_learning()

if __name__ == "__main__":
    main()