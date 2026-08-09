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
        msg = msg.lower().strip()
        if msg == "hello":
            return [
    {
        "type": "text",
        "body": "🕵️ *Hello. This is Sherlock — built to replace the need to ask around whenever you need a lecturer.*\n\nThe old system was good. It solved the problem through people, groups, questions, and replies. Sherlock is not marginally better than the merely good one. It is an order of magnitude better, measured by whatever standard: conceptual creativity, speed, ingenuity of design, or problem-solving ability.\n\nEvery lecturer and number here was contributed by someone who once needed the same answer. Add what you know; it may be the answer someone else needs tomorrow."
    },
    {
        "type": "list",
        "body": "What brings you to Sherlock today? Choose an option from the list below.",
        "button_title": "Choose your inquiry",
        "rows": [
            {
                "id": "add_lecturer",
                "title": "➕ Add a Lecturer",
                "description": "Add lecturer by providing first name, last name and phone number"
            },
            {
                "id": "search_lecturer",
                "title": "🔎 Find a Lecturer",
                "description": "Search by either first name or last name"
            }
        ]
    }
]
        
        
        if msg == "add_lecturer":
            set_state(wa_id, WAITING_FOR_FIRST_NAME) 
            return [
                {
                "type": "text",
                "body": "Please enter the lecturer's first name."
            }
            ]
            
        elif msg == "search_lecturer":
            set_state(wa_id, WAITING_FOR_LECTURER_NAME)
            return [
                {
                "type": "text",
                "body": "Please enter the lecturer's name you want to search for."
            }
            ]
        else:
            return [
                {
                "type": "text",
                "body": "Invalid option. Please select a valid option from the menu."}

            ]
    elif state == WAITING_FOR_LECTURER_NAME:
        sessions[wa_id]["lecturer_name"] = msg

        result = lecturer_lookup(sessions[wa_id]["lecturer_name"])

        if result["status"] == "success":

            response = []

            for lecturer in result["data"]:
                first_name = lecturer["first_name"]
                last_name = lecturer["last_name"]
                phone_number = lecturer["phone_number"]

                full_name = f"{first_name} {last_name}"

                contact = {
                    "name": {
                        "formatted_name": full_name
                    },
                    "phones": [
                        {
                            "phone": phone_number,
                        }
                    ]
                }
                response.append(contact)

            del sessions[wa_id]
            return [
                {
                    "type": "contacts",
                    "data": response
                }
            ]

        elif result["status"] == "error":
            return [
                {
                "type": "text",
                "body": result["message"]
            }
            ]

    elif state == WAITING_FOR_FIRST_NAME:
        set_state(wa_id, WAITING_FOR_LAST_NAME)
        sessions[wa_id]["first_name"] = msg
        return [
            {
            "type": "text",
            "body": "Please enter the lecturer's last name."    
        }
        ]

    elif state == WAITING_FOR_LAST_NAME:
        set_state(wa_id, WAITING_FOR_PHONE_NUMBER)
        sessions[wa_id]["last_name"] = msg
        return [
            {
            "type": "text",
            "body": "Please enter the lecturer's phone number."
        }
        ]

    elif state == WAITING_FOR_PHONE_NUMBER:
        sessions[wa_id]["phone_number"] = msg

        result = add_lecturer(sessions[wa_id]["first_name"], sessions[wa_id]["last_name"], sessions[wa_id]["phone_number"])

        if result["status"] == "success":
            first_name = sessions[wa_id]["first_name"]
            last_name = sessions[wa_id]["last_name"]    
            phone_number = sessions[wa_id]["phone_number"]

            del sessions[wa_id]

            return [
                {
                "type": "text",
                "body": f"Lecturer {first_name} {last_name} "
                        f"with phone number {phone_number} has been added successfully."
            }
            ]

        

       
        #TODO: Fix the search lecturer function.
        #TODO: Add confirmation loop