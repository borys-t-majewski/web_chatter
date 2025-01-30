

# Security Chatbot

## Made for Hackathon: Agenton 2025

Task outline:
In an increasingly connected world, conversations—whether online or over the phone—can often become avenues for social engineering attacks and data exploitation. The "Conversational Security Agent" task seeks to educate users on the subtle risks posed by seemingly innocuous conversations while empowering them to identify and resist social engineering tactics in real-world scenarios.

## Setup & Installation

1. Install dependencies:

pip install -r requirements.txt

2. Configure OpenAI API key in .env file:

OPENAI_API_KEY=sk-proj-....


3. Optional: Adjust model parameters in constants.py:

TEMPERATURE = 0.1

model = "gpt-4o-mini"

It's expected to run well in gpt-4o-mini or better, and only supports open ai models.

## Running the Application

1. Run app_with_tracking.py in your IDE

2. Open http://localhost:5000 in your browser

3. Follow the instructions below chatbot to interact with it.
