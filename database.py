## NOTES 
#add sql  functionality that allows indexing
import sqlite3

def get_db():
    #uncomment this line
    #database = 'sherlock.db'
    #comment this line out 
    database = 'lecturer.db'
    connection = sqlite3.connect(database)
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

def add_lecturer(first_name, last_name, phone_number):

    first_name = first_name.strip().title()
    last_name = last_name.strip().title()
    phone_number = phone_number.strip()

    #validate name later
    
    if len(phone_number) != 10 or not phone_number.isdigit():
        return{
            "status" : "error",
            "message" : "A phone number must be exactly 10 digits!"
        }
    
    
    connection, cursor = get_db()

    try:
        cursor.execute('''
            INSERT INTO Lecturers (first_name, last_name, phone_number)
            VALUES (?, ?, ?)
            ''',(first_name, last_name, phone_number))

        
        new_id = cursor.lastrowid
        
        connection.commit()
        return {
            "status" : "success",
            "data" : {
                "id" : new_id,
                "first_name" : first_name,
                "last_name" : last_name,
                "phone_number" : phone_number
            }
        }


    except sqlite3.IntegrityError:
        return {
            "status" : "error",
            "message" : "A lecturer with that phone number already exists!"
        }

    finally:
        connection.close()

def lecturer_lookup(search_name):
    search_name = search_name.strip().lower()

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
        lecturer_list = []

        for row in results:
            lecturer_list.append({
                "first_name": row[1],
                "last_name": row[2],
                "phone_number": row[3]
            })
        return {
            "status": "success",
            "count": len(lecturer_list),
            "data": lecturer_list
        }
            
    else:
        return {
            "status" : "error",
            "message" : "A lecturer by that name does not exist! "
        }
