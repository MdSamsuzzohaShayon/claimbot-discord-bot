# Claimbot
 - [Prev github repo](https://github.com/Grimshad/Claimbot), [V2 Repo](https://github.com/Grimshad/Claimbotv2)
 - [Tutorial](https://www.youtube.com/watch?v=xBZp4t0tzdQ&list=PLuwK012tUglquEYi64dm6FtMRmXx9SpfJ)
 - [startup](https://github.com/Rapptz/discord.py/blob/v2.2.2/examples/advanced_startup.py)
 - Started at 5 April

### instructions

 ![Disgram](image/diagram.png)

 - **start, stop, release cycle**
 - basically, when we receive a new reservation event from Guesty, we add this reservation to the *available cleanings channel* [Discord]
 - from there, a cleaner[Discord user role] can accept the job
 - then it is moved into their personal list of cleanings
 - from there, they can release the cleaning back into the pool, or on the day of the cleaning they can start and then stop the cleaning when they finish
 - once completed. the pay for the cleaning is added to the cleaners pay
 - messages are sent directly to the cleaners to remind them about the job and notify them of changes to the job. messages are also sent in the admin notification channel to keep everyone up to date on who is cleaning what each day
 - No, no. The user can accept any task in the available tasks. The user cannot start the task until the day of the cleaning
 - Also, I forgot. Users cannot have multiple tasks on the same day
 - So do not allow users to accept a task for they already have a task on that day

 - **Pay calc**
 - And last thing I can think is. We need to keep yearly storage of cleaners and their pay, This table is updated when the cleaner completes the task
 - And then a way to pull the data for current and previous month 
 - We also keep a table of total pay per listing, and need to pull for current and previous month 
 - And then we found this system to be inaccurate. So we currently have a command to recalculate all pay for the current or previous months 
 - This command essentially loops through all the tasks for the month to calculate the pays again just in case it's incorrect

 - **Next task**
 - The cleaner should only be able to start the task the day of the task, but they should be able to complete the task at any point after it's started
 - The cleaners need to stay organized and focus on only the next task, but be able to see their upcoming tasks so they can plan. This is why we currently have a chart with tasks and only send the message for starting the day of 

 - **Notifications**
 - For notifications. There's the admin notifications and the cleaner notifications(DM). 
 - For admin notifications, every day it should send the details of who is cleaning which units, send a message when cleaners start and stop cleanings( lily you have already) , 

 - **Task update**
 - Send a message when a cleaning has been updated (including change of assignee or date) or cancelled
 - Cleaner notification should send the cleaner a dm the day prior to remind them of a task 
 - and the day of to remind them again as well as dm them if the task is cancelled
 - the date changes (if the assignee changes just say it was cancelled).
 - It would also be good if they did not start or stop the task to remind them to do so at a certain time of day

 - **Cleaning Payments**
 - When a cleaning is completed, add the cleanerpay to that cleaners total for the month, also add the cleanerpay to that listings total for the month. 
 - Reset these numbers every month 
 - The ability to get a list of the cleaners and their pay for the current, and previous month, as well as the listings totals for the current and previous months. 
 - A way to retrieve older data from other previous months 
 - The ability to recalculate the current or previous month directly from the tasks in guesty, because guesty may have been altered since we stored the data. We will recalculate at the end of the month before we pay people 
 - The ability to manually add an adjustment to the cleaners total 
 - The ability for a cleaner to click a button to retrieve their total pay for the current month

 - Send user a reminder like "You are cleaning NAME tomorrow at 10am"
 - And then "you are cleaning NAME today at 10am"
 - Something similar. Just to remind them so they don't forget

 - It means there is another reservation the same day
 - Yes 8am. Please account for daylight savings
 - If a guest checks out the same day another guest checks in it's a TA

 - **Repair**
 - Bessie clicked the complete button on her cleaning today and her channel disappeared. It seems to be deleted for me as well. And she still has new cleanings coming up 
 - You misunderstood my instructions for the upcoming channels. They should not be removed by the bot. They should just not be added unless the cleaner has a cleaning and the channel doesn't exist. 
 - You need to change the bot so that when it is restarted it doesn't clear and resend all the charts, people are getting annoyed by the message spam. We need to edit existing messages instead of making new ones.
 - You should not be pulling for start or complete, You should only be pushing the start and complete time


### Step by step
 - Delete 64b3d002d5dcdd003d28cf51, 64c59504727b4500377f8108, 64d8a42fb387a100369458d5, 64d8a7b43b955a0035ebd45f
 - Send an empty chart of tasks if a user does not have tasks within 7 days
 - Check all user message is it on the current user's  channel or not
 - When changing a task to unassigned in guesty it's not moving the task back to available in discord
 - Issues with assignee change handler
 - Test every hook -> response(response null or anything) to all webhooks
 - Match database status and webhook task status, if both does not match fetch the task from guesty and check status again
 - Check if the task is not in progress and Delete all messages that is not today from user channel and delete messages at hat are not within 7 days from available cleaning  
 - Check if message already exist in every function where we have added the task(very update hook functions)
 - When we are calling another ever afterward we are fetching we are getting that error - https://github.com/encode/httpx/issues/342
 - Fetching a message and a task 15 times without any other logic reference: utils.discord.CallbackOperations.CallbackOperations.task_add_callback_backup
 - Add a button with users charts beside release a task to rearrange user tasks
 - adjustment for get_listings_summary_callback is not working properly
 - Work with *add cleaning* to *complete cleaning* all callback functions of button (Use the latest proper data, use OrganizeGuestyData class)
 - ✅✅ Save adjustment with guesty_cleaning_id or guesty_user_id 
 - Make available cleaning channel public
 - Subdivide `send_daily_tasks_n_not` function from task daily controller and use them for both purpose, initializer
 - Change task database - Organize data model properly
 - Remove duplicate code by using functions in task daily controller (Create or update task, message or user)
 - The ability for a cleaner to click a button to retrieve their total pay for the specific month
 - Conditional (Not turn around) make it total functional
 - A way to retrieve older data from other previous specific months (Create a slash command and select year and month to achieve that)
 - Need to work on update event, for instance if status change to canceled and assignee change. if both happen, handle this event with efficiency (Database should keep at the bottom of the function to update all at once)
 - Watch some hyper v box tutorial
 - Clean up DatabaseMultiOperations
 - Get an userid from username in discord -> https://open-api-docs.guesty.com/reference/usershttpcontroller_getuserbyid  
 - **Task update webhook** -> check title is clean -> check status -> if status is completed do the same as did for on complete task button
 - **New reservation webhook** -> if any user has a reservation with same name and same date save a cleaner task 
 - [Assign a task](https://open-api-docs.guesty.com/reference/post_tasks-open-api-create-single-task) to cleaner in guesty (reservationId, startTime, endTime, assigneeId, title, description)
 - Release specific task and do the calculation
 - Check assignee change -> remove task from user -> remove from available cleaning channel -> move to new user cleanning channel
 - Clean code https://www.youtube.com/watch?v=qZpwlrp00n8 , ngrok tutorial
 - ✅✅ Date format to be month/day/year



### Permissions
 - Read message, Manage events, create events, send messages, use application commands
 - Req 11:37 APM, Res 12:20 PM

### Keyboard shortcuts
 - `Ctrl + B` Navigate to declaration
 - `Ctrl + Alt + 7` or `Alt + 7` view the list of all usages of a class, method or variable across the whole project, and quickly navigate to the selected item
 - `Ctrl + F12` See project structure
 - `Ctrl + Shift + V` See text fragment copied previously
 - __file:///home/shayon/Downloads/Programs/pycharm-community-2022.3.3/help/ReferenceCard.pdf__

### Documentations
 - [Creating a Reservation](https://help.guestyforhosts.com/hc/en-gb/articles/9350424977309-Creating-a-Reservation-in-the-Calendar#:~:text=Step%20by%20step%3A%201%20Sign%20in%20to%20your,details.%20Click%20herefor%20more%20information.%206%20Click%20Submit.)
 - [Cancel a reservation](https://help.guesty.com/hc/en-gb/articles/9359215565981-Canceling-a-Reservation#:~:text=Step%20by%20Step%3A%201%20Sign%20in%20to%20your,cancel.%20...%206%20Next%20to%20%22Summary%22%2C%20click%20Change.)
 - [Create a new task](https://help.guesty.com/hc/en-gb/articles/9370182470685-Video-Creating-a-Task), select, data and time, assigine a member, and select a supervisor, applies to a property and a reservation
 - [Docs](https://discord.com/developers/docs/intro)
 - [Discord py Examples](https://github.com/Rapptz/discord.py/tree/v2.2.2/examples)
 - [Quick start](https://discordpy.readthedocs.io/en/stable/quickstart.html)
 - Working with Discord: [Creating a Bot Account](https://discordpy.readthedocs.io/en/stable/intents.html) | [A Primer to Gateway Intents](https://discordpy.readthedocs.io/en/stable/intents.html)
 - [Logging](https://discordpy.readthedocs.io/en/stable/logging.html)
 - [Application commands](https://github.com/Rapptz/discord.py/blob/v2.2.2/examples/app_commands/basic.py) are native ways to interact with apps in the Discord client. There are 3 types of commands accessible in different interfaces: the chat input, a message's context menu (top-right menu or right-clicking in a message), and a user's context menu (right-clicking on a user).
 - [Guesty API](https://open-api-docs.guesty.com/)
 - [New reservation web hook](https://open-api-docs.guesty.com/docs/webhooks-reservations#new-reservation--booking-request-notification)
   ```
   curl --request POST \
     --url https://open-api.guesty.com/v1/webhooks \
     --header 'accept: application/json' \
     --header 'authorization: Bearer eyJraWQiOiJHNzFrRHI0VzZKTTBSREJUam1mU19WMlNhbVl2SkFrUzRqbGVQc2kzaFdrIiwiYWxnIjoiUlMyNTYifQ.eyJ2ZXIiOjEsImp0aSI6IkFULkVXNTdpX3prTkVFMzhvTUtPLWMtaHI5X25LT1NrWXlEMHVXcWhtZ21idDgiLCJpc3MiOiJodHRwczovL2xvZ2luLmd1ZXN0eS5jb20vb2F1dGgyL2F1czFwOHFyaDUzQ2NRVEk5NWQ3IiwiYXVkIjoiaHR0cHM6Ly9vcGVuLWFwaS5ndWVzdHkuY29tIiwiaWF0IjoxNjgwNTAwNDM0LCJleHAiOjE2ODA1ODY4MzQsImNpZCI6IjBvYTVzd25xaTR1S0x5THY5NWQ3Iiwic2NwIjpbIm9wZW4tYXBpIl0sInJlcXVlc3RlciI6IkVYVEVSTkFMIiwiYWNjb3VudElkIjoiNjI4ZTg0ZDBkMjlkMDkwMDM1MGY4NzNhIiwic3ViIjoiMG9hNXN3bnFpNHVLTHlMdjk1ZDciLCJ1c2VyUm9sZXMiOlt7InJvbGVJZCI6eyJwZXJtaXNzaW9ucyI6WyJhZG1pbiJdfX1dLCJyb2xlIjoidXNlciIsImlhbSI6InYzIiwiYWNjb3VudE5hbWUiOiJSYWlkZW4gRnJ1bmsiLCJuYW1lIjoiQ2xlYW5lciBDYWxjdWxhdGlvbnMifQ.d3q102Xyy4JXHj9K0Q28vnErCfMA8VlEm1MP3GatjWc7vPzqxOLGzFpmu461eE_kMnpcsgDLxhovjSQ5HFS6iRVQEaAmD5kDSTGJN8BnjsOrY66PbJ7lgFg_FSNwBNoWPFmdHHKhxFuaYJfRVfRMlkP68iAzMQO4YLaxRMgrRmzP0ck5EtNzLk_bUv-Zq6liyhfw9NFoqFR0_ek3Hvuz_h83HQ02f3r2-bUMiC0p9nbWAilgJsHgfZJfomgOOdjBsOpRdzEz-HqGPNrSuiGQbBKiUdSdFn-43ms16cCi8l0oVwxcNamWtQMs0j2EckZL1Jffbvk3YYUuGR0_91MWtw' \
     --header 'content-type: application/json'
   ```
 - Get custom field for cleaner pay [Get All Custom Fields](https://open-api-docs.guesty.com/reference/get_accounts-id-custom-fields), [Adding a Custom Field to Listings](https://help.guesty.com/hc/en-gb/articles/9371384820509-Adding-a-Custom-Field-to-Listings)

### Errors
 - ERROR-> (2023-08-02 15:06:09,321) 'NoneType' object has no attribute 'id' [/home/shayon/Claimbotv2/controllers/TaskUpdateController.py:238]
 - ERROR-> (2023-08-02 15:06:09,321) 'NoneType' object has no attribute 'lower' [/home/shayon/Claimbotv2/controllers/TaskUpdateController.py:400]
 - ERROR-> (2023-08-05 14:53:38,851) "{\"URL\": \"https://open-api.guesty.com/v1/listings?limit=100\", \"Status\": 401, \"Headers\": \"Headers({'date': 'Sat, 05 Aug 2023 14:53:38 GMT', 'content-length': '62', 'connection': 'keep-alive', 'ratelimit-limit': '15', 'ratelimit-remaining': '14', 'ratelimit-reset': '1', 'x-ratelimit-limit-second': '15', 'x-ratelimit-limit-minute': '120', 'x-ratelimit-limit-hour': '5000', 'x-ratelimit-remaining-hour': '4999', 'x-ratelimit-remaining-second': '14', 'x-ratelimit-remaining-minute': '119', 'x-content-type': 'nosniff', 'x-xss-protection': '1;mode=block', 'x-permitted-cross-domain-policies': 'none', 'x-frame-options': 'deny', 'strict-transport-security': 'max-age=31536000;includesubdomains'})\", \"Text\": \"{\\\"error\\\": {\\\"code\\\": \\\"UNAUTHORIZED\\\", \\\"message\\\": \\\"Unauthorized\\\"}}\"}" [/home/shayon/Claimbotv2/utils/guesty/GuestyListingRequests.py:44]
 - ERROR-> (2023-08-05 14:53:38,867) {"URL": "https://open-api.guesty.com/v1/tasks-open-api/tasks?columns=status+taskTitle+listing+reservation+scheduledFor+endTime+canStartAfter+mustFinishBefore+assignee+id&filters=%7B%7D&skip=0&limit=200", "Status": 401, "Headers": "Headers({'date': 'Sat, 05 Aug 2023 14:53:38 GMT', 'content-length': '62', 'connection': 'keep-alive', 'ratelimit-limit': '15', 'ratelimit-remaining': '13', 'x-ratelimit-remaining-hour': '4998', 'ratelimit-reset': '1', 'x-ratelimit-limit-second': '15', 'x-ratelimit-limit-minute': '120', 'x-ratelimit-limit-hour': '5000', 'x-ratelimit-remaining-minute': '118', 'x-ratelimit-remaining-second': '13', 'x-content-type': 'nosniff', 'x-xss-protection': '1;mode=block', 'x-permitted-cross-domain-policies': 'none', 'x-frame-options': 'deny', 'strict-transport-security': 'max-age=31536000;includesubdomains'})", "Text": "{\"error\": {\"code\": \"UNAUTHORIZED\", \"message\": \"Unauthorized\"}}"} [/home/shayon/Claimbotv2/utils/guesty/GuestyTaskRequests.py:91]
 - discord py temporary failure in name resolution
 - Error -> TaskUpdateController.py:230 NoneType object has not attributed lower (This could happen because it had been unauthorized)
 - NoneType has not attributed id
 - 404 not found - Unknown message CallbackOperations.py:399
 - 429 status code discord we are being rate limited in Discord py
 - Ignoring exception in view
 - https://copyprogramming.com/howto/expose-discord-bot-to-api-flask-fastapi
 - Getting this error when adding another task after completing previous task. `1 | buttons/TaskButtonsCallback.py:54 | 2023-04-30T02:21:54.673405 404 Not Found (error code: 10062): Unknown interaction`
 - CallbackOperations.py:697 -> Unknown message





### Run locally
 - Make sure to use updated guesty token in config/token.csv
 - Create and run mongodb database

   
### Deployment
 - Change branch to claimbotpy (For now)
 - Change values from dot env file
 - Change virtual environment
 - Change webhook urls
 - Setup mongodb
 - Run the project with systemd or pm2
 - Make sure the system runs after restarting the server


### Message to client
 - I see some issues with network and editing messages on discord too many times.
### Guesty
 - **Listing** -> In the context of Guesty, a property management platform for short-term rentals, a listing refers to a specific property or accommodation that is available for rent. When property owners or managers use Guesty, they can create listings for each property they want to rent out, and these listings contain all the relevant information about the property. A Guesty listing typically includes details such as the property's address, description, amenities, photographs, pricing, availability calendar, house rules, and any other pertinent information that potential guests might need to know. Property owners can customize their listings to showcase the unique features and appeal of their properties and attract potential guests. Listings on Guesty are typically published on various vacation rental platforms and online travel agencies (OTAs) to maximize exposure and reach a wider audience. The Guesty platform helps property managers streamline the listing creation process, synchronize availability and rates across different platforms, manage reservations, communicate with guests, and handle other aspects of short-term rental management.
 - **Reservation** -> In Guesty, a reservation refers to a booking made by a guest for a specific property or accommodation. When a guest chooses to book a property listed on Guesty, a reservation is created to record the details of the booking and manage the subsequent processes. When a reservation is made in Guesty, it typically includes information such as the guest's name and contact details, the dates of the stay, the number of guests, the total cost of the booking, and any specific requests or requirements the guest may have communicated. The reservation also links to the corresponding property listing and allows property managers to view and manage all the relevant information associated with the booking. Guesty provides tools and features to help property managers efficiently handle reservations. This includes features like automated messaging to communicate with guests, managing check-in and check-out processes, handling payments and refunds, synchronizing availability across different booking platforms, and generating reports to track reservations and revenue. By centralizing reservation management, Guesty enables property managers to streamline their operations, ensure a smooth guest experience, and effectively manage multiple bookings for their short-term rental properties.
 - **Task** -> In Guesty, a task refers to a specific action or assignment that needs to be completed within the property management system. Tasks are used to track and manage various activities related to the management of short-term rental properties.Tasks in Guesty can be created and assigned to specific team members or property managers to ensure that important actions are completed in a timely manner. These tasks can be related to guest communication, property maintenance, housekeeping, or any other operational aspect of managing rental properties. Some common examples of tasks in Guesty include: Guest Communication: Tasks can be created to respond to guest inquiries, handle booking requests, send check-in instructions, or follow up with guests before and after their stay. Housekeeping and Maintenance: Tasks can be assigned to schedule cleaning services, perform routine maintenance checks, address repairs, or handle any property-related issues. Check-In and Check-Out: Tasks can be created to ensure a smooth check-in and check-out process, including preparing the property, collecting keys, and conducting inspections. Reviews and Feedback: Tasks can be used to remind property managers to request reviews from guests, respond to guest reviews, and address any feedback or concerns. Administrative Tasks: Tasks can include activities like updating property information, managing pricing and availability, handling financial transactions, and generating reports.  Guesty's task management feature provides a centralized system for property managers to assign, track, and prioritize tasks, improving efficiency, communication, and ensuring that all necessary actions are completed in a timely manner.

### Systemctl/Systemd on linux
 - Run a python script with systemd [tutorial](https://www.youtube.com/watch?v=TXSPPT6_qTY)
 - Activate virtual environment `source virtual-env/bin/activate`
 - Check systemd is installed perfectly or not `systemd --version`
 - **Create a new file** for systemd `sudo nano /etc/systemd/system/claimbotpy.service`

   ```
   [Unit]
   Description=Python example service
   After=multi-user.target
   # StandardOutput=file:/home/shayon/Documents/Claimbotpy/print.log
   # StandardError=file:/home/shayon/Documents/Claimbotpy/print.log
   
   [Service]
   Type=simple
   Restart=always
   Environment="PATH=/home/shayon/Documents/Claimbotpy/virtual-env/bin"
   ExecStart=/home/shayon/Documents/Claimbotpy/virtual-env/bin/python3 /home/shayon/Documents/Claimbotpy/main.py
   # Without virtual environment use /usr/bin/python3
   # ExecStart=/usr/bin/python3 /home/shayon/Documents/Claimbotpy/main.py
   User=shayon
   
   [Install]
   WantedBy=multi-user.target
   ```

 - Make sure the script has executable permissions `chmod +x example.py`
 - Reload `sudo systemctl daemon-reload`
 - Create symlink `sudo systemctl enable claimbotpy.service`
 - Start service `sudo systemctl start claimbotpy.service`
 - Check the process `htop -p process_id`
 - Check all the services `sudo systemctl list-units --type service --all`
 - View the logs for the service `sudo journalctl -u claimbotpy.service`
 - **Remove or delete** a service
   ```
   sudo systemctl disable claimbotpy.service
   sudo rm -rf /etc/systemd/system/claimbotpy.service
   sudo systemctl daemon-reload
   ```
   
 

 - All you need to do is set the start time field. By this what did you mean? There is a time for starting a task, which was set from Guesty, and I am showing a button for starting the task on the date of that task. Furthermore, cleaner will complete the task.
 - Currently, I am validating for a task mush have listing. Should it be like this?

### Transfer files from server to loca computer
 - use curl and a website
   ```
   curl --location 'https://file.io?title=any.pdf' \
   --form 'file=@"/home/shayon/Documents/tin-certificate.pdf"'
   ```
 - make request, get key and use that key to download the file
