from database import add_lecturer, lecturer_lookup

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
   
    elif state == MENU:

        if msg == "add_lecturer":
            set_state(wa_id, WAITING_FOR_FIRST_NAME) 
            
            
        elif msg == "search_lecturer":
            set_state(wa_id, WAITING_FOR_LECTURER_NAME)

    elif state == WAITING_FOR_LECTURER_NAME:
        sessions[wa_id]["lecturer_name"] = msg
        lecturer_lookup(sessions[wa_id]["lecturer_name"])

    elif state == WAITING_FOR_FIRST_NAME:
        set_state(wa_id, WAITING_FOR_LAST_NAME)
        sessions[wa_id]["first_name"] = msg

    elif state == WAITING_FOR_LAST_NAME:
        set_state(wa_id, WAITING_FOR_PHONE_NUMBER)
        sessions[wa_id]["last_name"] = msg

    elif state == WAITING_FOR_PHONE_NUMBER:
        set_state(wa_id, MENU)
        sessions[wa_id]["phone_number"] = msg

        add_lecturer(sessions[wa_id]["first_name"], sessions[wa_id]["last_name"], sessions[wa_id]["phone_number"])
    