# Technical Specs
The application will be a single page application that will be built using Streamlit and will run on port 8081.

## Initialization 
1. Use GET localhost:5001/api/groups/<int:id>/words/raw to get a JSON response with japanese words and their english translations.
2. The words will be usedto generate a list of sentences in english.
3. An LLM will be used to construct a simple sentence containing one of the words.
4. An LLM will be user to transcribe the english sentence into japamese.

## Page States
Page states describes the behaviour of the single page application from the user's perspective.
The page will have 3 states:
- Initial State
- Practice State
- Results State

### Starting State
The page will be in the Starting State when the user first loads the page.
It will display a welcome message describing the application and a button called "Let's Practice Writing!".
When the button is pressed the application will generate a simple sentence in english using the Sentence Generator LLM.
The state will change to the Practice State

### Practice State
The user will be presented with the english sentence they need to write in japanese.
They will see an upload area and a grayed outbutton called "Check my writing".
The user should be able to drag and drop an image file of their writing attempt or click the upload area to upload an image file from their file system.
Once the image is uploaded the "Check my writing" button will be enabled.
When the button is pressed the application will use the Evaluation System to process the image uploaded by the user and produce a report on the user's performance.
The state will change to the Results State.

### Results State
The user will see the original english sentence and the transcribed japanese text of their writing attempt.
They will also see the Evaluation System assessment of their writing.
If the user successfully translates the sentence they will see a "Give me another sentence" button.
When the button is pressed the state will change to the Practice State with a new sentence.
If the user fails to translate the sentence they will see a "Try again" button.
When the button is pressed the state will change to the Practice State with the same sentence as before.
There will also be a "Finish" button regardless of the user's performance.
When the button is pressed the single page application will end.

## Sentence Generator

### Sentence Generator LLM
The sentence generator LLM will use the following LLM: google/gemini-1.5-flash

### Sentence Generator Prompt
```text
Generate a simple sentence that contains the following word: {{word}}
The grammar of the sentence should be scoped to JLPTN5 grammar level.
You can use the following vocabulary to construct a simple sentence:
- simple objects eg. book, car, house
- simple verbs eg. read, drive, eat
- simple adjectives eg. red, big, tasty
- simple adverbs eg. quickly, very, always
```

## Evaluation System
The evaluation system will perform the following steps:
- transcribe the user's image into japanese using MangaOCR
- use Translation Sub-System to procduce a literal translation of the transcribed japanese text
- use Grading Sub-System to compare, grade and evaluate the user's translation with the original sentence

### MangaOCR
MangaOCR is a pre-trained model that can be used to transcribe images of japanese text into japanese text.
It is a fine-tuned version of the OCR-D/OCR-D-table model.

### Translation Sub-System
#### Translation LLM
The Translation LLM will use the following LLM: google/gemini-1.5-flash

#### Translation Prompt
```text
Translate the following text from japanese to english:
{{text}}
```

### Grading Sub-System
Will evaluate the user's translation and produce a score and evaluation:
- a letter score using the japanase S Rank to score the user's translation
- an evaluation of the user's translation with suggestions for improvement
#### Grading LLM
The Grading LLM will use the following LLM: google/gemini-1.5-flash

#### Grading Prompt
```text
Grade the following piece of text based on the reference text:
{{text}}. Provide a letter score using the japanase S Rank to score the user's translation.
Provide an evaluation of the user's translation with suggestions for improvement.
```

## Google Gemini API
The google gemini API key is set as an environment variable: GOOGLE_API_KEY