from pos_system import app
from flask import render_template, redirect, url_for, request, flash, request
from pos_system.database import Employee, Activities, Customers, Transactions, Products, Cart, Transaction_Item, user_has_role, add_role, remove_role, update_role, Inventory, Suppliers, get_mysql_week, Reorders, test_conn
from pos_system.forms import RegisterForm, LoginForm , EditEmployeeForm, AddCustomerForm, AddProductForm, EditProductForm, EditCustomerForm, CheckoutForm, AddEmployeeRoleForm, AddSupplierForm, EditSupplierForm, EditProfileForm
from flask_login import login_user, logout_user, current_user
from datetime import datetime
from pos_system import bcrypt, session
import pdfkit # type: ignore
from flask import send_from_directory
import os
from functools import wraps
from flask import session, redirect, url_for


def role_required(role_name):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if current_user.is_authenticated:
                user_id = current_user.emp_id
            else:
                flash(f'Please login as {role_name} to access the page', 'info')
                return redirect(url_for('login_page'))
            if not user_has_role(user_id, role_name):
                return redirect(url_for('login_page'))
            return func(*args, **kwargs)
        return wrapper
    return decorator


@app.route("/")
def home():
    if test_conn:
        flash(test_conn(), 'success')
    return render_template("home.html")

@app.route("/login", methods=['GET', 'POST'])
def login_page():
    form = LoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        emp = Employee.check_emp(emp_id=form.emp_id.data, password=form.password.data)
        if emp:
            flash(f"Success! You are logged in as {emp.emp_name}", category='success')
            Activities.add_activity(emp.emp_id, "login")
            login_user(emp)
            session['username'] = emp.emp_name  # Set session variable
            return render_template("home.html")
        else:
            flash('Username and password are not match! Please try again.', category='danger')
    return render_template("login.html", form = form)

@app.route("/logout")
def logout_page():
    Activities.add_activity(current_user.emp_id, "logout")
    session.clear() #clear session
    logout_user()
    flash("You have been logged out!", category='info')
    return redirect(url_for('home'))

@app.route("/employee_management")
@role_required('ADMIN')
def employee_management():
    employees = Employee.get_all()
    activities = Activities.get_activities()
    return render_template("employee_management.html", employees=employees, activities=activities,
                           edit_form=EditEmployeeForm(), add_form=RegisterForm(), role_form=AddEmployeeRoleForm())

@app.route('/add_employee', methods=['GET', 'POST'])
@role_required('ADMIN')
def add_employee():
    form = RegisterForm()
    if form.validate_on_submit():
        if len(str(form.mobile.data)) != 10:
            flash('Mobile number must be 10 digits long.', 'danger')
            return redirect(url_for('employee_management'))
        user = Employee.create_emp(
                        username=form.empname.data,
                        email=form.email_address.data,
                        password=form.password.data,
                        dob=form.dob.data,
                        doj=datetime.today().date(),
                        gender=str(form.gender.data),
                        mobile=form.mobile.data,
                        salary=form.salary.data)
        # Activities.add_activity(user.emp_id, "login")
        # login_user(user)
        # session['username'] = user.emp_name  # Set session variable
        # flash(f"Account created successfully! You are now logged in as {user.emp_name}", category='success')
        return render_template("employee_management.html", employees=Employee.get_all(), activities=Activities.get_activities(),
                           edit_form=EditEmployeeForm(), add_form=RegisterForm(), role_form=AddEmployeeRoleForm())

    else:
        for errors in form.errors.values():
            for error in errors:
                flash(f"error: {error}", category='danger')
    return render_template("employee_management.html", add_form = form, edit_form=EditEmployeeForm(), 
                           employees=Employee.get_all(), activities=Activities.get_activities(), role_form=AddEmployeeRoleForm())

@app.route('/edit_employee/<int:id>', methods=['GET', 'POST'])
@role_required('ADMIN')
def edit_employee(id):
    employee = Employee.get_emp_w_id(id)
    employees = Employee.get_all()
    if request.method == 'POST' and request.form['submit'] == 'Update':
        employee.emp_name = request.form.get('empname') if request.form.get('empname') else employee.emp_name
        employee.email = request.form.get('email_address') if request.form.get('email_address') else employee.email
        employee.gender = request.form.get('gender') if request.form.get('gender') else employee.gender
        employee.dob = request.form.get('dob') if request.form.get('dob') else employee.dob
        employee.doj = request.form.get('doj') if request.form.get('doj') else employee.doj
        employee.mobile = request.form.get('mobile') if request.form.get('mobile') else employee.mobile
        employee.salary = request.form.get('salary') if request.form.get('salary') else employee.salary
        password = request.form.get('confirm_password')
        if password:
            employee.password_hash = bcrypt.generate_password_hash(password)
        if len(str(employee.mobile)) != 10:
            flash('Mobile number must be 10 digits long.', 'danger')
            return redirect(url_for('employee_management'))
        if Employee.update_employee(employee, id):
            flash('Employee updated successfully.', 'success')
            return redirect(url_for('employee_management'))
    return render_template('employee_management.html', employees=employees, edit_form=EditEmployeeForm(), add_form=RegisterForm(), 
                           role_form = AddEmployeeRoleForm() ,activities=Activities.get_activities())

@app.route('/delete_employee/<int:id>', methods=['POST'])
@role_required('ADMIN')
def delete_employee(id):
    if Employee.delete_emp_w_id(id):
        flash('Employee deleted successfully.', 'success')
    else:
        flash('Error deleting employee.', 'danger')
    return redirect(url_for('employee_management'))

@app.route('/handle_role', methods=['POST'])
@role_required('ADMIN')
def handle_role():
    emp_id = request.form.get('employee_id')
    role = request.form.get('roles')
    action1 = request.form.get('action1')  
    action2 = request.form.get('action2')  
    action3 = request.form.get('action3')  

    if emp_id and role:
        if action1 == 'Add Role':
            if add_role(emp_id, role):  
                flash('Role added successfully.', 'success')
            else:
                flash('Error adding role.', 'danger')
        elif action2 == 'Remove Role':
            if remove_role(emp_id, role):  
                flash('Role removed successfully.', 'success')
            else:
                flash('Error removing role.', 'danger')
        elif action3 == 'Update Role':
            if update_role(emp_id, role):  
                flash('Role updated successfully.', 'success')
            else:
                flash('Error updating role.', 'danger')
    else:
        flash('Please provide employee ID and role.', 'danger')

    return redirect(url_for('employee_management'))

@app.route('/customer_management')
@role_required('ADMIN')
def customer_management():
    customers=Customers.get_all()
    return render_template("customer_management/customer_management.html", customers=customers, add_form=AddCustomerForm(), edit_form=EditCustomerForm())


@app.route('/transactions/<int:cust_id>', methods=['POST'])
def get_customer_transactions(cust_id):
    transactions = Transactions.get_transactions(cust_id)
    return render_template('customer_management/customer_management.html', transactions=transactions,customers=Customers.get_all(), add_form=AddCustomerForm(), edit_form=EditCustomerForm())

@app.route('/open-transactions', methods=['GET','POST'])
def open_transactions():
    cust_id = request.form.get('customerId', session.get('cust_id'))
    transactions = Transactions.get_transactions(cust_id)
    return render_template('customer_management/transactions.html', transactions=transactions)

@app.route('/add-customer', methods=['POST'])
def add_customer():
    form = AddCustomerForm()
    if form.validate_on_submit():
        cust_id = Customers.get_latest_customer_id() + 1
        customer = Customers(cust_id=cust_id, cust_name=form.cust_name.data, cust_mobile=form.phone.data, cust_email=form.email.data)
        if len(str(customer.phone)) != 10:
            flash('Mobile number must be 10 digits long.', 'danger')
            return redirect(url_for('customer_management'))
        
        if customer.add_customer():
            flash('Customer added successfully.', 'success')
            return redirect(url_for('customer_management'))
    else:
        for errors in form.errors.values():
            for error in errors:
                flash(f"error: {error}", category='danger')
    return render_template('customer_management/customer_management.html', add_form=form, customers=Customers.get_all(), edit_form=EditCustomerForm())


@app.route('/edit-customer/<int:cust_id>', methods=['POST'])
def edit_customer(cust_id):
    customer = Customers.get_customer_w_id(cust_id)
    customers = Customers.get_all()
    if request.method == 'POST' and request.form['submit'] == 'Update':
        customer.cust_name = request.form.get('cust_name') if request.form.get('cust_name') else customer.cust_name
        customer.phone = request.form.get('phone') if request.form.get('phone') else customer.phone
        customer.email = request.form.get('email') if request.form.get('email') else customer.email
        if len(str(customer.phone)) != 10:
            flash('Mobile number must be 10 digits long.', 'danger')
            return redirect(url_for('customer_management'))
        if customer.update_customer(cust_id=cust_id):
            flash('Customer updated successfully.', 'success')
            return redirect(url_for('customer_management'))
    return render_template('customer_management/customer_management.html', customers=customers, add_form=AddCustomerForm(), edit_form=EditCustomerForm())

@app.route('/delete-customer', methods=['POST'])
def delete_customer():
    cust_id = request.form.get('cust_id')
    if Customers.delete_customer_w_id(cust_id):
        flash('Customer deleted successfully.', 'success')
    else:
        flash('Error deleting customer.', 'danger')
    return redirect(url_for('customer_management'))


@app.route('/product-management', methods=['GET','POST'])
@role_required('ADMIN')
def product_management():
    products = Products.get_all()
    return render_template('product_management.html', products=products, add_form=AddProductForm(), edit_form=EditProductForm())

@app.route('/add-product', methods=['POST'])
def add_product():
    form = AddProductForm()
    if form.validate_on_submit():
        product_id = Products.get_latest_product_id() + 1
        product = Products(product_id=product_id, product_name=form.product_name.data, description=form.description.data if form.description.data else None,
                            price=form.price.data, category=form.category.data)
        if Products.adds_product(product):
            return redirect(url_for('product_management'))
    else:
        for errors in form.errors.values():
            for error in errors:
                flash(f"error: {error}", category='danger')
    return render_template('product_management.html', add_form=form, products=Products.get_all(), edit_form=EditProductForm())

@app.route('/delete-product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if Products.delete_product_w_id(product_id):
        flash('Product deleted successfully.', 'success')
    else:
        flash('Error deleting product.', 'danger')
    return redirect(url_for('product_management'))

@app.route('/edit-product/<int:product_id>', methods=['POST'])
def edit_product(product_id):
    product = Products.get_product_w_id(product_id)
    products = Products.get_all()
    if request.method == 'POST' and request.form['submit'] == 'Update':
        product.product_name = request.form['product_name'] if request.form['product_name'] else product.product_name
        product.description = request.form['description'] if request.form['description'] else product.description
        product.price = request.form['price'] if request.form['price'] else product.price
        product.category = request.form['category'] if request.form['category'] else product.category
        if product.update_product(product_id=product_id):
            flash('Product updated successfully.', 'success')
            return redirect(url_for('product_management'))
    return render_template('product_management.html', products=products, add_form=AddProductForm(), edit_form=EditProductForm())


@app.route('/checkout', methods=['GET', 'POST'])
@role_required('CASHIER')
def checkout():
    form = CheckoutForm()
    if form.validate_on_submit():
        product = Products.get_product_w_id(form.product_id.data)
        if product:
            product.quantity += form.quantity.data
        return redirect(url_for('checkout'))
    products = Products.get_all()
    return render_template('transaction_process/checkout.html', title='Checkout', form=form, products=products)

@app.route('/confirm-order', methods=['GET', 'POST'])
def finalise_transaction():
    form = CheckoutForm()
    Customers.add_to_session()
    form.customer_id.choices = [(cust[0], f"{cust[0]} - {cust[1]}") for cust in session.get('customers', {}).items()]
    if form.validate_on_submit():
        cart = Cart.get_cart()
        transaction = Transactions(tran_id=(Transactions.get_latest_transaction_id()+1), date_time=datetime.now(), total_amount=cart.total_amount, payment_method=form.payment_method.data, cust_id=form.customer_id.data, emp_id=current_user.emp_id)
        transaction.add_transaction()
        transaction_items = []
        for item in cart.items:
            transaction_item = Transaction_Item(tran_item_id=(Transaction_Item.get_latest_transaction_item_id()+1), tran_id=Transactions.get_latest_transaction_id(), product_id=item.product.product_id, quantity=item.quantity, subtotal=(item.quantity * Products.get_price(item.product)))
            transaction_items.append(transaction_item)
            # Update the quantity_in_stock in the Inventory table
            Inventory.sell(item.product.product_id, item.quantity)
        for transaction_item in transaction_items:
            Transaction_Item.add_tr_item(tran_id=transaction_item.tran_id, product_id=transaction_item.product_id, quantity=transaction_item.quantity, subtotal=transaction_item.subtotal)
        Cart.clear()
        session['customers'] = {}
        flash('Order Purchased successfully.', 'success')
        customer = Customers.get_customer_w_id(form.customer_id.data)
        # Render the HTML invoice
        rendered = render_template('transaction_process/invoice.html', transaction=transaction, transaction_items=transaction_items, customer=customer)

        # Create a PDF file
        pdf = pdfkit.from_string(rendered, False)

        # Save the PDF to a file
        filename = f'invoice_{transaction.tran_id}.pdf'
        pdf_file = os.path.join('/home/teja/Documents/pos-dbms/pos_system/static/reports', filename)
        with open(pdf_file, 'wb') as f:
            f.write(pdf)

        # Redirect to the download route
        return redirect(url_for('download_invoice', filename=filename))
    return render_template('transaction_process/confirm_order.html', title='Confirm Order', form=form, customer_form=AddCustomerForm())


@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    quantity = int(request.form.get('quantity', 1))
    product = Products.get_product_w_id(product_id)
    cart = Cart.get_cart()
    cart.add(product, quantity)
    return redirect(url_for('view_cart'))

@app.route('/view_cart')
def view_cart():
    cart = Cart.get_cart()
    total_price = sum(item.price for item in cart.items)
    return render_template('transaction_process/view_cart.html', cart=cart, total_price=total_price)

@app.route('/update_quantity/<int:product_id>', methods=['POST'])
def update_quantity(product_id):
    quantity = int(request.form['quantity'])
    cart = Cart.get_cart()
    for item in cart.items:
        if item.product.product_id == product_id:
            item.quantity = quantity
            break
    cart.update_quantity(product_id, quantity)
    return redirect(url_for('view_cart'))

@app.route('/remove_item/<int:product_id>', methods=['POST'])
def remove_item(product_id):
    cart = Cart.get_cart()
    Cart.remove_item(product_id=product_id)
    return redirect(url_for('view_cart'))

@app.route('/clear_cart', methods=['GET'])
def clear_cart():
    Cart.clear()
    return redirect(url_for('view_cart'))

@app.route('/static/reports/<filename>')
def download_invoice(filename):
    # Define the path to the file
    directory = '/home/teja/Documents/pos-dbms/pos_system/static/reports'
    return send_from_directory(directory, filename, as_attachment=True)

@app.route('/add-customer-confirm-order', methods=['POST'])
@role_required('CASHIER')
def add_customer_at_confirm_order():
    form = AddCustomerForm()
    if form.validate_on_submit():
        cust_id = Customers.get_latest_customer_id() + 1
        customer = Customers(cust_id=cust_id, cust_name=form.cust_name.data, cust_mobile=form.phone.data, cust_email=form.email.data)
        if customer.add_customer():
            flash('Customer added successfully.', 'success')
            Customers.add_to_session()
            return redirect(url_for('finalise_transaction'))  # redirect back to the same page
    else:
        for errors in form.errors.values():
            for error in errors:
                flash(f"error: {error}", category='danger')
    return render_template('transaction_process/confirm_order.html', title='Confirm Order', form=CheckoutForm(), customer_form=AddCustomerForm())

@app.route('/transaction_items/<int:tran_id>', methods=['POST'])
def show_transaction_items(tran_id):
    transaction_items = Transaction_Item.get_transaction_items(tran_id)
    return render_template('customer_management/transaction_items.html', transaction_items=transaction_items, tran_id=tran_id)


@app.route('/inventory_management', methods=['GET'])
@role_required('ADMIN')
def inventory_management():
    low_stock_products = Reorders.get_reorder_products()
    products = Inventory.get_products()
    return render_template('inventory_management.html', low_stock_products=low_stock_products, products=products)

@app.route('/update_quantity_in_stock/<int:product_id>', methods=['POST'])
@role_required('ADMIN')
def update_quantity_in_stock(product_id):
    quantity = int(request.form['new_quantity'])
    Inventory.update_quantity_in_stock(product_id, quantity)
    return redirect(url_for('inventory_management'))

@app.route('/update_reorder_level/<int:product_id>', methods=['POST'])
@role_required('ADMIN')
def update_reorder_level(product_id):
    reorder_level = int(request.form['new_reorder_level'])
    Inventory.update_reorder_level(product_id, reorder_level)
    return redirect(url_for('inventory_management'))

@app.route('/supplier_management')
@role_required('ADMIN')
def supplier_management():
    suppliers = Suppliers.get_all()
    return render_template('supplier_management.html', add_form=AddSupplierForm(), edit_form=EditSupplierForm(), suppliers=suppliers)

@app.route('/supplier_management/add_supplier', methods=['POST'])
@role_required('ADMIN')
def add_supplier():
    add_form = AddSupplierForm()
    suppliers = Suppliers.get_all()
    if add_form.validate_on_submit():
        supplier_id = Suppliers.get_latest_supplier_id() + 1
        supplier = Suppliers(supplier_id=supplier_id, supplier_name=add_form.supplier_name.data, mobile=add_form.mobile.data, email=add_form.email_address.data)
        if len(str(supplier.mobile)) != 10:
            flash('Mobile number must be 10 digits long.', 'danger')
            return redirect(url_for('supplier_management'))
        
        if supplier.add_supplier():            
            flash('Supplier added successfully.', 'success')
            return redirect(url_for('supplier_management'))
    else:
        for errors in add_form.errors.values():
            for error in errors:
                flash(f"error: {error}", category='danger')
    return render_template('supplier_management.html', add_form=add_form, edit_form=EditSupplierForm(), suppliers=suppliers)

@app.route('/supplier_management/edit_supplier/<int:supplier_id>', methods=['POST'])
@role_required('ADMIN')
def edit_supplier(supplier_id):
    supplier = Suppliers.get_supplier_w_id(supplier_id)
    suppliers = Suppliers.get_all()
    if request.method == 'POST' and request.form['submit'] == 'Update':
        supplier.supplier_name = request.form.get('supplier_name') if request.form.get('supplier_name') else supplier.supplier_name
        supplier.mobile = request.form.get('mobile') if request.form.get('mobile') else supplier.mobile
        supplier.email = request.form.get('email') if request.form.get('email') else supplier.email

        if len(str(supplier.mobile)) != 10:
            flash('Mobile number must be 10 digits long.', 'danger')
            return redirect(url_for('supplier_management'))
        
        if supplier.update_supplier(supplier_id=supplier_id):
            flash('Supplier updated successfully.', 'success')
            return redirect(url_for('supplier_management'))
    return render_template('supplier_management.html', suppliers=suppliers, add_form=AddSupplierForm(), edit_form=EditSupplierForm())

@app.route('/supplier_management/delete_supplier/<int:supplier_id>', methods=['POST'])
def delete_supplier(supplier_id):
    if Suppliers.delete_supplier_w_id(supplier_id):
        flash('Supplier deleted successfully.', 'success')
    else:
        flash('Error deleting supplier.', 'danger')
    return redirect(url_for('supplier_management'))

@app.route('/profile')
def profile_page():
    edit_form = EditProfileForm()
    return render_template('profile.html', edit_form=edit_form)

def get_week_number(mysql_datetime):
    # Convert MySQL datetime string to Python datetime object
    mysql_datetime_obj = datetime.strptime(mysql_datetime, '%Y-%m-%d')

    # Extract week number using mode 0 of WEEK() function
    week_number = mysql_datetime_obj.isocalendar()[1]

    return week_number 

@app.route('/report-and-analytics', methods=['POST', 'GET'])
@role_required('ADMIN')
def report_and_analytics():
    sales_filter = request.form.get('sales_filter', 'daily') if request.method == 'POST' else 'daily'
    product_filter = request.form.get('product_filter', 'top_products') if request.method == 'POST' else 'top_products'
    transaction_filter = request.form.get('transaction_filter', 'payment_methods') if request.method == 'POST' else 'payment_methods'
    transaction_print_filter = request.form.get('transaction_print_filter', 'by_date') if request.method == 'POST' else 'by_date'
    product_data = Products.get_product_analysis(product_filter)
    result_dict = Transactions.get_total_sales_revenue(sales_filter)  #allah-hu-akbar
    transaction_data = Transactions.get_transaction_analysis(transaction_filter)
    
    
    date_str = request.form.get('date') if request.method == 'POST' and request.form.get('form') == 'print' else str(datetime.today().date())
    
    if date_str:
        date = date_str if(type(date_str) == datetime.date) else datetime.strptime(date_str, '%Y-%m-%d')

        week = get_mysql_week(date)
        month = date.month
        year = date.year
        print_filter = {'date': date, 'week': week, 'month': month, 'year': year}
        
    if transaction_print_filter == 'by_date':
        transaction_print_data = Transactions.get_transaction_analysis_by_date(print_filter['date'])
    elif transaction_print_filter == 'by_week':
        transaction_print_data = Transactions.get_transaction_analysis_by_week(print_filter['week'])
    elif transaction_print_filter == 'by_month':
        transaction_print_data = Transactions.get_transaction_analysis_by_month(print_filter['month'])
    elif transaction_print_filter == 'by_year':
        transaction_print_data = Transactions.get_transaction_analysis_by_year(print_filter['year'])
    else:
        transaction_print_data = Transactions.get_transaction_analysis_by_date(print_filter['date'])


    if request.form.get('form') == 'print':
        # Render the HTML invoice
        rendered = render_template('report_and_analytics/transaction_print_data.html', transaction_print_filter=transaction_print_filter, transaction_print_data=transaction_print_data)


        # Create a PDF file
        pdf = pdfkit.from_string(rendered, False)

        # Save the PDF to a file
        if transaction_print_filter == 'by_date':
            filename = f'transaction_data_{transaction_print_filter}_{print_filter["date"]}.pdf'
        elif transaction_print_filter == 'by_week':
            filename = f'transaction_data_{transaction_print_filter}_week_{print_filter["week"]}.pdf'
        elif transaction_print_filter == 'by_month':
            filename = f'transaction_data_{transaction_print_filter}_month_{print_filter["month"]}.pdf'
        elif transaction_print_filter == 'by_year':
            filename = f'transaction_data_{transaction_print_filter}_year_{print_filter["year"]}.pdf'

        pdf_file = os.path.join('/home/teja/Documents/pos-dbms/pos_system/static/reports', filename)
        with open(pdf_file, 'wb') as f:
            f.write(pdf)

        # Redirect to the download route
        return redirect(url_for('download_invoice', filename=filename))

        # return render_template('report_and_analytics/transaction_print_data.html', transaction_print_filter=transaction_print_filter, transaction_print_data=transaction_print_data)

    return render_template('report_and_analytics/report_and_analytics.html', sales_filter=sales_filter, product_filter = product_filter, result_items = result_dict.items(), transaction_print_data=transaction_print_data,
                           product_items= product_data, transaction_filter= transaction_filter, transaction_data=transaction_data, transaction_print_filter=transaction_print_filter)

