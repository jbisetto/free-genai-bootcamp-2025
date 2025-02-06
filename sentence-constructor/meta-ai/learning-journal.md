# Learning Journal 
## Italian Sentence Constructor

## Business Goal: 
A chat agent that acts as a teaching assistant to guide students from translating a target English sentence into Italian. The teaching assistant is not there to provide the direct answer, only guidance.


## Technical Uncertainty
1. How well can an AI-Powered Assistant perform a very broad task?
2. Would a very broad task be better performed by dividing it into subtasks with specialized agents?
3. Does using an AI-Powered Assistant make for a good place to rapidly prototype agents?
4. How could we take the agent we built in an AI-Powered Assistant and reimplement it into a stack that allows for direct integration into our platform?	
5. How much do we have to rework our prompt documents from one AI-Powered Assistant to another?
6. What prompting techniques can we naturally discover working in the confines of an AI-Powered Assistant?
7. Are there any interesting innovations unique to specific AI-Powered Assistants for our business goal?
8. What were we able to achieve based on our AI-Powered Assistant choice and our hardware, or budget limitations?

# Prompt document
## v001
Initial creation
### Response Evaluation
- just provided the answer
- not a great breakdown of trascribing
### Learning
- forgot all my grammar and vocab learned in highschool, using AI to bridge that gap, i.e. what are particles
## v002
### Changes
- do not give answer
- provide vocabulary table
- don't include particles
- don't define words using conjugation or tenses use dictionary form
### Response Evaluation
- table is there, did have a row for 'did' explaining that we will need to figure out the correct verb conjugation
- that's basically a particle...

## v003
#1 v003 try to get it to not mention or hint about particles and provide a sentence structure
### Response Evaluation
- still giving us tense hints
- still giving us conjugation hints
## v004
#1 v004 added Language Level: Beginner, CEFR A1
### Response Evaluation
- lost the ascii art sentence structure
## v005
#1 v005 add restriction to not provide answer if prompted and gave an example of how to show sentence structure
### Response Evaluation
- sentence sturcture is back
- including plural words in the table and hints

## v006
#1 v006 add restriction to only provide the singular of words in the vocabulary table
### Response Evaluation
- still providing tense and preposition hints 

## v007
#1 v007 add tense and preposition restrictions
### Response Evaluation
- still including hints about plural words
## v008
#1 v008 add pluralization restriction
### Response Evaluation
- hints are better, focusing on nouns and verbs
- listing adverbs but not their italian tanslation