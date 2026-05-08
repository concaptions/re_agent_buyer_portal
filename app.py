import secrets
import uuid
import requests
from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = 'change-this-to-a-real-secret-key'

BASEROW_BUYER_TABLE_URL = "https://baserow.intevoai.com/api/database/rows/table/684/"
BASEROW_AGENT_TABLE_URL = "https://baserow.intevoai.com/api/database/rows/table/687/"
BASEROW_TOKEN = "86aZji1ZIvGQ0hcgoi4I1qDWGiRWv7Bn"


def search_buyer(phone):
    response = requests.get(BASEROW_BUYER_TABLE_URL, headers={
        "Authorization": f"Token {BASEROW_TOKEN}"
    }, params={
        "user_field_names": "true",
        "filter__Buyer Phone__equal": phone
    })
    data = response.json()
    return data.get("results", [])


@app.route('/')
def home():
    return render_template('landing.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    phone = request.form.get('identifier', '').strip()
    if not phone:
        flash("Please enter your phone number.")
        return redirect(url_for('login'))

    results = search_buyer(phone)
    if not results:
        flash("No forms found against your number.")
        return redirect(url_for('login'))

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


# ============================================================
# Agent Sign-up Wizard (mirrors the n8n RE Agent Registration workflow)
# ============================================================

def _store_form(form):
    data = session.get("signup_data", {})
    for key, value in form.items():
        data[key] = value.strip() if isinstance(value, str) else value
    session["signup_data"] = data


def _to_int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def create_agent_row(data):
    """POST collected agent data to Baserow table 687 using field IDs."""
    full_name = f"{data.get('Agent First Name', '')} {data.get('Agent Last Name', '')}".strip()

    payload = {
        "field_6686": data.get("Agent First Name"),
        "field_6688": True,
        "field_6689": data.get("Agent Phone Number"),
        "field_6690": data.get("Default Option Fee"),
        "field_6763": data.get("Office Address"),
        "field_6764": data.get("DBA"),
        "field_6766": data.get("Brokerage Phone Number"),
        "field_6767": data.get("Brokerage Email"),
        "field_6768": data.get("Brokerage Firm Name"),
        "field_6769": data.get("Brokerage License Number"),
        "field_6771": data.get("Designated Supervisor"),
        "field_6772": data.get("Supervisor Email"),
        "field_6773": data.get("Supervisor Phone Number"),
        "field_6774": full_name,
        "field_6775": data.get("Agent Email"),
        "field_6776": data.get("Agent Phone Number"),
        "field_6777": data.get("Team Name (If any)"),
        "field_6779": _to_int(data.get("Default Option Period (days)")),
        "field_6780": _to_int(data.get("Standard survey preference (days)")),
        "field_6781": data.get("Title policy payer"),
        "field_6782": _to_int(data.get("Default objection period (days)")),
        "field_6783": data.get("Preferred home warranty"),
        "field_6785": data.get("Agent License Number"),
        "field_6786": data.get("Supervisor License Number"),
        "field_6800": data.get("User ID"),
        "field_7611": data.get("Who obtains the Subdivision Information?"),
        "field_7612": data.get("Within how many days after the effective date must it be obtained?"),
        "field_7613": data.get("Does the Buyer require an updated resale certificate?"),
        "field_7614": data.get("What is the maximum amount Buyer will pay for Association fees, deposits, and reserves?"),
        "field_7615": data.get("If the Title Company needs Association information beyond what's required, who pays for it?"),
        "field_7616": data.get("Escrow Agent Name"),
        "field_7617": data.get("Escrow Agent Address"),
        "field_7620": data.get("signup_token"),
    }
    payload = {k: v for k, v in payload.items() if v not in (None, "")}

    response = requests.post(
        BASEROW_AGENT_TABLE_URL,
        headers={
            "Authorization": f"Token {BASEROW_TOKEN}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


@app.route('/signup')
def signup():
    session["signup_data"] = {}
    return redirect(url_for('signup_agent'))


@app.route('/signup/agent', methods=['GET', 'POST'])
def signup_agent():
    if request.method == 'POST':
        _store_form(request.form)
        return redirect(url_for('signup_supervisor'))
    return render_template('signup/agent.html', step=1, data=session.get("signup_data", {}))


@app.route('/signup/supervisor', methods=['GET', 'POST'])
def signup_supervisor():
    if request.method == 'POST':
        _store_form(request.form)
        return redirect(url_for('signup_transactions'))
    return render_template('signup/supervisor.html', step=2, data=session.get("signup_data", {}))


@app.route('/signup/transactions', methods=['GET', 'POST'])
def signup_transactions():
    if request.method == 'POST':
        _store_form(request.form)
        return redirect(url_for('signup_subdivision'))
    return render_template('signup/transactions.html', step=3, data=session.get("signup_data", {}))


@app.route('/signup/subdivision', methods=['GET', 'POST'])
def signup_subdivision():
    data = session.get("signup_data", {})
    branch = data.get("Who obtains the Subdivision Information?", "Seller obtains it")

    if request.method == 'POST':
        _store_form(request.form)
        data = session.get("signup_data", {})
        data["User ID"] = str(uuid.uuid4())
        data["signup_token"] = f"{secrets.randbelow(900000) + 100000}"
        session["signup_data"] = data

        try:
            create_agent_row(data)
        except requests.HTTPError as e:
            detail = e.response.text if e.response is not None else str(e)
            flash(f"Submission failed: {detail}")
            return redirect(url_for('signup_subdivision'))
        except requests.RequestException as e:
            flash(f"Could not reach the database: {e}")
            return redirect(url_for('signup_subdivision'))

        token = data["signup_token"]
        session.pop("signup_data", None)
        return redirect(f"https://t.me/reagent512_bot?start={token}")

    return render_template('signup/subdivision.html', step=4, branch=branch, data=data)


if __name__ == '__main__':
    app.run(debug=True)
