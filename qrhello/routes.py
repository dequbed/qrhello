from flask import make_response, request, redirect, url_for, render_template, flash
from qrhello import app, db

import qrhello.dbfoo

@app.route('/l/hallo')
def hallo():
    if not request.cookies.get("name"):
        return redirect(url_for("register") + "?return_to=/l/i/hallo")
    else:
        return render_template("hallo.html")

@app.route('/l/tschuess')
def tschuess():
    return render_template("tschuess.html")

@app.route('/l/i/<string:item_id>', methods=['GET', 'POST'])
def reserve_item(item_id):
    # In any case we need those cookies set
    if not request.cookies.get("name"):
        return redirect(url_for("register") + "?return_to=/l/i/" + item_id)

    db = qrhello.db
    # Again, GET means trying to get the form
    if request.method == 'GET':
        claimant = db.claimed(item_id)
        if claimant is not None:
            reserved = True
            (reserved_by, _) = claimant
        else:
            reserved = False
            reserved_by = None

        return render_template("reserveitem.html", item_id=item_id, reserved=reserved, reserved_by=reserved_by)
    else:
        name = request.cookies.get("name")
        email = request.cookies.get("email")
        db.claim(item_id, name, email)

        # Method is POST, so they're either trying to reserve the item or take over the item.
        return "Reserving/Taking over item %s as %s " % (item_id, name)

@app.route('/l/register', methods=['GET', 'POST'])
def register():
    # Check the req method first. POST means submitting form contents, GET means trying to get the form.
    if request.method == 'POST':
        try:
            # Valid form has both name and email.
            name = request.form['name']
            email = request.form['email']

            # Most URLs set the 'return_to'.
            redirect_to = request.args.get('return_to')
            if redirect_to:
                response = redirect(redirect_to)
            else:
                # if there isn't a 'return_to' set, default to just sending to the hello page
                response = redirect(url_for("hallo"))

            # We need to set these cookies so people don't have to do this again
            response.set_cookie("name", name)
            response.set_cookie("email", email)
            return response

        except KeyError as e:
            # Invalid form; was either missing name or email
            return "Missing %s" % e, 400
    else:
        # GET request => Send the register form
        return render_template("register.html")

@app.route('/l/ueber')
def about():
    return render_template('about.html')

def reserved_by_item(item_id):
    return qrhello.dbfoo.sql_is_reserved(item_id)
