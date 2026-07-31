## sherlock
sherlock is a tool whose primary purpose is to  make it easier to find any lecturer's phone number . It solves the  problem of having  an endless loop where every semester , class representatives have to keep asking the same  question: `Where do I find the phone numbers of the 8 lecturers who are taking my class this semester?`. The fix always is to go to whatsapp groups and ask for their contancts or ask other lecturer's for their contacts. The 
loop continues because the same people who volunteer the phone numbers are bound to volunteer them again and again...forever...or at least until they graduate. sherlock makes it possible that once a lecturer's number is volunteered by anyone , it remains persistent in the central database and anyone who would want that number would just search it up and they would find it. 

For convinience , sherlock  aims to be as close to the users as it can possibly be.Therefore , it's functionality which includes :

`1. Searching a lecturer
 2.Adding a lecturer `
 
 are done through whatsapp. What that means for the users is that , they can find any lecturer on the database without having to leave whatsapp and can also add a lecturer to the database without ever leaving the plattform.


## Privacy
As it is , anybody with the number through which sherlock is registered  can find any lecturer information if they knew their name. I am aware that that is a breach of data privacy laws , with time , I will improve the system to make it as though only class rep numbers can querry and search for lecturer numbers , therefore limiting the scope. Any one else will be shadow banned . This feature is not available yet as this is just an MVP.

The data sherlock obtains from it's users are their phone number, their user name and the text they send. All this is done through META servers and therefore is  not prone to interferance . If sherlock ever gets into production, it means that it complies with META laws which should make it safe for everyone using it. 

## Contribution
All forms of contribution are welcomed: both ideological and code . If the contribution is ideological , meaning you want to contribute to a feature or report a bug , you can do it  on the issues tab . If your contribution is code , make sure to adhere to the following guidlines:

    1.Make sure you understand the project before you can make a PR. I spent so much time on this project and therefore , making uploads of AI slop are not recommended. If you have to use AI to contribute , make sure you under      stand what you are doing.

    2. Write intentional Pull Requests . Your PR should clearly highlight what you are trying to change , why you are trying to change and how it improves the overall functionaluty of the system. It should be in the form :
       change  x improves y by doing z.

All contribution is welcomed.

## Project structure
Currently       

## Project structure
Currently

```
sherlock/
├── api.py             # FastAPI app — REST endpoints
├── main.py            # Entry point / WhatsApp bot runner
├── conversation.py    # Menu-driven WhatsApp conversation flow (search/add lecturer)
├── database.py        # DB connection and query logic
├── lecturer.db         # SQLite database (lecturer records)
└── README.md
``

