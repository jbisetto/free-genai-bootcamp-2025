# Prompt for Extracting JLPT N5 Listening Questions as JSON

Please analyze the following JLPT N5 listening practice transcript and extract ONLY questions of Type 2 (Conversation Comprehension Questions) and Type 4 (Listening Comprehension Without Visual Aids). Format your output as a JSON object.

## JLPT N5 Listening Question Type Definitions:

- **Type 1 (Picture/Option Selection)**: Questions where you listen to a conversation and select the best answer from visual options (often pictures). These usually involve situations like "Where is the man going?" with images to choose from. IGNORE THESE.

- **Type 2 (Conversation Comprehension)**: Questions where you first hear a question, then listen to a conversation, and select the best answer based on understanding specific details from the dialogue. Examples include questions about birthdays, meeting locations, food choices, etc. EXTRACT THESE.

- **Type 3 (Situational Response)**: Questions that show a situation and ask for the appropriate phrase to use (e.g., "You're going to sleep. What do you say to others?"). These test knowledge of common Japanese phrases in context. IGNORE THESE.

- **Type 4 (Pure Listening Comprehension)**: Questions without any visual aids where you listen to a question and select the appropriate response. These rely solely on listening comprehension without contextual clues. EXTRACT THESE.

## Important Notes:
- **Ignore video intro and outro sections** and any practice examples
- **Only extract questions that match Type 2 or Type 4 criteria**
- Type 2 questions often appear in sections labeled "問題2" in the transcript
- Type 4 questions often appear in sections labeled "問題4" in the transcript

## Output Format:
Your response should be a valid JSON object that is valid for the following json schema:

{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "questions": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "integer"
          }
          "question_type": {
            "type": "integer",
            "enum": [1, 2, 3, 4]
          },
          "introduction": {
            "type": "string"
          },
          "conversation": {
            "type": "string"
          },
          "question": {
            "type": "string"
          }
        },
        "required": ["id", "question_type", "introduction", "conversation", "question"]
      }
    }
  },
  "required": ["questions"]
}


Here is an example: 

{
  "questions": [
    {
      "id": 1, // Unique ID for the question
      "type": 2,
      "introduction": "男の人と女の人が話しています。", // Ensure this does not include the question itself.
      "conversation": "男の人: 綺麗な花ですね。女の人: ええ、誕生日に友達にもらいました。男の人: へえ、いつですか。女の人: 昨日です。11日です。男の人: そうですか。女の人: え、じゃあ1が4つ並びますね。男の人: ええ、そうですよ。",
      "question": "女の人の誕生日はいつですか。"
    },
    { 
      "id": 2, // Unique ID for the question
      "type": 4,
      "introduction": "パーティーで男の人と女の人が話しています。", // Ensure this does not include the question itself.
      "conversation": "あ山田さん飲み物がありませんね何を飲みますかビールとワインあとジュースとお茶がありますけどあコーヒーはありませんかうーんコーヒーはありませんねそうですか温かいものはありませんかああ温かいお茶はできますよじゃそれをお願いします",
      "question": "女の人は何を飲みますか。"
    }
  ]
}

Notes:
- Preserve all Japanese text as written in the original
- Include speaker indicators (e.g., 男の人:, 女の人:)
- For questions with missing components, use the string "[Not provided in transcript]"
- Do not include a question in the introduction text
- Ensure the JSON is properly formatted and valid
- if a type 4 question sentence requires an image or visual to answer then ignore the question


Please process the entire transcript following this format, focusing ONLY on extracting questions of Type 2 and Type 4.

Only respond with the given format and nothing else.
Do not pretty print the response.