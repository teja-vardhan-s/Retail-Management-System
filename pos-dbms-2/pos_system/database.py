from sqlalchemy import create_engine, text
from pos_system import login_manager, bcrypt, session
from sqlalchemy.exc import SQLAlchemyError
from flask import flash

username = 'mysqluser'
password = 'password'
host = 'localhost'
port = '3306'
database_name = 'Pos_DB'

db_url = f"mysql+mysqlconnector://{username}:{password}@{host}:{port}/{database_name}"

engine = create_engine(db_url)

def test_conn():
    """test connectivity to the database

    Returns:
        A string: indicating the connection status
    """
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 'test connection successful' "))
    return result.fetchone()[0]

class Employee():
    def __init__(self, emp_id, empname, password_hash, dob, doj, gender, email, mobile, salary):
        self.emp_id = emp_id
        self.emp_name = empname
        self.password_hash = password_hash
        self.dob = dob
        self.doj = doj
        self.gender = gender
        self.email = email
        self.mobile = mobile
        self.salary = salary
        
    def is_active(self):
        """True, as all emps are active."""
        return True

    def get_id(self):
        """Return the id to satisfy Flask-Login's requirements."""
        return str(self.emp_id)

    def is_authenticated(self):
        """Return True if the emp is authenticated."""
        return True

    def is_anonymous(self):
        """False, as anonymous emps aren't supported."""
        return False
    
        
    def reload_emp_from_db(self):
        emp = Employee.loading_emp(self.id)
        if emp:
            self.emp_id = emp.emp_id
            self.emp_name = emp.emp_name
            self.password_hash = emp.password_hash
            self.dob = emp.dob
            self.doj = emp.doj
            self.gender = emp.gender #char
            self.email = emp.email
            self.mobile = emp.mobile
            self.salary = emp.salary

    def update_employee(employee, emp_id):
        """updates employee details in the database

        Args:
            employee (Employee obj): object of Employee class
            emp_id (int): employee id

        Returns:
            bool: true if updation is successful, false otherwise
        """
        try:
            with engine.begin() as conn:  # Start a transaction
                conn.execute(text(f"UPDATE Employees SET emp_name = :emp_name, password_hash = :password_hash, salary = :salary WHERE emp_id = :emp_id"),
                            {"emp_name": employee.emp_name, "password_hash": employee.password_hash, "salary": employee.salary, "emp_id" : emp_id})
                conn.execute(text(f"UPDATE Employee_Details SET dob= :dob, doj= :doj, gender_id= :gender, email = :email, mobile = :phone WHERE emp_id = :emp_id"),
                            {"dob" : employee.dob, "doj": employee.doj, "gender": 1 if employee.gender == "M" else 2 ,"email": employee.email, "phone": employee.mobile, "emp_id" : emp_id})
            return True
        except SQLAlchemyError as e:
            print("Database error:", e)
            return False


    def get_all():
        """fetches all employees from the database"""
        try:
            with engine.begin() as conn:
                query = """
                        SELECT Employees.emp_id, Employees.emp_name, Employees.password_hash, 
                                                Employee_Details.dob, Employee_Details.doj, 
                                                Gender.gender_name, Employee_Details.email, Employee_Details.mobile, Employees.salary
                                                FROM Employees
                                                JOIN Employee_Details ON Employees.emp_id = Employee_Details.emp_id
                                                JOIN Gender ON Employee_Details.gender_id = Gender.gender_id
                        """
                result = conn.execute(text(query))
                emp_data = result.fetchall()
                emps = []
                for emp in emp_data:
                    emps.append(Employee(emp_id=emp[0], empname=emp[1], password_hash=emp[2], dob=emp[3], 
                                         doj=emp[4], gender=emp[5], email=emp[6], mobile=emp[7], salary=emp[8]))
                return emps
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return []



    def create_emp(username, password, dob, doj, gender, email, mobile, salary):
        """creates an employee in the database

        Args:
            username (string): name of the employee
            password (string): password
            dob (datetime.date): date of birth
            doj (datetime.date): date of join
            gender (char): M for Male, F for Female
            email (string): email address
            mobile (int): 10 digit mobile number
            salary (float): salary of the employee

        Returns:
            Employee object: an instance of created employee is returned
        """
        if gender == 'M':
            gender_id = 1
        elif gender == "F":
            gender_id = 2
        try:
            password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
            with engine.begin() as conn:
                conn.execute(text(f"INSERT INTO Employees (emp_name, password_hash,salary) VALUES (:username, :password_hash, :salary)"),
                                    {"username": username, "password_hash": password_hash, "salary": salary})
                emp_id_result = conn.execute(text("SELECT LAST_INSERT_ID()"))  # Fetch the last inserted ID
                emp_id = emp_id_result.fetchone()[0]  # Retrieve the ID
                conn.execute(text(f"INSERT INTO Employee_Details (emp_id, dob, doj, gender_id, email, mobile) VALUES (:emp_id, :dob, :doj, :gender, :email, :mobile)"),
                                    {"emp_id": emp_id, "dob": dob, "doj": doj, "gender": gender_id, "email": email, "mobile": mobile})
                conn.commit()
                return Employee(emp_id=emp_id, empname=username, email=email, password_hash=password_hash,
                                dob=dob, doj=doj, gender=gender, mobile=mobile, salary=salary)
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return None

    
    def check_emp(emp_id, password):
        """checks if the employee exists in the database"""
        try:
            with engine.begin() as conn:
                query = """SELECT Employees.emp_id, Employees.emp_name, Employees.password_hash, 
                                                Employee_Details.dob, Employee_Details.doj, 
                                                Gender.gender_name, Employee_Details.email, Employee_Details.mobile, Employees.salary
                                                FROM Employees
                                                JOIN Employee_Details ON Employees.emp_id = Employee_Details.emp_id
                                                JOIN Gender ON Employee_Details.gender_id = Gender.gender_id
                                            WHERE Employees.emp_id = :emp_id"""
                result = conn.execute(text(query), {"emp_id": emp_id})
                emp_data = result.fetchone()
                if emp_data is not None:
                    if bcrypt.check_password_hash(emp_data[2], password):
                        return Employee(emp_data[0], emp_data[1], emp_data[2], emp_data[3], 
                                       emp_data[4], emp_data[5], emp_data[6], emp_data[7], emp_data[8])
                    else:
                        return False
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return None
    
    def get_emp_w_id(emp_id):
        """fetches an employee from the database using emp_id"""
        try:
            with engine.begin() as conn:
                query = """SELECT Employees.emp_id, Employees.emp_name, Employees.password_hash, 
                                                Employee_Details.dob, Employee_Details.doj, 
                                                Gender.gender_name, Employee_Details.email, Employee_Details.mobile, Employees.salary
                                                FROM Employees
                                                JOIN Employee_Details ON Employees.emp_id = Employee_Details.emp_id
                                                JOIN Gender ON Employee_Details.gender_id = Gender.gender_id
                                            WHERE Employees.emp_id = :emp_id"""
                result = conn.execute(text(query), {"emp_id": emp_id})
                emp_data = result.fetchone()
                if emp_data:
                    return Employee(emp_data[0], emp_data[1], emp_data[2], emp_data[3], 
                                    emp_data[4], emp_data[5], emp_data[6], emp_data[7], emp_data[8])
                else:
                    return None
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return None
            
    def delete_emp_w_id(emp_id):
        """delete an employee from the database using emp_id

        Args:
            emp_id (int): employee id

        Returns:
            bool: True upon successful deletion, False otherwise
        """
        try:
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM Employees WHERE emp_id = :emp_id"), {"emp_id": emp_id})
                conn.commit()
                return True
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return False
        
    def check_email(email):
        """checks if the email exists in the database"""
        try:
            with engine.begin() as conn:
                query = """SELECT Employees.emp_id, Employees.emp_name, Employees.password_hash, 
                                                Employee_Details.dob, Employee_Details.doj, 
                                                Gender.gender_name, Employee_Details.email, Employee_Details.mobile, Employees.salary
                                                FROM Employees
                                                JOIN Employee_Details ON Employees.emp_id = Employee_Details.emp_id
                                                JOIN Gender ON Employee_Details.gender_id = Gender.gender_id
                                            WHERE Employee_Details.email = :email"""
                result = conn.execute(text(query), {"email": email})
                return result.rowcount > 0
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return False

        
    def loading_emp(emp_id):
        """loads employee from the database usinf emp_id

        Args:
            emp_id (int): employee id

        Returns:
            Employee object: instance of the loaded employee
        """        """"""
        try:
            with engine.begin() as conn:
                query = """SELECT Employees.emp_id, Employees.emp_name, Employees.password_hash, 
                                                Employee_Details.dob, Employee_Details.doj, 
                                                Gender.gender_name, Employee_Details.email, Employee_Details.mobile, Employees.salary
                                                FROM Employees
                                                JOIN Employee_Details ON Employees.emp_id = Employee_Details.emp_id
                                                JOIN Gender ON Employee_Details.gender_id = Gender.gender_id
                                            WHERE Employees.emp_id = :emp_id"""
                result = conn.execute(text(query), {"emp_id": emp_id})
                emp_data = result.fetchone()
                if emp_data:
                    # Create an employee instance using the fetched data
                    emp = Employee(emp_id=emp_data[0], empname=emp_data[1], password_hash=emp_data[2], dob=emp_data[3], 
                                   doj=emp_data[4], gender=emp_data[5], email=emp_data[6], mobile=emp_data[7], salary=emp_data[8])
                    return emp
                else:
                    return None
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return None
        
    def get_latest_emp_id():
        """gets the latest employee id from database

        Returns:
            int: the latest emp_id
        """
        try:
            with engine.begin() as conn:
                result = conn.execute(text("SELECT emp_id FROM Employees ORDER BY emp_id DESC LIMIT 1"))
                return result.fetchone()[0]
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return None
            
@login_manager.user_loader
def load_user(user_id):
    return Employee.loading_emp(user_id)

class Activities():
    def __init__(self, activity_id, emp_id, date, time, activity_type):
        self.activity_id = activity_id
        self.emp_id = emp_id
        self.activity_date = date
        self.activity_time = time
        self.activity_type = activity_type 

    def add_activity(emp_id, activity_type):
        """adds an activity in the database

        Args:
            emp_id (int): employee id of the employee who made the activity
            activity_type (int): referencing activity_type table in the database

        Returns:
            bool: True upon succesful insertion, otherwise False
        """
        try:
            with engine.begin() as conn:
                activity_type_id = conn.execute(text(f"SELECT activity_type_id FROM Activity_Type WHERE activity_type_name = '{activity_type}'"))
                activity_type_id = activity_type_id.fetchone()[0]

                conn.execute(text(f"INSERT INTO Activities (emp_id, activity_type_id, activity_date, activity_time) VALUES (:emp_id, :activity_type_id, CURRENT_DATE(), CURRENT_TIME())"),
                             {"emp_id": emp_id, "activity_type_id": activity_type_id})
                conn.commit()
                return True
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return False
        
    def get_activities():
        """fetches all records from Activities table in Database

        Returns:
            list: contains instances of Activities class
        """        
        try:
            with engine.begin() as conn:
                query = """SELECT Activities.activity_id, Activities.emp_id, Activities.activity_date AS date, 
                                            Activities.activity_time AS time, Activity_Type.activity_type_name
                                            FROM Activities
                                            INNER JOIN Activity_Type ON Activities.activity_type_id = Activity_Type.activity_type_id
                                            ORDER BY Activities.activity_id"""
                result = conn.execute(text(query))
                activities_data = result.fetchall()
                activities = []
                for activity in activities_data:
                    activity_obj = Activities(activity_id=activity[0], emp_id=activity[1], date=activity[2], time=activity[3], activity_type=activity[4])
                    activities.append(activity_obj)
                return activities
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return []
        

class Customers():
    def __init__(self, cust_id, cust_name, cust_email, cust_mobile):
        self.cust_id = cust_id
        self.cust_name = cust_name
        self.phone = cust_mobile
        self.email = cust_email if cust_email else None
        
    def get_all():
        """gets all records from Cutomers Table in database

        Returns:
            list: contains instances of Customers class
        """        
        try:
            with engine.begin() as conn:
                query = """SELECT Customers.customer_id, Customers.customer_name, 
                                            Contact_Details.email, Contact_Details.mobile
                                            FROM Customers
                                            LEFT JOIN Contact_Details ON Customers.customer_id = Contact_Details.customer_id
                                            ORDER BY Customers.customer_id"""
                result = conn.execute(text(query))
                cust_data = result.fetchall()
                customers = []
                for cust in cust_data:
                    customers.append(Customers(cust_id=cust[0], cust_name=cust[1], cust_email=cust[2], cust_mobile=cust[3]))
                return customers
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return []
        
    def delete_customer_w_id(cust_id):
        """deletes a record from Customers table in the database using customer_id

        Args:
            cust_id (int): id of the customer to be deleted

        Returns:
            bool: True upon succesful deletion, otherwise False
        """        
        try:
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM Customers WHERE customer_id = :cust_id"), {"cust_id": cust_id})
                conn.commit()
                return True
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return False
        
    def update_customer(customer, cust_id):
        """updates customer record in the database using cust_id

        Args:
            customer (Customers): an instance of Customers class 
            cust_id (int): the id of customer to be updated

        Returns:
            bool: True upon succesful updation, otherwise False
        """        
        try:
            with engine.begin() as conn:
                query1 = """UPDATE Customers
                                    SET customer_name = :cust_name
                                    WHERE customer_id = :cust_id"""
                query2 = """UPDATE Contact_Details
                                    SET email = :email, mobile = :phone
                                    WHERE customer_id = :cust_id"""
                conn.execute(text(query1), {"cust_name": customer.cust_name, "cust_id": cust_id})
                conn.execute(text(query2), {"email": customer.email, "phone": customer.phone, "cust_id": cust_id})
                conn.commit()
                return True
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return False
        
    def get_customer_w_id(cust_id):
        """fetches a customer with id from the database

        Args:
            cust_id (int): id of the customer who needs to be fetched

        Returns:
            Customers obj: customer as an object of Customers class
        """        
        try:
            with engine.begin() as conn:
                query = """SELECT Customers.customer_id, Customers.customer_name, 
                                            Contact_Details.email, Contact_Details.mobile
                                            FROM Customers
                                            LEFT JOIN Contact_Details ON Customers.customer_id = Contact_Details.customer_id
                                            WHERE Customers.customer_id = :cust_id"""
                result = conn.execute(text(query), {"cust_id": cust_id})
                cust_data = result.fetchone()
                if cust_data:
                    return Customers(cust_id=cust_data[0], cust_name=cust_data[1], cust_email=cust_data[2], cust_mobile=cust_data[3])
                else:
                    return None
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return None
            
    def add_customer(self):
        """adds itself (a customer) to the Customers table in database

        Returns:
            bool: True upon succesful insertion, otherwise False
        """         
        try:
            with engine.begin() as conn:                
                conn.execute(text(f"INSERT INTO Customers (customer_id, customer_name) VALUES (:cust_id, :cust_name)"), 
                                    {"cust_id": self.cust_id, "cust_name": self.cust_name})
                conn.execute(text(f"INSERT INTO Contact_Details (customer_id, email, mobile) VALUES (:cust_id, :email, :phone)"), 
                                    {"cust_id": self.cust_id, "email": self.email, "phone": self.phone})
                conn.commit()
                return True
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return False
        
    def get_latest_customer_id():
        """gets the latest customer id in the database

        Returns:
            int: latest customer_id
        """        
        try:
            with engine.begin() as conn:
                result = conn.execute(text("SELECT customer_id FROM Customers ORDER BY customer_id DESC LIMIT 1"))
                latest_cust_id = result.fetchone()
                if latest_cust_id is not None:
                    return latest_cust_id[0]
                else:
                    return 0
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return None
            
    def reload_customer_from_db(self):
        customer = Customers.get_customer_w_id(self.cust_id)
        if customer:
            self.cust_name = customer.cust_name
            self.email = customer.email
            self.phone = customer.phone
            
    def refresh_customers_in_db():
        customers = Customers.get_all()
        for customer in customers:
            customer.reload_customer_from_db()

    @staticmethod
    def add_to_session():
        """adds all the customers in the database to the session
        """        
        customers = Customers.get_all()
        cust_dict= {}
        for customer in customers:
            cust_dict[customer.cust_id] = customer.cust_name
        session['customers'] = cust_dict

class Transactions():
    def __init__(self, tran_id, date_time, total_amount, payment_method, cust_id, emp_id):
        self.tran_id = tran_id
        self.date_time = date_time
        self.total_amount = total_amount
        self.payment_method = payment_method
        self.cust_id = cust_id
        self.emp_id = emp_id

    def add_transaction(self):
        """adds/inserts a transaction into the database

        Returns:
            bool: True upon succesful insertion, otherwise False
        """
        try:
            with engine.begin() as conn:
                conn.execute(text("INSERT INTO Transactions (tran_id, date_time, total_amount, payment_method, cust_id, emp_id) VALUES (:tran_id, CURRENT_TIMESTAMP(), :total_amount, :payment_method, :cust_id, :emp_id)"),
                             {"tran_id": self.tran_id, "total_amount": self.total_amount, "payment_method": self.payment_method, "cust_id": self.cust_id, "emp_id": self.emp_id})
                conn.commit()
                return True
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return False
        
    @staticmethod
    def get_transactions(cust_id):
        """fetches all transactions made by the customer with cust_id from the database

        Args:
            cust_id (int): id of customer whose transactions need to be fetched

        Returns:
            list: contains instances of Transactions class 
        """
        try:
            with engine.begin() as conn:
                result = conn.execute(text("SELECT * FROM Transactions WHERE cust_id = :cust_id"), {'cust_id': cust_id})
                trans_data = result.fetchall()
                transactions = []
                for trans in trans_data:
                    transactions.append(Transactions(tran_id=trans[0], date_time=trans[1], total_amount=trans[2], payment_method=trans[3], cust_id=trans[4], emp_id=trans[5]))
                return transactions
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return []
        
    def get_all():
        """fetches all transactions from the database 

        Returns:
            list: contains instances of Transactions class
        """
        try:
            with engine.begin() as conn:
                result = conn.execute(text("SELECT * FROM Transactions"))
                trans_data = result.fetchall()
                transactions = []
                for trans in trans_data:
                    transactions.append(Transactions(tran_id=trans[0], date_time=trans[1], total_amount=trans[2], payment_method=trans[3], cust_id=trans[4], emp_id=trans[5]))
                return transactions
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return []

        
    @classmethod
    def get_latest_transaction_id(cls):
        """fetches the latest transaction id

        Returns:
            int: lastest tran_id
        """     
        try:
            with engine.begin() as conn:
                result = conn.execute(text("SELECT tran_id FROM Transactions ORDER BY tran_id DESC LIMIT 1"))
                latest_tran_id = result.fetchone()
                if latest_tran_id is not None:
                    return latest_tran_id[0]
                else:
                    return 0
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return None
            
    def get_total_sales_revenue(filter):
        """fetches total sales revenue from the database

        Args:
            filter (string): monthly, weekly, daily, yearly

        Returns:
            dictionary: contains a filter mapped to its total revenue
        """
        try:
            with engine.begin() as conn:
                if filter == 'monthly':
                    query = text("SELECT MONTH(date_time) AS transaction_month, SUM(total_amount) AS total_amount FROM Transactions GROUP BY transaction_month")
                elif filter == 'weekly':
                    query = text("SELECT WEEK(date_time) AS transaction_week, SUM(total_amount) AS total_amount FROM Transactions GROUP BY transaction_week")
                elif filter == 'daily':
                    query = text("SELECT DATE(date_time) AS transaction_date, SUM(total_amount) AS total_amount FROM Transactions GROUP BY transaction_date")
                elif filter == 'yearly':
                    query = text("SELECT YEAR(date_time) AS transaction_year, SUM(total_amount) AS total_amount FROM Transactions GROUP BY transaction_year")
                result = conn.execute(query)
                result_dict = {}
                for row in result:
                    data = row[0]
                    total_amount = row[1]
                    result_dict[data] = total_amount
                return result_dict
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return None


        
    def get_transaction_analysis(filter):
        
        """fetches transaction analysis from the database

        Returns:
            list: contains instances of Transactions class
        """        
        try:
            with engine.begin() as conn:
                if filter == 'payment_methods':
                    query = text("SELECT payment_method, SUM(total_amount) AS total_revenue FROM Transactions GROUP BY payment_method")
                elif filter == 'recent_transaction_details':
                    query = text("""SELECT T.tran_id, T.date_time, T.total_amount, T.payment_method, C.customer_name 
                                    FROM Transactions AS T
                                    INNER JOIN Customers AS C 
                                    WHERE T.cust_id = C.customer_id
                                    ORDER BY T.date_time DESC 
                                    LIMIT 10;
                                    """)
                result = conn.execute(query)
                return result.fetchall()
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return []
    
    def get_transaction_analysis_by_date(date):
        """fetches transaction analysis by date from the database

        Args:
            date (datetime.date): date of the transaction

        Returns:
            list: contains instances of Transactions class
        """        
        try:
            with engine.begin() as conn:
                result = conn.execute(text("SELECT * FROM Transactions WHERE DATE(date_time) = :date"), {"date": date})
                return result.fetchall()
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return []

    
    def get_transaction_analysis_by_week(week):
        """fetches transaction analysis by week from the database

        Args:
            week (int): week of the transaction

        Returns:
            list: contains instances of Transactions class
        """        
        try:
            with engine.begin() as conn:
                result = conn.execute(text("SELECT * FROM Transactions WHERE WEEK(date_time) = :week"), {"week": week})
                return result.fetchall()
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return []
        
    def get_transaction_analysis_by_month(month):
        """fetches transaction analysis by month from the database

        Args:
            month (datetime.month): month of the transaction

        Returns:
            list: conatians instances of Transactions class
        """
        try:
            with engine.begin() as conn:
                result = conn.execute(text("SELECT * FROM Transactions WHERE MONTH(date_time) = :month"), {"month": month})
                return result.fetchall()
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return []
        
    def get_transaction_analysis_by_year(year):
        """fetches transaction analysis by year from the database

        Args:
            year (datetime.year): year of the transaction

        Returns:
            lsit: contains instances of Transactions class
        """        

        try:
            with engine.begin() as conn:
                result = conn.execute(text("SELECT * FROM Transactions WHERE YEAR(date_time) = :year"), {"year": year})
                return result.fetchall()
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return []

       
class Transaction_Item():
    def __init__(self, tran_item_id, tran_id, product_id, quantity, subtotal):
        self.tran_item_id = tran_item_id
        self.tran_id = tran_id
        self.product_id = product_id
        self.quantity = quantity
        self.subtotal = subtotal

    @classmethod
    def get_latest_transaction_item_id(cls):
        """fetches the latest transaction item id from the database

        Returns:
            int: latest tran_item_id
        """        
        try:
            with engine.begin() as conn:
                result = conn.execute(text("SELECT tran_item_id FROM Transaction_Item ORDER BY tran_item_id DESC LIMIT 1"))
                latest_tran_item_id = result.fetchone()
                if latest_tran_item_id is not None:
                    return latest_tran_item_id[0]
                else:
                    return 0
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return None
    
    def add_transaction_item(self):
        """inserts the transaction item into the database

        Returns:
            bool: True upon succesful insertion, otherwise False
        """        
        try:
            with engine.begin() as conn:
                conn.execute(text("INSERT INTO Transaction_Item (tran_item_id, tran_id, product_id, quantity, subtotal) VALUES (:tran_item_id, :tran_id, :product_id, :quantity, :subtotal)"), 
                             {"tran_item_id": self.tran_item_id, "tran_id": self.tran_id, "product_id": self.product_id, "quantity": self.quantity, "subtotal": self.subtotal})
                conn.commit()
                return True
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return False
        
    def get_transaction_items(tran_id):
        """fetches all the transaction items from the database

        Args:
            tran_id (int): id of the transaction

        Returns:
            list: contains instances of Transaction_Item class
        """
        try:
            with engine.begin() as conn:
                result = conn.execute(text("SELECT * FROM Transaction_Item WHERE tran_id = :tran_id"), {"tran_id": tran_id})
                return result.fetchall()
        except SQLAlchemyError as e:
            # Flash a user-friendly error message
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return None
            
    def add_tr_item(tran_id, product_id, quantity, subtotal):
        """inserts a transaction item into the database

        Args:
            tran_id (int): id of the transaction
            product_id (int): id of the product
            quantity (int): quantity of the product
            subtotal (float): sub total of the product

        Returns:
            _type_: _description_
        """        
        try:
            with engine.begin() as conn:
                conn.execute(text("INSERT INTO Transaction_Item (tran_id, product_id, quantity, subtotal) VALUES (:tran_id, :product_id, :quantity, :subtotal)"), 
                             {"tran_id": tran_id, "product_id": product_id, "quantity": quantity, "subtotal": subtotal})
                conn.commit()
                return True
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return False
        
class Products():
    def __init__(self, product_id, product_name, description , price, category):
        self.product_id = product_id
        self.product_name = product_name
        self.description = description
        self.category = category
        self.price = price

    def adds_product(product):
        try:
            with engine.begin() as conn:
                category_id = conn.execute(text(f"SELECT category_id FROM Category WHERE category_name = '{product.category}'"))
                category_id = category_id.fetchone()[0]
                if category_id == 0:
                    conn.execute(text(f"INSERT INTO Category (category_name) VALUES ({product.category})"))
                    category_id = conn.execute(text(f"SELECT category_id FROM Category WHERE category_name = '{product.category}'"))
                
                conn.execute(text(f"INSERT INTO Products (product_id, product_name, description, category_id, price) VALUES (:product_id, :product_name, :description, :category_id, :price)"),
                                 {"product_id": product.product_id, "product_name": product.product_name, "description": product.description, "category_id": category_id, "price": product.price})
                conn.commit()
                return True
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return False
        
    def get_all():
        try:
            with engine.begin() as conn:
                query = """SELECT Products.product_id, Products.product_name, 
                                            Products.description, Products.price, Category.category_name
                                            FROM Products
                                            JOIN Category ON Products.category_id = Category.category_id"""
                result = conn.execute(text(query))
                prod_data = result.fetchall()
                products = []
                for prod in prod_data:
                    products.append(Products(product_id=prod[0], product_name=prod[1], description=prod[2], price=prod[3], category=prod[4]))
                return products
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return []
        
    def get_latest_product_id():
        try:
            with engine.begin() as conn:
                result = conn.execute(text("SELECT product_id FROM Products ORDER BY product_id DESC LIMIT 1"))
                latest_product_id = result.fetchone()
                if latest_product_id is not None:
                    return latest_product_id[0]
                else:
                    return 0
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return None
        
    def delete_product_w_id(product_id):
        try:
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM Products WHERE product_id = :product_id"), {"product_id": product_id})
                conn.commit()
                return True
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return False
        
    def update_product(product, product_id):
        try:
            with engine.begin() as conn:
                # getting category_id from db
                category_id = conn.execute(text(f"SELECT category_id FROM Category WHERE category_name = '{product.category}'"))
                category_id = category_id.fetchone()[0]
                if category_id == 0:
                    conn.execute(text(f"INSERT INTO Category (category_name) VALUES ({product.category})"))
                    category_id = conn.execute(text(f"SELECT category_id FROM Category WHERE category_name = {product.category}"))

                query = """UPDATE Products
                                    SET product_name = :product_name,
                                        description = :description,
                                        category_id = :category_id,
                                        price = :price
                                    WHERE product_id = :product_id"""
                conn.execute(text(query),
                            {"product_name": product.product_name, "description": product.description, "category_id": category_id, "price": product.price, "product_id": product_id})
                conn.commit()
                return True
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return False
        
    def get_product_w_id(product_id):
        try:
            with engine.begin() as conn:
                query = """SELECT Products.product_id, Products.product_name, 
                                            Products.description, Products.price, Category.category_name
                                            FROM Products
                                            JOIN Category ON Products.category_id = Category.category_id 
                                            WHERE product_id = :product_id"""
                result = conn.execute(text(query), {"product_id": product_id})
                prod_data = result.fetchone()
                if prod_data:
                    return Products(product_id=prod_data[0], product_name=prod_data[1], description=prod_data[2], price=prod_data[3], category=prod_data[4])
                else:
                    return None
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return None
            
    def get_unique_categories():
        try:
            with engine.begin() as conn:
                result = conn.execute(text("SELECT DISTINCT category_name FROM Category"))
                categories = result.fetchall()
                return [category[0] for category in categories]
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return []
        
    def get_category_products(category):
        try:
            with engine.begin() as conn:
                query = """SELECT Products.product_id, Products.product_name, 
                                            Products.description, Products.price, Category.category_name
                                            FROM Products
                                            JOIN Category ON Products.category_id = Category.category_id 
                                            WHERE category_name = :category"""
                result = conn.execute(text(query), {"category": category})
                prod_data = result.fetchall()
                products = []
                for prod in prod_data:
                    products.append(Products(product_id=prod[0], product_name=prod[1], description=prod[2], price=prod[3], category=prod[4]))
                return products
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return []

    def get_quantity(self):
        try:
            with engine.begin() as conn:
                result = conn.execute(text("SELECT quantity_in_stock FROM Inventory WHERE product_id = :product_id"), {"product_id": self.product_id})
                quantity = result.fetchone()
                return quantity[0] if quantity else 0
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return 0
        
    def get_price(self):
        try:
            with engine.begin() as conn:
                result = conn.execute(text("SELECT price FROM Products WHERE product_id = :product_id"), {"product_id": self.product_id})
                price = result.fetchone()
                return price[0] if price else 0
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return 0
    
    def get_prices_from_cart(cart):
        prices = []
        try:
            with engine.begin() as conn:
                for item in cart.items:
                    result = conn.execute(text("SELECT price FROM Products WHERE product_id = :product_id"), {"product_id": item.product_id})
                    price = result.fetchone()
                    if price:
                        prices.append(price[0])
                    else:
                        flash(f"Product with ID {item.product_id} not found in database", "error")
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
        return prices
    
    @classmethod
    def get_price_w_id(product_id):
        try:
            with engine.begin() as conn:
                result = conn.execute(text("SELECT price FROM Products WHERE product_id = :product_id"), {"product_id": product_id})
                price = result.fetchone()
                return price[0] if price else 0
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return 0
    
    def get_product_analysis(product_filter):
        try:
            with engine.begin() as conn:
                if product_filter == 'top_products':
                    query = """SELECT p.product_id, p.product_name, SUM(ti.quantity) AS total_quantity 
                                FROM Products p JOIN Transaction_Item ti ON p.product_id = ti.product_id 
                                GROUP BY p.product_id 
                                ORDER BY total_quantity DESC 
                                LIMIT 5"""
                elif product_filter == 'product_categories':
                    query = """SELECT c.category_name, SUM(ti.quantity) AS total_quantity
                                    FROM Products p
                                    JOIN Transaction_Item ti ON p.product_id = ti.product_id
                                    JOIN Category c ON p.category_id = c.category_id
                                    GROUP BY c.category_name
                                    ORDER BY total_quantity DESC
                                    LIMIT 5"""
                result = conn.execute(text(query))
                return result.fetchall()
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return []

class Inventory():
    def __init__(self, product_id, supplier_id, quantity_in_stock, reorder_level):
        self.product_id = product_id
        self.supplier_id = supplier_id
        self.quantity_in_stock = quantity_in_stock
        self.reorder_level = reorder_level

    def get_from_inventory(product_id):
        try:
            with engine.begin() as conn:
                result = conn.execute(text(f"SELECT * FROM Inventory WHERE product_id = :product_id"), {"product_id": product_id})
                inventory_data = result.fetchone()
                if inventory_data:
                    inventory = Inventory(product_id=inventory_data[0], supplier_id=inventory_data[1], quantity_in_stock=inventory_data[2], reorder_level=inventory_data[3])
                    return inventory
                else:
                    inventory = Inventory(None, None, 0, 0)
                    return inventory
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return None
                
    def get_products():
        try:
            with engine.begin() as conn:
                results = conn.execute(text("SELECT p.product_id, p.product_name, p.description, p.price, i.supplier_id, i.quantity_in_stock, i.reorder_level, s.supplier_name FROM Products p JOIN Inventory i ON p.product_id = i.product_id JOIN Suppliers s ON i.supplier_id = s.supplier_id ORDER BY p.product_id"))
                return results.fetchall()
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return []
        
        
    def sell(product_id, quantity):
        try:
            with engine.begin() as conn:
                conn.execute(text(f"UPDATE Inventory SET quantity_in_stock = quantity_in_stock - :quantity WHERE product_id = :product_id"), {"quantity": quantity, "product_id": product_id})
                conn.commit()
            return True
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return False

        
    def update_quantity_in_stock(product_id, quantity):
        try:
            with engine.begin() as conn:
                conn.execute(text(f"UPDATE Inventory SET quantity_in_stock = :quantity WHERE product_id = :product_id"), {"quantity": quantity, "product_id": product_id})
                conn.commit()
            return True
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return False

        
    def update_reorder_level(product_id, reorder_level):
        try:
            with engine.begin() as conn:
                conn.execute(text(f"UPDATE Inventory SET reorder_level = :reorder_level WHERE product_id = :product_id"), {"reorder_level": reorder_level, "product_id": product_id})
                conn.commit()
            return True
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return False

class Reorders():
    def __init__(self, product_id, product_name, reorder_quantity):
        self.product_id=product_id
        self.product_name=product_name
        self.reorder_quantity=reorder_quantity

    def get_reorder_products():
        try:
            with engine.begin() as conn:
                query = """
                        SELECT r.product_id, p.product_name, r.reorder_quantity AS quantity_to_be_reordered
                        FROM to_reorder AS r
                        JOIN Products AS p ON r.product_id = p.product_id """
                results = conn.execute(text(query))
                reorder_products = [Reorders(product_id=row[0], product_name=row[1], reorder_quantity=row[2]) for row in results.fetchall()]
                return reorder_products
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return []
            
class CartItem:
    def __init__(self, product, quantity):
        self.product = product
        self.quantity = quantity

    @property
    def price(self):
        return self.product.price * self.quantity

    def add_quantity(self, quantity):
        self.quantity += quantity

    def remove_quantity(self, quantity):
        self.quantity -= quantity

    def __repr__(self):
        return f"CartItem({self.product.product_name}, {self.quantity})"

class Cart:
    def __init__(self):
        self.items = []

    def add(self, product, quantity):
            # Check if the product is already in the cart
            for item in self.items:
                if item.product.product_id == product.product_id:
                    # Increase the quantity but never make it go higher than a specified value
                    new_quantity = item.quantity + quantity
                    if new_quantity > product.get_quantity():
                        item.quantity = product.get_quantity()
                    else:
                        item.quantity = new_quantity
                    break
            else:
                # Add the product to the cart if it doesn't exist
                self.items.append(CartItem(product, quantity))

                # Convert the Cart object to a dictionary for easier serialization
            cart_dict = {'items': [{'product_id': item.product.product_id, 'quantity': item.quantity} for item in self.items]}

            # Store the cart dictionary in the session
            session['cart'] = cart_dict

    @property
    def total_amount(self):
        return sum(item.price for item in self.items)

    @classmethod
    def get_cart(cls):
        # Get the shopping cart from the session or initialize it as a new Cart object
        cart_dict = session.get('cart', {'items': []})
        if not cart_dict or 'items' not in cart_dict or not cart_dict['items']:
        # If the cart is not in session, or 'items' key is not in the cart, or the cart is empty,
        # initialize it with an empty list of items
            cart_dict = {'items': []}
        # Convert the dictionary to a list of CartItem objects
        cart = cls()
        for item in cart_dict['items']:
            product = Products.get_product_w_id(item['product_id'])
            cart.add(product, item['quantity'])

        return cart

    @classmethod
    def add_to_cart(self, product_id, quantity):
        # Get the shopping cart from the session
        cart = self.get_cart()

        # Find the product in the database
        product = Products.get_product_w_id(product_id)

        # Add the product to the cart or update the quantity if it already exists
        for item in cart.items:
            if item.product.product_id == product_id:
                item.quantity += quantity
                break
        else:
            # Add the product to the cart if it doesn't exist
            cart.add(product, quantity)

        # Convert the Cart object to a dictionary for easier serialization
        cart_dict = {'items': [{'product_id': item.product.product_id, 'quantity': item.quantity} for item in cart.items]}

        # Store the cart dictionary in the session
        session['cart'] = cart_dict


    @classmethod
    def update_quantity(cls, product_id, quantity):
        # Get the shopping cart from the session
        cart = cls.get_cart()

        # Find the product in the cart
        for item in cart.items:
            if item.product.product_id == product_id:
                # Update the quantity
                item.quantity = quantity
                break

        # Convert the Cart object to a dictionary for easier serialization
        cart_dict = {'items': [{'product_id': item.product.product_id, 'quantity': item.quantity} for item in cart.items]}

        # Store the cart dictionary in the session
        session['cart'] = cart_dict

    @classmethod
    def remove_item(cls, product_id):
        # Get the shopping cart from the session
        cart = cls.get_cart()

        # Find the product in the cart
        for i, item in enumerate(cart.items):
            if item.product.product_id == product_id:
                # Remove the item from the cart
                del cart.items[i]
                break

        # Convert the Cart object to a dictionary for easier serialization
        cart_dict = {'items': [{'product_id': item.product.product_id, 'quantity': item.quantity} for item in cart.items]}

        # Store the cart dictionary in the session
        session['cart'] = cart_dict

    @staticmethod
    def clear():
        session['cart'] = {}
        print("Cart cleared") if not session['cart'] else print("Cart not cleared")

class Suppliers():
    def __init__(self, supplier_id, supplier_name, email, mobile):
        self.supplier_id = supplier_id
        self.supplier_name = supplier_name
        self.email = email
        self.mobile = mobile
        
    def get_all():
        try:
            with engine.begin() as conn:
                result = conn.execute(text("SELECT * FROM Suppliers"))
                suppliers = [Suppliers(supplier_id=row[0], supplier_name=row[1], email=row[2], mobile=row[3]) for row in result.fetchall()]
                return suppliers
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return []

        
    def delete_supplier_with_id(supplier_id):
        try:
            with engine.begin() as conn:
                conn.execute(text(f"DELETE FROM Suppliers WHERE supplier_id = '{supplier_id}'"))
                conn.commit()
                return True
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return False

        
    def update_supplier(supplier, supplier_id):
        try:
            with engine.begin() as conn:
                conn.execute(text(f"UPDATE Suppliers SET supplier_name = :supplier_name, email = :email, mobile = :mobile WHERE supplier_id = :supplier_id"),
                             {"supplier_name": supplier.supplier_name, "email": supplier.email, "mobile": supplier.mobile, "supplier_id": supplier_id})
                conn.commit()
                return True
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return False
        
    def get_supplier_w_id(supplier_id):
        try:
            with engine.begin() as conn:
                result = conn.execute(text(f"SELECT * FROM Suppliers WHERE supplier_id = '{supplier_id}'"))
                sup_data = result.fetchone()
                if sup_data:
                    return Suppliers(supplier_id=sup_data[0], supplier_name=sup_data[1], email=sup_data[2], mobile=sup_data[3])
                else:
                    flash("Supplier not found", "error")
                    return None
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return None

            
    def add_supplier(self):
        try:
            with engine.begin() as conn:
                conn.execute(text(f"INSERT INTO Suppliers (supplier_id, supplier_name, email, mobile) VALUES ('{self.supplier_id}', '{self.supplier_name}', '{self.email}', '{self.mobile}')"))
                conn.commit()
                return True
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return False
        
    def get_latest_supplier_id():
        try:
            with engine.begin() as conn:
                result = conn.execute(text("SELECT supplier_id FROM Suppliers ORDER BY supplier_id DESC LIMIT 1"))
                latest_sup_id = result.fetchone()
                if latest_sup_id is not None:
                    return latest_sup_id[0]
                else:
                    return 0
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return None

            
    def check_email(email):
        try:
            with engine.begin() as conn:
                result = conn.execute(text(f"SELECT * FROM Suppliers WHERE email = '{email}'"))
                return result.rowcount > 0
        except SQLAlchemyError as e:
            print("Database error:", e)
            # Flash a generic error message to the user
            flash("An error occurred while fetching data. Please try again later.", "error")
            # Return a default value or handle the error as needed
            return False
            

def user_has_role(user_id, role_name):
    try:
        with engine.begin() as conn:
            result = conn.execute(text(f"SELECT 1 FROM UserRoles ur JOIN Roles r ON ur.role_id = r.role_id WHERE ur.emp_id = :user_id AND r.role_name = :role_name"), {"user_id": user_id, "role_name": role_name})
            return result.fetchone() is not None
    except SQLAlchemyError as e:
        print("Database error:", e)
        # Flash a generic error message to the user
        flash("An error occurred while fetching data. Please try again later.", "error")
        # Return a default value or handle the error as needed
        return False
    
def add_role(user_id, role_name):
    try:
        with engine.begin() as conn:
            result = conn.execute(text(f"SELECT role_id FROM Roles WHERE role_name = :role_name"), {"role_name": role_name})
            role_id = result.fetchone()[0]
            conn.execute(text(f"INSERT INTO UserRoles (emp_id, role_id) VALUES (:user_id, :role_id)"), {"user_id": user_id, "role_id": role_id})
            conn.commit()
            return True
    except SQLAlchemyError as e:
        print("Database error:", e)
        # Flash a generic error message to the user
        flash("An error occurred while fetching data. Please try again later.", "error")
        # Return a default value or handle the error as needed
        return False
    
def remove_role(user_id, role_name):
    try:
        with engine.begin() as conn:
            result = conn.execute(text(f"SELECT role_id FROM Roles WHERE role_name = :role_name"), {"role_name": role_name})
            role_id = result.fetchone()[0]
            conn.execute(text(f"DELETE FROM UserRoles WHERE emp_id = :user_id AND role_id = :role_id"), {"user_id": user_id, "role_id": role_id})
            conn.commit()
            return True
    except SQLAlchemyError as e:
        print("Database error:", e)
        # Flash a generic error message to the user
        flash("An error occurred while fetching data. Please try again later.", "error")
        # Return a default value or handle the error as needed
        return False
    
def get_roles():
    try:
        with engine.begin() as conn:
            result = conn.execute(text("SELECT * FROM Roles"))
            roles_data = result.fetchall()
            roles = []
            for role in roles_data:
                roles.append(role[1])
            return roles
    except SQLAlchemyError as e:
        print("Database error:", e)
        # Flash a generic error message to the user
        flash("An error occurred while fetching data. Please try again later.", "error")
        # Return a default value or handle the error as needed
        return []
    
def update_role(user_id, role_name):
    try:
        with engine.begin() as conn:
            result = conn.execute(text(f"SELECT role_id FROM Roles WHERE role_name = :role_name"), {"role_name": role_name})
            role_id = result.fetchone()[0]
            conn.execute(text(f"UPDATE UserRoles SET emp_id = :user_id WHERE role_id = :role_id"), {"user_id": user_id, "role_id": role_id})
            conn.commit()
            return True
    except SQLAlchemyError as e:
        print("Database error:", e)
        # Flash a generic error message to the user
        flash("An error occurred while fetching data. Please try again later.", "error")
        # Return a default value or handle the error as needed
        return False

def get_mysql_week(date):
    try:
        with engine.begin() as conn:
            result = conn.execute(text(f"SELECT WEEK(:date)"), {"date": date})
            week = result.fetchone()
            return week[0]
    except SQLAlchemyError as e:
        print("Database error:", e)
        # Flash a generic error message to the user
        flash("An error occurred while fetching data. Please try again later.", "error")
        # Return a default value or handle the error as needed
        return None
