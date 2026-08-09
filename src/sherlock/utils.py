def  format_phone_number(phone_number):
    phone_number = phone_number.strip()

    if phone_number.startswith("0"):
        return "+254" + phone_number[1:]

    return phone_number