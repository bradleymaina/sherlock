import sqlite3

conn = sqlite3.connect("lecturers.db")
csr = conn.cursor()

csr.execute('''CREATE TABLE IF NOT EXISTS lecturers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact TEXT NOT NULL
    ) ''')


public class Lecturer {
    private int id = 0;
    private String name = input("Enter lecturer name: ");
    private String contact = input("Enter lecturer contact: ");