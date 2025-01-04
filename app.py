import time
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from database import DataBase
from utils import login_required
import ast
from config import DATABASE
import os
from mint import _mint
from llm_call import _llm_call
from vlm_call import generate_image

from PIL import Image
from io import BytesIO
import requests
import os
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

DEBUG = os.getenv("STUDYJOB_DEBUG", False)

app = Flask(__name__)
# Store session information on the filesystem of the local machine
# Not cleared when restarting the application
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = DataBase(DATABASE)

with app.app_context():
    # Initialize DB at the start of the application
    #initialize_db.init(db)
    # Delete session files from local machine to enforce no data persists
    # on app restart. This can be used but I am not sure if this is the best
    # and safest way to enforce this.
    for file in os.listdir("./flask_session"):
        os.remove(f"./flask_session/{file}")


@app.route("/", endpoint="/")
def home():
    """
    Render home page of application
    """
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"], endpoint="/register")
def register():
    """
    Authenticate the information entered by the user and save credentials
    to the database
    """

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username or not password or not confirmation:
            # Check if any fields are empty
            flash("Enter all fields", category="danger")
            return render_template("register.html")

        if len(db.select("SELECT * from users WHERE username = ?", username)) > 0:
            # Check if username already exists
            flash("User already exists with this username", category="danger")
            return render_template("register.html")

        elif password != confirmation:
            # Check if password and confirmation match
            flash("Passwords do not match", category="danger")
            return render_template("register.html")

        else:
            # Save credentials to DB and register the user
            db.insert(
                "INSERT INTO users (username, password) VALUES (?,?)",
                username,
                password,
            )
            flash("You were successfully registered", category="success")
            return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"], endpoint="/login")
def login():
    """
    Authenticate information entered by the user with the information saved
    in the database and log the user in
    """

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            # Check if any fields are empty
            flash("Input all fields", category="danger")
            return render_template("login.html")

        # Query database for username
        user_info = db.select(
            "SELECT * from users WHERE username = ? AND password = ?",
            username,
            password,
        )

        if len(user_info) == 0:
            # No such user exists
            flash("Invalid username or password", category="danger")
            return render_template("login.html")

        else:
            # Remember which user has logged in
            session["user_id"] = user_info[0]["user_id"]
            session["username"] = user_info[0]["username"]
            flash("You were successfully logged in", category="success")
            return redirect("/")

    else:
        return render_template("login.html")


@app.route("/logout", methods=["GET"])
def logout():
    """
    Log user out by clearing information stored in the session
    """
    session.clear()
    flash("You were successfully logged out", category="success")
    return redirect("/")

@app.route("/dailyword", methods=["GET"], endpoint="/dailyword")
#@login_required
def dailyword():
    """
    Render dailyword page of application
    """
    api_base = os.getenv("OPENAI_API_BASE")
    key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_API_MODEL", "Qwen/Qwen2.5-7B-Instruct")

    prompt = "Generate a random Chinese word along with its pinyin and English translation in structured JSON format. json only, nothing else. format: {chinese_word: <chinese_word>, pinyin: <pinyin>, english_translation: <english_translation>}"
    result = _llm_call(api_base, key, model, prompt)

    res=ast.literal_eval(result)

    chinese_word = res["chinese_word"]
    pinyin = res["pinyin"]
    english_translation = res["english_translation"]

    return render_template("dailyword.html", chinese_word=chinese_word, pinyin=pinyin, english_translation=english_translation)

@app.route("/infographics", methods=["GET"], endpoint="/infographics")
#@login_required
def infographics():
    """
    Render infographics page of application
    """

    def string_validate(s):
        """Validate and clean the input string."""
        if not isinstance(s, str):
            return ""
        # Remove control characters and strip the string
        cleaned = ''.join(c for c in s if c.isprintable())
        # Truncate to 50 characters
        return cleaned[:50]

    translation = "Translation"
    root_explanation = "Root explanation goes here."
    memory_story = "A story to help remember the word."
    example_sentence = "Example sentence using the word."
    image_url = "wangchangling1_300_100.png"

    word = request.args.get("word")
    if word:
        # Check if the word is already in the flashcards2 table
        cached_data = db.select("SELECT * FROM flashcards2 WHERE word = ?", word)

        if cached_data:
            # Fetch the data from the database
            cached_data = cached_data[0]
            translation = cached_data["translation"]
            root_explanation = string_validate(cached_data["root_explanation"])
            memory_story = string_validate(cached_data["memory_story"])
            example_sentence = string_validate(cached_data["example_sentence"])
            image_url = cached_data["image_url"]
        else:
            api_base = os.getenv("OPENAI_API_BASE")
            key = os.getenv("OPENAI_API_KEY")
            model = os.getenv("OPENAI_API_MODEL", "Qwen/Qwen2.5-7B-Instruct")

            prompt = f"Given the user input English {word}, generate its Chinese translation, root_explanation, memory_story, example_sentence in structured JSON format. json only, nothing else. format: {{word: <word>, translation: <translation>, root_explanation: <root_explanation>, memory_story: <memory_story>, example_sentence: <example_sentence>}}. Make sure the length of each <root_explanation>, <memory_story>, <example_sentence> does not exceed 50. Make sure all generated items are valid text, do not contain control characters. root_explanation explains roots and etymology of the English word in Chinese. example_sentence is English text."
            result = _llm_call(api_base, key, model, prompt)

            print(result)
            res = ast.literal_eval(result)

            translation = res["translation"]
            root_explanation = string_validate(res["root_explanation"])
            memory_story = string_validate(res["memory_story"])
            example_sentence = string_validate(res["example_sentence"])

            prompt = f"{memory_story}"
            image_url = generate_image(prompt)
            print(image_url)

            if image_url:

                # Download the image
                response = requests.get(image_url)
                image = Image.open(BytesIO(response.content))

                # Resize the image
                width = int(request.args.get("width", image.width))
                height = int(request.args.get("height", image.height))
                image = image.resize((width, height))

                # Save the image to a file with a timestamp
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                image_url = f"{word}_{timestamp}.png"
                image_path = os.path.join('static/images/', image_url)
                image.save(image_path)

                # Save the data to the flashcards2 table
                db.insert(
                    "INSERT INTO flashcards2 (word, translation, root_explanation, memory_story, example_sentence, image_url) VALUES (?,?,?,?,?,?)",
                    word,
                    translation,
                    root_explanation,
                    memory_story,
                    example_sentence,
                    image_url
                )
    else:
        word = "Word"

    return render_template("infographics.html", word=word, translation=translation, root_explanation=root_explanation, memory_story=memory_story, example_sentence=example_sentence, image_url=image_url)

@app.route("/poem", methods=["GET"], endpoint="poem")
#@login_required
def poem():
    """
    Render poetry gallery page
    """
    return render_template("poem.html")

@app.route("/mint", methods=["GET"], endpoint="mint")
#@login_required
def mint():
    """
    Render mint page of application
    """
    if not DEBUG:
        result = _mint()
    else:
        time.sleep(5)  # Simulate a 5 second delay
        result = 1

    return "NFT minted: " + str(result)

@app.route("/new_chinese", methods=["GET"], endpoint="new_chinese")
#@login_required
def new_chinese():
    """
    Render Chinese learning cards gallery
    """
    return render_template("new_chinese.html")

@app.route("/explore", methods=["GET"], endpoint="explore")
#@login_required
def explore():
    """
    Render combined Chinese learning and poetry gallery
    """
    return render_template("explore.html")

if __name__ == "__main__":
     app.run(debug=True)
