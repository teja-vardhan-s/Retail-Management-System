-- Employees Table
CREATE TABLE Employees (
    emp_id INT PRIMARY KEY AUTO_INCREMENT,
    emp_name VARCHAR(50) NOT NULL,
    password_hash VARCHAR(100) NOT NULL,
    salary DECIMAL(10, 2) NOT NULL
);

CREATE TABLE Employee_Details (
    emp_id INT PRIMARY KEY,
    dob DATE NOT NULL,
    doj DATE NOT NULL,
    gender_id INT NOT NULL,
    email VARCHAR(50) NOT NULL,
    mobile VARCHAR(10) NOT NULL,
    FOREIGN KEY (emp_id) REFERENCES Employees(emp_id) ON DELETE CASCADE
);

CREATE TABLE Gender (
    gender_id INT PRIMARY KEY,
    gender_name VARCHAR(10) NOT NULL
);


-- Activities Table
CREATE TABLE Activity_Type (
    activity_type_id INT PRIMARY KEY,
    activity_type_name VARCHAR(10) NOT NULL
);

CREATE TABLE Activities (
    activity_id INT PRIMARY KEY AUTO_INCREMENT,
    emp_id INT NOT NULL,
    activity_time TIME NOT NULL,
    activity_date DATE NOT NULL,
    activity_type_id INT NOT NULL,
    FOREIGN KEY (emp_id) REFERENCES Employees(emp_id) ON DELETE CASCADE,
    FOREIGN KEY (activity_type_id) REFERENCES Activity_Type(activity_type_id)
);

-- Customers Table
CREATE TABLE Customers (
    customer_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_name VARCHAR(50) NOT NULL
);

CREATE TABLE Contact_Details (
    customer_id INT PRIMARY KEY,
    email VARCHAR(50) NULL,
    mobile VARCHAR(10) NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id) ON DELETE CASCADE
);


-- Transactions Table
CREATE TABLE Transactions (
    tran_id INT PRIMARY KEY AUTO_INCREMENT,
    date_time DATETIME NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    payment_method VARCHAR(20) NOT NULL,
    cust_id INT NOT NULL,
    FOREIGN KEY (cust_id) REFERENCES Customers(customer_id)
);


-- Category Table
CREATE TABLE Category (
    category_id INT PRIMARY KEY AUTO_INCREMENT,
    category_name VARCHAR(50) NOT NULL
);

-- Products Table
CREATE TABLE Products (
    product_id INT PRIMARY KEY AUTO_INCREMENT,
    product_name VARCHAR(50) NOT NULL,
    description TEXT NULL,
    price DECIMAL(10, 2) NOT NULL,
    category_id INT NOT NULL,
    FOREIGN KEY (category_id) REFERENCES Category(category_id)
);


-- Transaction_Item Table
CREATE TABLE Transaction_Item (
    tran_item_id INT PRIMARY KEY AUTO_INCREMENT,
    tran_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    subtotal DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (tran_id) REFERENCES Transactions(tran_id),
    FOREIGN KEY (product_id) REFERENCES Products(product_id)
);


-- Suppliers Table
CREATE TABLE Suppliers (
    supplier_id INT PRIMARY KEY AUTO_INCREMENT,
    supplier_name VARCHAR(50) NOT NULL,
    email VARCHAR(50) NULL,
    mobile VARCHAR(10) NOT NULL
);


-- Inventory Table
CREATE TABLE Inventory (
    product_id INT PRIMARY KEY,
    supplier_id INT NOT NULL,
    quantity_in_stock INT NOT NULL,
    reorder_level INT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES Products(product_id),
    FOREIGN KEY (supplier_id) REFERENCES Suppliers(supplier_id)
);


-- Roles and UserRoles Tables
CREATE TABLE Roles (
    role_id INT PRIMARY KEY,
    role_name VARCHAR(20) UNIQUE NOT NULL
);

CREATE TABLE UserRoles (
    emp_id INT,
    role_id INT,
    PRIMARY KEY (emp_id, role_id),
    FOREIGN KEY (emp_id) REFERENCES Employees(emp_id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES Roles(role_id)
);

CREATE TABLE to_reorder (
    product_id INT PRIMARY KEY,
    reorder_quantity INT NOT NULL
);

--trigger
DELIMITER //

DELIMITER //

CREATE TRIGGER ReorderTrigger
AFTER UPDATE ON Inventory
FOR EACH ROW
BEGIN
    DECLARE reorder_qty INT;

    -- Calculate reorder quantity
    SET reorder_qty = NEW.quantity_in_stock - NEW.reorder_level;

    -- Check if quantity in stock is less than reorder level
    IF reorder_qty < 0 THEN
        -- Check if the product_id already exists in to_reorder table
        IF EXISTS (SELECT 1 FROM to_reorder WHERE product_id = NEW.product_id) THEN
            -- Update existing record
            UPDATE to_reorder
            SET reorder_quantity = -reorder_qty
            WHERE product_id = NEW.product_id;
        ELSE
            -- Insert new record
            INSERT INTO to_reorder (product_id, reorder_quantity)
            VALUES (NEW.product_id, -reorder_qty);
        END IF;
    ELSEIF reorder_qty > 0 THEN
        -- Remove the record from to_reorder table
        DELETE FROM to_reorder WHERE product_id = NEW.product_id;
    END IF;
END //

DELIMITER ;

--INSERT INTO statements

INSERT INTO Gender VALUES (1, 'M');
INSERT INTO Gender VALUES (2, 'F');
INSERT INTO Employees(emp_name, password_hash, salary) VALUES ('John Doe', 'password', 12000);
insert into Employee_Details (emp_id, dob, doj, gender_id, email, mobile) VALUES (1, '1990-01-01', '2020-01-01', 1, 'johndoe@gmail.com', 1234567890);
INSERT INTO Activity_Type VALUES (1, 'login');
INSERT INTO Activity_Type VALUES (2, 'logout');
INSERT INTO Roles VALUES (1, 'ADMIN');
INSERT INTO Roles VALUES (2, 'CASHIER');




