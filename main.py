import sqlite3
 
# use context manager to connect to the database
conn = sqlite3.connect("lecturer.db")
csr = conn.cursor()

csr.execute('''CREATE TABLE IF NOT EXISTS lecturer_table (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    phone_number TEXT NOT NULL
    ) ''')


country_code = "+254";
id = 0;
first_name = input("Enter lecturer first name: ").strip();
last_name = input("Enter lecturer last name: ").strip();
phone_number = input(f"Enter lecturer phone number: {country_code}").strip();

phone_number = country_code + phone_number;

if len(phone_number) != 13:
    print("Invalid phone number. Please enter a valid 13 digit phone number.")
    exit()


csr.execute('''INSERT INTO lecturer_table (first_name, last_name, phone_number) VALUES (?, ?, ?)''', (first_name, last_name, phone_number))
conn.commit()

print("Lecturer added successfully!")

conn.close()
