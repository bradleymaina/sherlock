START = "START"
MENU = "MENU"

#Add Lecturer
WAITING_FOR_FIRST_NAME = "WAITING_FOR_FIRST_NAME"
WAITING_FOR_LAST_NAME = "WAITING_FOR_LAST_NAME"
WAITING_FOR_PHONE_NUMBER = "WAITING_FOR_PHONE_NUMBER"

#Search for Lecturer
WAITING_FOR_LECTURER_NAME = "WAITING_FOR_LECTURER_NAME"

states = {}

def set_state(phone, state):
    states[phone] = state

def get_state(phone):
    return states.get(phone)

def process_message(phone, msg):
    state = get_state(phone)

    if state is None:
        set_state(phone, MENU)
        state = START

    elif state == MENU:

        if msg == "add_lecturer":
            set_state(phone, WAITING_FOR_FIRST_NAME) 

        elif msg == "search_lecturer":
            set_state(phone, WAITING_FOR_SEARCH_NAME)

    elif state == WAITING_FOR_FIRST_NAME:
        set_state(phone, WAITING_FOR_LAST_NAME)

    elif state == WAITING_FOR_LAST_NAME:
        set_state(phone, WAITING_FOR_PHONE_NUMBER)

    elif state == WAITING_FOR_PHONE_NUMBER:
        set_state(phone, MENU)