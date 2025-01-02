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


@app.route("/login", methods=["GET", "POST"])
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


@app.route("/learn", methods=["GET", "POST"], endpoint="/learn")
@login_required
def learn():
    """
    Show basic stats and charts about the words in the database, and
    show flashcards picked randomly
    """

    if request.method == "GET":
        # Show stats and charts
        total_stats = db.select(
            "SELECT status FROM mapping WHERE user_id = ?", session["user_id"]
        )

        total = len(total_stats)
        new, known, unknown = 0, 0, 0

        for row in total_stats:
            if row["status"] == "new":
                new += 1
            elif row["status"] == "known":
                known += 1
            else:
                unknown += 1

        return render_template(
            "learn.html", total=total, new=new, known=known, unknown=unknown
        )

    elif request.method == "POST":
        # Call flashcard.html with a randomly generated flashcard if user pressed
        # the start learning button
        rand_card = Flashcard.get_random_flashcard(db, session["user_id"])
        return render_template("flashcard.html", flashcard=rand_card, learn=True)


@app.route("/create", methods=["GET", "POST"], endpoint="/create")
@login_required
def create():
    """
    Let user add words to their collection by entering a custom word or by
    choosing from a list of preset words
    """

    # Don't include any preset words that have already been added by the user
    exclude_ids = [
        val["card_id"]
        for val in db.select(
            "SELECT card_id FROM mapping WHERE user_id = ?", session["user_id"]
        )
    ]

    placeholders = ",".join(["?"] * len(exclude_ids))
    query = f"SELECT card_id, word FROM flashcards WHERE type = ? AND card_id NOT IN ({placeholders})"
    params = ["preset"] + list(exclude_ids)
    preset_words = db.select(query, *params)

    if request.method == "POST":
        card_type = request.form.get("type")
        if card_type == "preset":
            # Preset word chosen to be added
            card_id = request.form.get("card_id")
            # Add mapping to DB since flashcard already exists
            db.insert(
                "INSERT INTO mapping (user_id, card_id, status) VALUES (?,?,?)",
                session["user_id"],
                card_id,
                "new",
            )
            added_flashcard = Flashcard.load_from_db(db, card_id, session["user_id"])
            flash("Flashcard added successfully", category="success")
            return render_template(
                "flashcard.html", flashcard=added_flashcard, add_button=True
            )

        else:
            # Custom word chosen to be added
            word = request.form.get("word")
            if not word:
                # No word input
                flash("Enter a word", category="danger")
                return render_template("create.html", preset_words=preset_words)

            else:
                word_data = fetch_definition(word)
                if not word_data:
                    # Definition does not exist or API failed
                    flash(
                        f"{word} - definition could not be fetched", category="danger"
                    )
                    return render_template("create.html", preset_words=preset_words)

                else:
                    # Create flashcard from word and add to database
                    added_flashcard = Flashcard(word, word_data, "custom")
                    exists = added_flashcard.add_to_db(db, session["user_id"])
                    if exists:
                        flash("Flashcard already exists", category="danger")
                        return render_template("create.html", preset_words=preset_words)

                    else:
                        flash("Flashcard added successfully", category="success")
                        return render_template(
                            "flashcard.html", flashcard=added_flashcard, add_button=True
                        )

    return render_template("create.html", preset_words=preset_words)


@app.route("/flashcard", methods=["GET", "POST"])
@login_required
def flashcard():
    """
    Show flashcard with relevant information and buttons based on how the user
    reached the page
    """

    if request.form.get("view"):
        # User came from the manage page
        data = ast.literal_eval(request.form.get("view"))
        card_id = data["card_id"]
        card = Flashcard.load_from_db(db, card_id, session["user_id"])
        if not card:
            # Card does not exist - this should not happen
            flash(f"{card_id} does not exist - ERROR", category="danger")
            return redirect("/manage")

        else:
            return render_template(
                "flashcard.html", flashcard=card, learn=False, manage_button=True
            )

    elif request.form.get("answer"):
        # User came from another flashcard and is in the learning flow
        word = request.form.get("word")
        correct = request.form.get("answer")

        if correct == "correct":
            # Update status in DB to "known"
            Flashcard.update_status(db, word, session["user_id"], "known")

        elif correct == "incorrect":
            # Update status in DB to "not known"
            Flashcard.update_status(db, word, session["user_id"], "unknown")

        # Get the next random card from database to show
        random_card = Flashcard.get_random_flashcard(db, session["user_id"])
        return render_template("flashcard.html", flashcard=random_card, learn=True)

    return redirect("/")


@app.route("/manage", methods=["GET", "POST"], endpoint="manage")
@login_required
def manage():
    """
    Show all words that the user has already added to their collection and
    handle any calls to delete or view specific cards
    """

    if request.method == "GET":
        # User came from clicking a link or redirected to this page
        user_id = session["user_id"]
        # Select all words that the user already added
        all_words = db.select(
            "SELECT A.card_id, A.word, A.definitions, A.type, B.status FROM flashcards A LEFT JOIN mapping B ON A.card_id = B.card_id WHERE B.user_id = ?;",
            user_id,
        )
        words = []
        # Format words to pass as a jinja variable
        for row in all_words:
            data = {}
            data["card_id"] = row["card_id"]
            data["word"] = row["word"].capitalize()
            data["definitions"] = row["definitions"]
            data["type"] = row["type"].capitalize()
            data["status"] = row["status"].capitalize()
            words.append(data)
        return render_template("manage.html", words=words)

    elif request.method == "POST":
        # User came by clicking the delete button on one of the words
        data = ast.literal_eval(request.form.get("delete"))
        card_id = data["card_id"]
        Flashcard.delete_from_db(db, card_id, session["user_id"])
        flash("Flashcard deleted successfully", category="success")
        return redirect("/manage")

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
    result = _mint()
    return "Cert_Minted!: " + str(result)

@app.route("/new_chinese", methods=["GET"], endpoint="new_chinese")
#@login_required
def new_chinese():
    """
    Render Chinese learning cards gallery
    """
    return render_template("new_chinese.html")

if __name__ == "__main__":
     app.run(debug=True)
