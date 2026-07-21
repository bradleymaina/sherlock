import sqlite3

def get_db():
    connection = sqlite3.connect('lecturer.db')
    return connection, connection.cursor()

def create_table():
    connection, cursor = get_db()

    create_table_query = '''
        CREATE TABLE IF NOT EXISTS Lecturers(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            phone_number TEXT UNIQUE NOT NULL
        );
'''
    cursor.execute(create_table_query)
    connection.commit()
    connection.close()

def add_lecturer():
    first_name = input("Enter First Name: ").strip().lower()
    last_name = input("Enter Last Name: ").strip().lower()
    phone_number = input("Enter Phone Number: ").strip()

    if len(phone_number) != 10 or not phone_number.isdigit():
        print("Enter a valid phone number")
        return
    
    #what does this line do ??
    connection, cursor = get_db()

    try:
        cursor.execute('''
            INSERT INTO Lecturers (first_name, last_name, phone_number)
            VALUES (?, ?, ?)
            ''',(first_name, last_name, phone_number))
        
        connection.commit()
        print(f"{first_name.capitalize()} {last_name.capitalize()} has been added to the database.")

    except sqlite3.IntegrityError:
        print(f"Error: {phone_number} already exists in the database")

    finally:
        connection.close()

def lecturer_lookup():
    search_name = input("Who are you trying to find? ").strip().lower()
    query_param = f"%{search_name}%"

    connection, cursor = get_db()
    cursor.execute ('''
        SELECT * FROM Lecturers
        WHERE first_name LIKE ?
         OR last_name LIKE ?
''',(query_param, query_param))
    
    results = cursor.fetchall()
    cursor.close()
    connection.close()

    if results:
        print("\n ---Search Results---")
        for row in results:
            print(f"{row[1].capitalize()}\t{row[2].capitalize()}\t{row[3]}")
    else:
        print("No Lecturer Found matching that name")

def main():
    create_table()

    while True:
        print("\n ===sherlock===")
        print("1. Add Lecturer")
        print("2. Search Lecturer")
        print("3. quit")

        choice = input("Select an option (1 , 2, q): ").strip()

        if choice == '1':
            add_lecturer()
        elif choice == '2':
            lecturer_lookup()
        elif choice == 'q':
            print("Goodbye")
            break
        else:
            print("Invalid choice. Choose either 1, 2 or 3")


if  __name__ == "__main__":
    main()

        


    
