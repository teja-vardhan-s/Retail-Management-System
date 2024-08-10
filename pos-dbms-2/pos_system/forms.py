from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, DateField, SelectField, DecimalField, SelectMultipleField, FieldList, FormField, validators
from wtforms.validators import Length, EqualTo, Email, DataRequired, ValidationError, AnyOf, InputRequired, NumberRange
from pos_system.database import Products, Inventory, Employee, get_roles, Suppliers

class MultiSelectField(FieldList):
    def __init__(self, *args, **kwargs):
        if 'min_entries' not in kwargs:
            kwargs['min_entries'] = 1
        if 'max_entries' not in kwargs:
            kwargs['max_entries'] = None
        super(MultiSelectField, self).__init__(*args, **kwargs)
        for field in self:
            field.flags[field.MIN_LENGTH] = field.flags[field.MAX_LENGTH] = kwargs['min_entries']

def max_quantity(max_value):
    def _max_quantity(form, field):
        if field.data > max_value:
            raise ValidationError(f"Quantity cannot exceed {max_value}.")
    return _max_quantity

class LoginForm(FlaskForm):
    emp_id = IntegerField(label='EmpID:', validators=[DataRequired()])
    password = PasswordField(label='Password:', validators=[DataRequired()])

    submit = SubmitField(label='Login')

#temporary registering 
class RegisterForm(FlaskForm):
        
    def validate_email_address(self, email_address_to_check):
        # Check if email already exists
        if Employee.check_email(email_address_to_check.data):
            raise ValidationError('Email Address already exists! Please try a different email address')

    empname = StringField(label='Username:', validators=[Length(min=2, max=30), DataRequired()])
    email_address = StringField(label='Email Address:', validators=[Email(), DataRequired(), validate_email_address])
    dob = DateField(label='Date of Birth:', validators=[DataRequired()])
    gender = SelectField(label='Gender:', choices=['M', 'F'], 
                         validators=[DataRequired()], validate_choice=True)
    mobile = IntegerField(label='Phone:', validators=[DataRequired()])
    salary = DecimalField(label='Salary', validators=[DataRequired()])
    password = PasswordField(label='Password:', validators=[Length(min=6), DataRequired()])
    confirm_password = PasswordField(label='Confirm Password:', validators=[EqualTo('password'), DataRequired()])

    submit = SubmitField(label='Add Employee')

class EditEmployeeForm(FlaskForm):

    empname = StringField(label='Username:', validators=[Length(min=2, max=30)])
    email_address = StringField(label='Email Address:', validators=[Email()])
    dob = DateField(label='Date of Birth:')
    doj = DateField(label='Date of Joining:')
    gender = SelectField(label='Gender:', choices=['M', 'F'], 
                          validate_choice=True)
    mobile = IntegerField(label='Phone:', validators=[ ])
    salary = DecimalField(label='Salary')
    password = PasswordField(label='Password:', validators=[Length(min=6)])
    confirm_password = PasswordField(label='Confirm Password:', validators=[EqualTo('password')])

    # Use the AnyOf validator to ensure that at least one of the fields is filled

    any_of_validator = AnyOf([DataRequired() for field in [empname, email_address, dob, gender, mobile, salary, password, confirm_password]])

    def validate_confirm_password(self, confirm_password):
        if self.password.data and not self.confirm_password.data:
            raise ValidationError('Confirm Password field is required if Password field is filled.')
        if self.password.data and self.confirm_password.data and self.password.data != self.confirm_password.data:
            raise ValidationError('Passwords do not match.')
    
    submit = SubmitField(label='Update', validators=[any_of_validator])

class AddCustomerForm(FlaskForm):
        
    cust_name = StringField(label='Customer Name', validators=[Length(min=2, max=30), DataRequired()])
    phone = IntegerField(label='Phone:', validators=[DataRequired()])
    email = StringField(label='Email Address:')

    submit = SubmitField(label='Add Customer')

class AddProductForm(FlaskForm):
    product_name = StringField(label='Product Name', validators=[Length(min=2, max=30), DataRequired()])
    description = StringField(label='Description:')
    price = DecimalField(label='Price:', validators=[DataRequired()])
    category = StringField(label='Category:', validators=[DataRequired()])

    submit = SubmitField(label='Add Product')

class EditProductForm(FlaskForm):
    product_name = StringField(label='Product Name', validators=[Length(min=2, max=30)])
    description = StringField(label='Description:')
    price = DecimalField(label='Price:')
    category = StringField(label='Category:')

    submit = SubmitField(label='Update')

class EditCustomerForm(FlaskForm):
        
    cust_name = StringField(label='Customer Name', validators=[Length(min=2, max=30)])
    phone = IntegerField(label='Phone:')
    email = StringField(label='Email Address:', validators=[Email()])

    submit = SubmitField(label='Update')


class ProductQuantityField(FlaskForm):
    product_id = IntegerField('Product ID', validators=[InputRequired()])
    quantity = IntegerField('Quantity', validators=[InputRequired(), NumberRange(min=1, max=Inventory.get_from_inventory(1).quantity_in_stock)])

class ProductQuantityForm(FlaskForm):
    products = SelectMultipleField('Products', coerce=int)

    def __init__(self, *args, **kwargs):
        super(ProductQuantityForm, self).__init__(*args, **kwargs)
        self.products.query = Products.get_all()

    def validate_products(self, products):
        selected_products = [p for p in products.data if p]
        if len(selected_products) < 1:
            raise ValidationError('At least one product must be selected.')
        for product_id in selected_products:
            product = Products.get_product_w_id(product_id)
            if not product:
                raise ValidationError(f'Product with ID {product_id} not found.')
            inventory = Inventory.get_from_inventory(product_id)
            if inventory.quantity_in_stock < 1:
                raise ValidationError(f'Product with ID {product_id} is out of stock.')
    def get_product_quantity_fields(self):
        fields = []
        for product_id in self.products.data:
            field = FormField(ProductQuantityField)
            field.product_id = product_id
            fields.append(field)
        return fields

    def get_product_quantity_fields(self):
        fields = []
        for product_id in self.products.data:
            field = FormField(ProductQuantityField)
            field.product_id = product_id
            fields.append(field)
        return fields


class CheckoutForm(FlaskForm):
    customer_id = SelectField('Customer:', validators=[DataRequired()])
    payment_method = SelectField('Payment Method:', validators=[DataRequired()], choices=['Cash', 'Credit Card', 'Debit Card', 'UPI'])
    submit = SubmitField('Checkout')

class AddEmployeeRoleForm(FlaskForm):
    employee_id = SelectField('Employee ID', validators=[DataRequired()], choices=[(emp.emp_id, f"{emp.emp_id} - {emp.emp_name}") for emp in Employee.get_all()])
    roles = SelectField('Role', validators=[DataRequired()], choices=[(role) for role in get_roles()])
    action1 = SubmitField('Add Role')
    action2 = SubmitField('Remove Role')
    action3 = SubmitField('Edit Role')

class AddSupplierForm(FlaskForm):
    def validate_email_address(self, email_address_to_check):
        # Check if email already exists
        if Suppliers.check_email(email_address_to_check.data):
            raise ValidationError('Email Address already exists! Please try a different email address')
        
    supplier_name = StringField(label='Supplier Name', validators=[Length(min=2, max=30), DataRequired()])
    mobile = IntegerField(label='Phone:', validators=[DataRequired()])
    email_address = StringField(label='Email Address:', validators=[Email(), DataRequired(), validate_email_address])

    submit = SubmitField(label='Add Supplier')

class EditSupplierForm(FlaskForm):

    supplier_name = StringField(label='Supplier Name', validators=[Length(min=2, max=30)])
    mobile = IntegerField(label='Phone:')
    email_address = StringField(label='Email Address:', validators=[Email()])

    submit = SubmitField(label='Update')

class EditProfileForm(FlaskForm):
    empname = StringField(label='Username:', validators=[Length(min=2, max=30)])
    email_address = StringField(label='Email Address:', validators=[Email()])
    dob = DateField(label='Date of Birth:')
    doj = DateField(label='Date of Joining:')
    gender = SelectField(label='Gender:', choices=['M', 'F'], 
                          validate_choice=True)
    mobile = IntegerField(label='Phone:')
    password = PasswordField(label='Password:', validators=[Length(min=6)])
    confirm_password = PasswordField(label='Confirm Password:', validators=[EqualTo('password')])

    # Use the AnyOf validator to ensure that at least one of the fields is filled

    any_of_validator = AnyOf([DataRequired() for field in [empname, email_address, dob, gender, mobile, password, confirm_password]])

    def validate_confirm_password(self, confirm_password):
        if self.password.data and not self.confirm_password.data:
            raise ValidationError('Confirm Password field is required if Password field is filled.')
        if self.password.data and self.confirm_password.data and self.password.data != self.confirm_password.data:
            raise ValidationError('Passwords do not match.')
    
    submit = SubmitField(label='Update', validators=[any_of_validator])