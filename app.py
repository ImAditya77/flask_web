from flask import Flask, render_template, request, jsonify
import os
from groq import Groq
from datetime import datetime
from dotenv import load_dotenv
import logging
import traceback

# Load environment variables from .env
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Read API key from .env
API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    logger.error("GROQ_API_KEY not found in .env file")
    raise ValueError("GROQ_API_KEY environment variable not set")

# Initialize Groq client
try:
    client = Groq(api_key=API_KEY)
    logger.info("✅ Groq client initialized successfully")
except Exception as e:
    logger.exception("Failed to initialize Groq client")
    client = None

SUPPORTED_MODELS = [
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
    "meta-llama/llama-guard-4-12b",
    "openai/gpt-oss-120b"
]


@app.route('/')
def home():
    return render_template('index.html')


# Test endpoint
@app.route('/test_groq', methods=['GET'])
def test_groq():
    if not client:
        return jsonify({
            "ok": False,
            "error": "Groq client not initialized"
        }), 500

    try:
        response = client.chat.completions.create(
            model=SUPPORTED_MODELS[0],
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant."
                },
                {
                    "role": "user",
                    "content": "Reply with only OK"
                }
            ],
            temperature=0,
            max_tokens=10
        )

        return jsonify({
            "ok": True,
            "model": SUPPORTED_MODELS[0],
            "response": response.choices[0].message.content
        })

    except Exception as e:
        logger.exception("Groq test failed")
        return jsonify({
            "ok": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@app.route('/generate_roadmap', methods=['POST'])
def generate_roadmap():

    if not client:
        return jsonify({
            "error": "Groq client not initialized"
        }), 500

    interest = request.form.get("interest")

    if not interest:
        return jsonify({
            "error": "Interest field is required"
        }), 400

    last_error = None
    last_trace = None

    for model in SUPPORTED_MODELS:

        try:

            logger.info(f"Trying model: {model}")

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content":
                        """
                        You are an expert career mentor.

                        Create a complete learning roadmap.

                        The roadmap should include:

                        1. Beginner Stage
                        2. Intermediate Stage
                        3. Advanced Stage
                        4. Projects
                        5. Resources
                        6. Timeline
                        7. Career Opportunities

                        Use proper headings and bullet points.
                        """
                    },
                    {
                        "role": "user",
                        "content": f"Create a complete roadmap for learning {interest}"
                    }
                ],
                temperature=0.7,
                max_tokens=1500
            )

            roadmap = response.choices[0].message.content

            # Save roadmap
            os.makedirs("roadmaps", exist_ok=True)

            filename = f"roadmaps/roadmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

            with open(filename, "w", encoding="utf-8") as file:
                file.write(f"Interest: {interest}\n\n")
                file.write(roadmap)

            return jsonify({
                "roadmap": roadmap,
                "filename": filename,
                "model_used": model
            })

        except Exception as e:
            logger.exception(f"{model} failed")
            last_error = str(e)
            last_trace = traceback.format_exc()
            continue

    return jsonify({
        "error": "All models failed",
        "details": last_error,
        "traceback": last_trace
    }), 500


if __name__ == "__main__":
    app.run(debug=True)