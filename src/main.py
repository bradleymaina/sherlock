from database import create_table, add_lecturer, lecturer_lookup

def main():
    create_table()

    while True:
        print("\n ===sherlock===")
        print("1. Add Lecturer")
        print("2. Search Lecturer")
        print("q. quit")

        choice = input("Select an option (1 , 2, q): ").strip()

        if choice == '1':
            first_name = input("Enter First Name: ")
            last_name = input("Enter Last Name: ")
            phone_number = input("Enter Phone Number: ")

            option = input(f"Are you sure you want to add {first_name.capitalize()} {last_name.capitalize()} with phone {phone_number} (y/n)?").strip()
            if option == 'y':
                result = add_lecturer(first_name, last_name, phone_number)

                if result["status"] == "success":
                    print(result["status"])
                    print(result["data"])
                else:
                    print(result["message"])
            elif option == 'n':
                print("Addition cancelled!")
            else:
               print("Invalid choice. Enter either y or n")
        elif choice == '2':
            search_name = input("Who are you trying to find? ") 

            result = lecturer_lookup(search_name)

            if result["status"] == "success":
                print(result["status"])
                print(result["data"])

            else:
                print(result["message"])

        elif choice == 'q':
            print("Goodbye")
            break
        else:
            print("Invalid choice. Choose either 1, 2 or 3")


if  __name__ == "__main__":
    main()

        


    
