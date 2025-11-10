# Reflection: Multi-agent Travel Planning Application
### Course: INFO 5940 011
### Assignment 2 
### Author: *Yuqing Sun* 
### netID: *ys2434* 

## What I Learned from Implementing a Multi-Agent Workflow
Building a multi-agent travel planning application deepened my understanding of how different AI agents can collaborate to solve a complex problem in a structured, sequential manner. The **Planner Agent** and **Reviewer Agent** had distinct yet interdependent roles, demonstrating the importance of clear division of responsibilities in agent design. Through this process, I learned how to design **instruction prompts** that balance autonomy with control — making the Planner creative but bounded by budget and itinerary constraints, and the Reviewer analytical and fact-based, supported by a live search tool. This workflow clarified how agents can **pass context-rich data** to each other, and how **iterative refinement** leads to more realistic and accurate outputs.

## Challenges Faced and How I Addressed Them
The biggest challenge was **authentication and environment configuration** for the  APIs. Initially, I encountered persistent `401` errors due to mismatched environment variable names (`OPENAI_API_KEY` vs. `API_KEY`). Solving this required deeper debugging of environment loading order and consistent normalization of variable names before agent initialization. Another challenge was ensuring the **Reviewer Agent correctly invoked the internet search tool** — fixing this involved explicitly linking the `internet_search` function to the Reviewer’s tool list. I also refined **prompt formatting** to ensure Markdown-structured outputs that could be rendered clearly in Streamlit.

## Creative Ideas and Design Choices
When designing the two agents, I wanted them to feel like a real team rather than just two scripts passing text back and forth. I imagined the **Planner Agent** as a friendly travel expert who enjoys creating detailed itineraries but still respects time, budget, and pacing limits. The **Reviewer Agent**, on the other hand, plays the role of a careful checker — the type of person who checks ticket prices, opening hours, and train schedules to make sure everything actually works in real life.  
I also focused on making their collaboration easy for users to follow. By having the Planner write in a structured Markdown format and the Reviewer produce a clear “Delta List” of suggested fixes, the whole workflow became more readable and transparent. You can literally see how the plan gets refined step by step. My goal was to make the interaction feel conversational and human — like planning a trip with a creative friend and a cautious one reviewing every detail before you book.

## External Tools and GenAI Usage
I used **ChatGPT (GPT-5)** to refine prompt instructions, debug authentication issues, and polish the reflection narrative. GenAI assistance was limited to clarifying environment setup and improving prompt clarity — all core code and logic were implemented manually.

