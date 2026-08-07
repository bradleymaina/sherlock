from .database import add_lecturer, lecturer_lookup

MENU = "MENU"

#Add Lecturer
WAITING_FOR_FIRST_NAME = "WAITING_FOR_FIRST_NAME"
WAITING_FOR_LAST_NAME = "WAITING_FOR_LAST_NAME"
WAITING_FOR_PHONE_NUMBER = "WAITING_FOR_PHONE_NUMBER"

#Search for Lecturer
WAITING_FOR_LECTURER_NAME = "WAITING_FOR_LECTURER_NAME"

sessions = {}

def set_state(wa_id, state):
    if wa_id not in sessions:
        sessions[wa_id] = {
            "state": state
        }
    else:
        sessions[wa_id]["state"] = state

def get_state(wa_id):
    session = sessions.get(wa_id)

    if session is None:
        return None

    return session["state"]

def process_message(wa_id, msg):
    state = get_state(wa_id)

    if state is None:
        set_state(wa_id, MENU)
        state = MENU
   
    if state == MENU:
        if msg == "hello":
            return "Welcome to sherlock.I am a virtual assistant that makes it easy to find lecturers and add them to the database."
        
        if msg == "add_lecturer":
            set_state(wa_id, WAITING_FOR_FIRST_NAME) 
            return "Please enter the lecturer's first name."
            
        elif msg == "search_lecturer":
            set_state(wa_id, WAITING_FOR_LECTURER_NAME)
            return "Please enter the lecturer's name you want to search for."
        else:
            return "Invalid option!"

    elif state == WAITING_FOR_LECTURER_NAME:
        sessions[wa_id]["lecturer_name"] = msg

        result = lecturer_lookup(sessions[wa_id]["lecturer_name"])

        if result["status"] == "success":
            response = ""
            for lecturer in result["data"]:
                first_name = lecturer["first_name"]
                last_name = lecturer["last_name"]
                phone_number = lecturer["phone_number"]
                response += f"Found lecturer: {first_name} {last_name} with phone number {phone_number}.\n"
            return response.strip()

    elif state == WAITING_FOR_FIRST_NAME:
        set_state(wa_id, WAITING_FOR_LAST_NAME)
        sessions[wa_id]["first_name"] = msg
        return "Please enter the lecturer's last name."

    elif state == WAITING_FOR_LAST_NAME:
        set_state(wa_id, WAITING_FOR_PHONE_NUMBER)
        sessions[wa_id]["last_name"] = msg
        return "Please enter the lecturer's phone number."

    elif state == WAITING_FOR_PHONE_NUMBER:
        sessions[wa_id]["phone_number"] = msg

        result = add_lecturer(sessions[wa_id]["first_name"], sessions[wa_id]["last_name"], sessions[wa_id]["phone_number"])

        if result["status"] == "success":
            first_name = sessions[wa_id]["first_name"]
            last_name = sessions[wa_id]["last_name"]    
            phone_number = sessions[wa_id]["phone_number"]

            del sessions[wa_id]

            return(
                f"Lecturer {first_name} {last_name} "
                f"with phone number {phone_number} has been added successfully."
            )

        return result["data"]

       
        #TODO: Fix the search lecturer function.
        #TODO: Add confirmation loop