import requests
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'change-this-to-a-real-secret-key'

BASEROW_URL = "https://baserow.intevoai.com/api/database/rows/table/684/"
BASEROW_TOKEN = "86aZji1ZIvGQ0hcgoi4I1qDWGiRWv7Bn"


def search_buyer(phone):
    response = requests.get(BASEROW_URL, headers={
        "Authorization": f"Token {BASEROW_TOKEN}"
    }, params={
        "user_field_names": "true",
        "filter__Buyer Phone__equal": phone
    })
    data = response.json()
    return data.get("results", [])


@app.route('/')
def home():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    phone = request.form.get('identifier', '').strip()
    if not phone:
        flash("Please enter your phone number.")
        return redirect(url_for('home'))

    results = search_buyer(phone)
    if not results:
        flash("No forms found against your number.")
        return redirect(url_for('home'))

    return redirect(url_for('dashboard', phone=phone))


@app.route('/dashboard/<phone>')
def dashboard(phone):
    results = search_buyer(phone)
    offers = []
    for row in results:
        offers.append({
            "name": row.get("file_name", "Untitled"),
            "link": row.get("link_to_offer", "#"),
            "type": row.get("document_type", {}).get("value", ""),
            "property": row.get("property") or "",
        })

    return render_template('dashboard.html', phone=phone, offers=offers)


if __name__ == '__main__':
    app.run(debug=True)
