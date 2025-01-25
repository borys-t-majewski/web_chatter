# Security Chatbot

## Setup & Installation

1. Install dependencies:

pip install -r requirements.txt
or
pip install -r requirements_minimum.txt

2. Configure OpenAI API key in .env file:

OPENAI_API_KEY=sk-proj-....


3. Optional: Adjust model parameters in constants.py:

TEMPERATURE = 0.2git 

model = "gpt-4o-mini"

It's expected to run well in gpt-4o-mini or better, and only supports open ai models.

## Running the Application

1. Run app_with_tracking.py in your IDE

2. Open http://localhost:5000 in your browser

3. You should see a chatbot interface - use instructions are below it.
