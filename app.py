from flask import Flask, render_template, request
import random
import csv
from datetime import datetime, timezone

app = Flask(__name__)
application = app


# Load quiz data from CSV file
def load_quiz_data():
    quiz_data = []
    with open("data.csv", newline="") as csvfile:
        csvreader = csv.DictReader(csvfile)
        for row in csvreader:
            quiz_data.append(row)
    return quiz_data


# Get questions for a specific chapter
def get_questions_for_chapter(chapter_number):
    quiz_data = load_quiz_data()
    chapter_questions = [q for q in quiz_data if q["chapter_number"] == chapter_number]

    # Randomly select up to 10 questions
    return (
        random.sample(chapter_questions, 15)
        if len(chapter_questions) >= 15
        else chapter_questions
    )


def save_score_to_csv(chapter_number, chapter_name, total_questions, final_score):
    # Get the current time in UTC format (ISO 8601 string)
    quiz_date = datetime.now(timezone.utc).isoformat()

    # Define the file name for historical data
    filename = "quiz_scores.csv"

    # Check if the file exists to determine if we need to write headers
    file_exists = False
    try:
        with open(filename, "r"):
            file_exists = True
    except FileNotFoundError:
        file_exists = False

    # Write to the CSV file
    with open(filename, "a", newline="") as file:
        writer = csv.writer(file)
        # Write header if it's a new file
        if not file_exists:
            writer.writerow(
                [
                    "quiz_date",
                    "chapter_number",
                    "chapter_name",
                    "total_questions",
                    "final_score",
                ]
            )

        # Write the new quiz result
        writer.writerow(
            [quiz_date, chapter_number, chapter_name, total_questions, final_score]
        )


# Home route (Index page)
@app.route("/")
def home():
    quiz_data = load_quiz_data()

    # Extract unique chapters
    chapters = {}
    for row in quiz_data:
        chapter_number = row["chapter_number"]
        chapter_name = row["chapter_name"]
        if chapter_number not in chapters:
            chapters[chapter_number] = chapter_name

    # Create a list of chapters with hyperlinks
    chapter_links = [{"number": num, "name": name} for num, name in chapters.items()]

    # Load historical scores
    historical_scores = []
    try:
        with open("quiz_scores.csv", "r") as file:
            reader = csv.DictReader(file)
            historical_scores = [row for row in reader]
    except FileNotFoundError:
        pass  # No file found, no data to show

    # Pass the historical data and available chapters to the template
    return render_template(
        "index.html",
        title="CBAP Quiz",
        chapter_links=chapter_links,
        historical_scores=historical_scores,
    )


# Quiz route for specific chapter
@app.route("/quiz/<chapter_number>", methods=["GET"])
def quiz(chapter_number):
    questions = get_questions_for_chapter(chapter_number)
    return render_template(
        "quiz.html", chapter_number=chapter_number, questions=questions
    )


# Route to handle quiz submission and calculate score
@app.route("/submit_quiz/<chapter_number>", methods=["POST"])
def submit_quiz(chapter_number):
    # Retrieve the 10 questions for this chapter
    questions = get_questions_for_chapter(chapter_number)

    chapter_name = questions[0][
        "chapter_name"
    ]  # Assuming all questions are from the same chapter
    score = 0

    # Iterate through the questions to calculate the score
    for index, question in enumerate(questions, start=1):
        correct_answer = question["correct_answer"]
        selected_answer = request.form.get(f"question_{index}")

        # Check if the selected answer matches the correct answer
        if selected_answer == correct_answer:
            score += 1

    # Save the quiz result to the CSV file
    save_score_to_csv(chapter_number, chapter_name, len(questions), score)

    # Render the score page
    return render_template("score.html", score=score, total=len(questions))


if __name__ == "__main__":
    app.run(debug=True)
