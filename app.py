from flask import Flask, render_template, redirect, url_for, session, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mysqldb import MySQL
import random
from datetime import datetime


def random_transaction_id():
    """returns random integer of digit 10"""
    return f"ID{random.randint(10000000, 99999999)}"

def random_account():
    """returns random integer of digit 8"""
    return random.randint(1000000000, 9999999999)

# initialize our flask app
app = Flask(__name__)

# configuring your MySQL server
app.config["SECRET_KEY"] = "hey47fewod3i4rcmi3rurmxkp23od94jvxz../"
app.config["MYSQL_HOST"] = 'localhost'
app.config["MYSQL_USER"] = 'root'
app.config["MYSQL_PASSWORD"] = ''
app.config["MYSQL_DB"] = 'bank_management_system'

# creating the instance of MySQL class
mysql = MySQL(app)

# Routing to the home page 
@app.route('/')
@app.route('/main_dashboard')
def main_dashboard():
    return render_template('dashboard.html', head="Home")

# Register Here
@app.route('/register', methods=["POST", "GET"])
def register():
    # See if there is any Error
    try:
        error = ''

        # if customer submits his details take the details
        if request.method == "POST":
            fname = request.form["fname"]
            lname = request.form["lname"]
            date_of_birth = request.form["dob"]
            phone_number = request.form["phone_number"]
            email = request.form["email"]
            password = request.form["password"]
            confirm_password = request.form["confirmPassword"]

            # check wether the password is consistent
            if password != confirm_password:
                 error = "Sorry your passwords were miss matched! "
                 return render_template('register.html', head="Register", error=error)
            
            # connect to mysql server and check if the customer already exists
            
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT email FROM customer WHERE email=%s", (email, ))
            check_email = cursor.fetchone()
            # close the server
            cursor.close()
            # if user exists in the database redirect him to the login page
            if check_email:
                error = "You Have already An Account!"
                return redirect(url_for('login'))
        
            # generate randeom account NB. for Real Apps use the 'uuid' module to prevent repetition 
            rand_acc = random_account()
            hashed_password = generate_password_hash(password)
            # initialize the server and store the credentials of the customer
            cursor = mysql.connection.cursor()
            cursor.execute("INSERT INTO customer values(%s, %s, %s, %s, %s, %s)", (fname, lname, phone_number, email, hashed_password, date_of_birth))

            # create a unique account for the customer
            cursor.execute("INSERT INTO account VALUES(%s, %s, %s, %s)", (rand_acc, email, datetime.now(), 0.0))

            # retrive the customers account number from the account table
            cursor.execute("SELECT * from account WHERE email=%s", (email, ))
            fetch_account = cursor.fetchone()
            account = fetch_account[0]
            mysql.connection.commit()
            cursor.close()
            
            # redirect the customer to the login page
            flash(f"You have successfully registered! with new Account number : {account}")
            return redirect(url_for('login'))
    # catch any errors
    except Exception:
        flash("Something Went Wrong! We're Sorry for the inconvenience!")
    
    # if there is an error return to the registration page
    return render_template('register.html', head="Register", error=error)


# the login page
@app.route('/login', methods=["POST", "GET"])
def login():
    try:
        error =  ''
        # check if the customer submits his email and password
        if request.method == "POST":
            # collect the credentials of the customer
            email = request.form["email"]
            password = request.form["password"]
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM customer WHERE email=%s", (email,))
            # retrive the row as a tuple from the customer table
            email_as_id = cursor.fetchone()
            cursor.close()

            # check wether the password is correct and the user is known by the database
            if email_as_id and check_password_hash(pwhash=email_as_id[4], password=password):
                # store some of the data as temporary data until the user logs out
                session['user_id'] = email
                session['name'] = email_as_id[0]
                flash(f"You have successfully loged In! {email_as_id[0]}")
                # user authenticated and redirect to the page routed as 'my_account' 
                return redirect(url_for('my_account'))
            else:
                error = "Incorrect Password or You Don't have Registered yet!"
    except Exception:
        # catch any errors in the code
        flash("Something Went Wrong! We're Sorry for the inconvenience!")

    return render_template('login.html', head="Login", error=error)

# the my_account page
@app.route('/my_account')
def my_account():
    try:
        # check if there is user loged in else redirect to the login page
        if 'user_id' in session:
            cursor = mysql.connection.cursor()
            # grab the credentials of the user as a tuple
            cursor.execute("select fname, lname, account_id, balance, phone_number, date_created from bank_management_system.customer, " +
                        "bank_management_system.account where customer.email=%s and customer.email=account.email;", (session['user_id'],))
            profile = cursor.fetchone()
            cursor.close()
            full_name = f"{profile[0]} {profile[1]}"
            account_no = profile[2]
            balance = profile[3]
            phone_number = profile[4]
            date = profile[5]
            # display user profile in the page
            return render_template('my_account.html', head="My Account", full_name=full_name, account_no=account_no, balance=balance, phone_number=phone_number, date=date, email=session['user_id'])

        flash("You Need to login first please!")

    except Exception:
        # catch any errors happening
        flash("Something Went Wrong! We're Sorry for the inconvenience!")

    # delete temporary data
    # session.clear()
    return redirect(url_for('login'))


# route to the deposite page
@app.route('/my_account/deposit', methods=["POST", "GET"])
def deposit():
    try:
        # check if there is user loged in else redirect to the login page
        if 'user_id' in session:
            if request.method == "POST":

                # when the user submits the amount as string convert it to float so as to match to the data type in our database
                amount = float(request.form.get("amount"))
                
                # check if the amount to be deposited is greater than 0
                if amount > 0:                    
                    cursor = mysql.connection.cursor()
                    # take the account number and the balance of the user as a tuple
                    cursor.execute("SELECT account_id, balance FROM account WHERE email=%s", (session['user_id'],))
                    account_info = cursor.fetchone()
                    account_number = account_info[0]
                    # increement the balance by the credited amount and insert it to the database back
                    balance = account_info[1] + amount
                    cursor.execute("UPDATE account SET balance=%s WHERE account_id=%s", (balance, account_number))
                    # record the transaction to the transaction_history table in our database
                    cursor.execute("INSERT INTO transaction_history(transaction_id, account_id, transaction_type, transaction_amount, sender_account, transaction_date)"
                                   +" VALUES(%s, %s, %s, %s, %s, %s)", (random_transaction_id(), account_number, "Deposit", f"+{amount}", "self", datetime.now()))
                    # apply changes and close the database
                    mysql.connection.commit()
                    cursor.close()
                    # prompt to the user about his action
                    flash(f"You have Successfully deposited {amount} to your account number {account_number}")

                else:
                    flash('amount must be greater than 0 to deposit!')

            return render_template('deposit.html')

        flash("Log in to access the page")
    except Exception:
        # catch any errors happening
        flash("Something Went Wrong! We're Sorry for the inconvenience!")
    # delete temporaily stored data and redirec to the login page
    session.clear()
    return redirect(url_for('login'))

# transfer page
@app.route('/my_account/transfer', methods=["POST", "GET"])
def transfer():
    # try:
        # check if there is user loged in else redirect to the login page
        if 'user_id' in session:
            if request.method == "POST":
                # take reciever account number, amount and password NB: change the amount submited to float
                # because the transfer_amount atribute in our transaction_history relation recieves only double numbers
                reciever_account = int(request.form.get("recAccount"))
                amount = float(request.form.get("transferAmount"))
                password = request.form.get("password")
                # check if amount is greater than 0
                if amount > 0.0:
                    # connect to the database
                    cursor = mysql.connection.cursor()
                    # take account number and current balance of the user as sender_balance
                    cursor.execute("SELECT balance, account_id, password FROM customer, account WHERE customer.email=%s and customer.email=account.email", (session['user_id'],))
                    account_info = cursor.fetchone()
                    sender_balance = account_info[0]
                    sender_account_number = account_info[1]
                    hashed_pswd = account_info[2]
                    if amount > sender_balance:
                        flash("You Don't have enough money!")

                    # if amount to be transfered is less than the balance check wether the password is correct
                    else:
                        # in real world apps it is not safe to store passwords or other sensitive info in the browsers cache 
                        if check_password_hash(pwhash=hashed_pswd, password=password):
                            # take the reciever's account number, reciever's email and reciever's balance from the account table
                            cursor.execute("SELECT * FROM account WHERE account_id=%s", (reciever_account,))
                            reciever_account_data = cursor.fetchone()
                            
                            # if reciever is not found in the database it means it is not registered yet
                            if not reciever_account_data:
                                flash("You have entered wrong account or the reciever is not registered yet")

                            else:
                                # increement  reciever's balance and decreement sender's balance by the same amount                                 
                                reciever_account_number = reciever_account_data[0]
                                reciever_email = reciever_account_data[1]
                                reciever_balance = reciever_account_data[3]
                                sender_balance -= amount
                                reciever_balance += amount

                                # take the reciever's profile as tuple
                                cursor.execute("select fname, lname from account, customer where account.email=customer.email and customer.email=%s", (reciever_email,))
                                reciever_profile = cursor.fetchone()
                                reciever_name = f"{reciever_profile[0]} {reciever_profile[1]}"
                                print(reciever_balance)
                                print(sender_balance)
                                # replace the reciever's and sender's balance by the new one
                                cursor.execute("UPDATE account SET balance=%s WHERE account_id=%s", (reciever_balance, reciever_account_number))
                                cursor.execute("UPDATE account SET balance=%s WHERE account_id=%s", (sender_balance, sender_account_number))
                                # record transaction made
                                cursor.execute("INSERT INTO transaction_history(transaction_id, account_id, transaction_type, transaction_amount, reciever_account, transaction_date)"+
                                    " VALUES(%s, %s, %s, %s, %s, %s)", (random_transaction_id(), sender_account_number, "Sent", "-"+str(amount), reciever_account_number, datetime.now()))
                                cursor.execute("INSERT INTO transaction_history(transaction_id, account_id, transaction_type, transaction_amount, sender_account, transaction_date) "+
                                    "VALUES(%s, %s, %s, %s, %s, %s)", (random_transaction_id(), reciever_account_number, "Recieved", "+"+str(amount), str(sender_account_number), datetime.now()))
                                
                                # apply the changes and close the database
                                mysql.connection.commit()
                                cursor.close()
                                # prompt the user about his action
                                flash(f"You have successfully sent {amount} Birr to {reciever_name}")

                        else:
                            flash("Inccorect password")

                else:
                    flash(f"Please Insert valid amount! {amount}")  

            return render_template('transfer.html')
        
        flash("Log in to access the page")
    
    # except Exception:
    #    flash("Something Went Wrong! We're Sorry for the inconvenience!")
    
    # clear the data stored as cache in the browser and redirect the user to login page
    # session.clear()
        return redirect(url_for('login'))

# Withdraw
@app.route('/my_account/withdraw', methods=["POST", "GET"])
def withdraw():
    try:
        # check if there is user loged in else redirect to the login page
        if 'user_id' in session:
            if request.method == "POST":
                # change the withdrawal amount to float
                amount = float(request.form["withdrawalAmount"])
                password = request.form["password"]
                # connect to the database and take the credentials of the current user
                cursor = mysql.connection.cursor()
                
                cursor.execute("select password, balance, account_id from account, customer where customer.email=%s and customer.email=account.email", (session['user_id'], ))
                fetch_data = cursor.fetchone()
                balance = fetch_data[1]
                account_number = fetch_data[2]

                # check if the password was correct
                if check_password_hash(password=password, pwhash=fetch_data[0]):
                    # decreement the balance by the withdrawal amount and store it
                    balance -= amount

                    cursor.execute("UPDATE account SET balance=%s WHERE account_id=%s", (balance, account_number))
                    # record transactions made
                    cursor.execute("INSERT INTO transaction_history(transaction_id, account_id, transaction_type, transaction_amount, transaction_date) VALUES(%s, %s, %s, %s, %s)", (random_transaction_id(), account_number, "Withdrawal", "-"+str(amount), datetime.now()))
                    mysql.connection.commit()
                    cursor.close()
                    flash(f"You have Successfully Withdraw {amount} Birr  from  {account_number}")

                else:
                    flash("Please Insert correct password!")
            return render_template("withdraw.html", head="Withdraw")
        flash("Log in to access the page")

    except Exception:
        flash("Something Went Wrong! We're Sorry for the inconvenience!")
    # if user is not signed in clear cache and redirect to the login page
    session.clear()
    return redirect(url_for('login'))
    

# transaction history
@app.route('/my_account/history', methods=["POST", "GET"])
def transaction_history():
    try:
        # check if there is user loged in else redirect to the login page
        if 'user_id' in session:
            # connect the database
            cursor = mysql.connection.cursor()
            # retrive account number of the current user
            cursor.execute("SELECT account_id FROM account WHERE email=%s", (session['user_id'], ))
            account_number = cursor.fetchone()
            account_number = account_number[0]
            # retrive all transactions made to the current user's account with detals as atuple
            cursor.execute("SELECT * FROM transaction_history WHERE account_id=%s ORDER BY transaction_date DESC", (account_number, ))
            all_history = cursor.fetchall()
            mysql.connection.commit()
            cursor.close()
            # send the tuple to history.html page to be displayed to the user
            return render_template('history.html', all_history=all_history, head="History")
        flash("Log in to access the page")

    except Exception:
        flash("Something Went Wrong! We're Sorry for the inconvenience!")

    # if user not logedin clear the data in browser's cache and redirect to the login page
    session.clear()
    return redirect(url_for('login'))

# logout 
@app.route('/logout', methods=["POST", "GET"])
def logout():
    if request.method == "POST":
        # if user wants to logout clear the cached data and redirect to the login page
        session.clear()
        # response.headers.add('Cache-Control', 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0')
        return redirect(url_for('login'))
    return render_template('logout.html', head="Logout")




if __name__ == "__main__":
    app.run(debug=True)


