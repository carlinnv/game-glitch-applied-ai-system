# 💭 Reflection: Game Glitch Investigator

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

## 1. What was broken when you started?

- What did the game look like the first time you ran it?
  - The game had the instructions at the top and an input box for the guess, with two buttons for submitting a guess and starting a new game. I noticed that it said "Attempts left: 7".
- List at least two concrete bugs you noticed at the start  
  (for example: "the secret number kept changing" or "the hints were backwards").
  - Bug 1: I noticed that the hints were reversed. For example, if the secret number was 50 and I guessed 75, it would say "Guess Higher!" 
  - Bug 2: The game begins with 7 attempts instead of 8. This means that the user did not get as many chances to guess as they should have upon opening the app.

---

## 2. How did you use AI as a teammate?

- Which AI tools did you use on this project (for example: ChatGPT, Gemini, Copilot)?
  - I primarily used Copilot agent mode in VSCode. I also experimented with Claude. 
- Give one example of an AI suggestion that was correct (including what the AI suggested and how you verified the result).
  - One thing AI suggested was changing the attempts counter when the app is first initialized. This was in order to fix the issue of the game starting with 1 attempt, hence giving the player 7 attempts to guess the number when they should have 8. I verified the results by reading through the code that AI suggested, then accepting it, then testing it in the real app. 
- Give one example of an AI suggestion that was incorrect or misleading (including what the AI suggested and how you verified the result).
  - Though not necessarily "wrong", CoPilot attempted to change my code during the refactoring process. I noticed this as I was reading through the code suggestions between both files. From here, I directed the AI to keep the code the same. 
---

## 3. Debugging and testing your fixes

- How did you decide whether a bug was really fixed?
  - I used pytest and opening the app to tell if a bug was really fixed. Using pytest, I tested that the guessing logic gave the appropriate responses to guesses that were too high or low. Then, I opened the app to check if the user actually gets 8 attempts rather than 7 to guess the number on their first try. 
- Describe at least one test you ran (manual or using pytest) and what it showed you about your code.
  - I directed Copilot to create a function in the test_game_logic file for me. This was the function that I used with pytest to check the three possible outcomes (win, guess too high, guess too low). 
- Did AI help you design or understand any tests? How?
  - Yes, AI helped me design and understand the tests in the test_game_logic.py. Copilot helped me design a function to test the guessing logic. It also helped me understand why the original tests failed. 

---

## 4. What did you learn about Streamlit and state?

- In your own words, explain why the secret number kept changing in the original app.
  - The secret number appeared to change in the original app because when it was being compared to the guess, it was sometimes converted into a string. This made it so that the app did not correctly execute numerical comparison between the guess and the secret number. 
- How would you explain Streamlit "reruns" and session state to a friend who has never used Streamlit?
  - I would tell them that every time Streamlit "reruns", it re-executes the Python code in full. This is why we need session states to keep track of persistent data. Using session states, we can keep track of variables between reruns that do not get erased. 
- What change did you make that finally gave the game a stable secret number?
  - I made it so that the secret number is not converted to a string. This way, numerical comparison works the way it should. 

---

## 5. Looking ahead: your developer habits

- What is one habit or strategy from this project that you want to reuse in future labs or projects? This could be a testing habit, a prompting strategy, or a way you used Git.
  - One habit I want to take away from this project is proper prompting strategies. First, I want to continue using tags like #codebase and #file. I think that using these tags to direct Copilot made my directions a lot clearer and got me better results. It also really helped me to create new chats for each issue I wanted to fix so I could go back and review the changes that were made.
- What is one thing you would do differently next time you work with AI on a coding task?
  - Next time, I would document my code a little better with #FIXME so that Copilot knows the specific spots to change. I think the #FIX comments were also helpful for me to review what was changed and how I changed it. 
- In one or two sentences, describe how this project changed the way you think about AI generated code.
  - This project made me realize that I can actually optimize the way I use AI in coding. For example, I can use different models of Copilot (Ask, Agent) depending on what I want to do. 
