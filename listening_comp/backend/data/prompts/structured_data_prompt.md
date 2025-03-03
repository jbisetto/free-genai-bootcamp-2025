# JLPT N5 Listening Transcript Extraction Prompt
You will be given a transcript of a JLPT N5 listening test. 

Here is a breakdown of the questioning formats:
# Main Question Types in the Transcript:
## 1. Picture/Option Selection Based on Dialogue (問題1)
- Format: Listen to a conversation, then select the best answer from options 1-4
- Example: "デパートで男の人と店の人が話しています。男の人はどこへ行きますか。" (At a department store, a man and store staff are talking. Where is the man going?)
- This section likely involves selecting from visual options/pictures

## 2. Conversation Comprehension Questions (問題2)
- Format: First hear a question, then listen to a conversation, and select from options 1-4
- Example: "女の人の誕生日はいつですか。" (When is the woman's birthday?)
- Tests understanding of specific details from conversations

## 3. Situational Response Questions (問題3)
- Format: Look at an image showing a situation, then select the appropriate response
- Example: "寝ます。他の人に何と言いますか。" (You're going to sleep. What do you say to others?)
- Tests knowledge of common Japanese phrases in context

## 4. Listening Comprehension Without Visual Aids (問題4)
- Format: No images provided, listen to a question and select the appropriate response
- Example: "あの方はどなたですか。" (Who is that person?)
- Tests pure listening comprehension without contextual clues

## Question Structure Patterns:
1. Location questions: "どこへ行きますか" (Where is someone going?)
1. Time questions: "何時頃にもう1度来ますか" (Around what time will someone come again?)
1. Selection questions: "何を飲みますか/食べますか" (What will someone drink/eat?)
1. Quantity questions: "先生は何人来ますか" (How many teachers will come?)
1. Action questions: "椅子をどう並べますか" (How will the chairs be arranged?)
1. Date questions: "いつですか" (When is it?)

The test follows a progressive difficulty pattern, starting with simpler picture-based questions and moving toward more complex comprehension questions that rely solely on listening without visual aids.
Each section has clear instructions about how to approach the questions, and practice examples are provided before the actual test questions begin.

# Task
Your task is to analyze the following JLPT N5 listening practice transcript using the provided breakdown and extract the following for each question that is a converstaion comprehension question or a listening comprehension without visual aids question.

For each converstaion comprehension question or listening comprehension without visual aids question extract the following information:
1. Introduction (setting the context/scene)
2. Conversation or monologue content
3. Question being asked

## Important Notes:
- **Ignore video intro and outro sections** - Do not include general video introductions, instructions about the JLPT format, or closing remarks/summaries
- Only extract the actual test content (questions, conversations, and their context)
- Only extract question formats 2 and 4 since they do not include an image or visual component
- Ignore questions in formats 1 and 3 since they could include an image or visual component

For each question in the transcript, format your response as:

```
## Question [Number] [Question type]

**Introduction:** [Text that sets up the situation or introduces the speakers]

**Conversation/Monologue:** [The full dialogue or monologue text]

**Question:** [The specific question being asked about the conversation]
```

Notes:
- Preserve all Japanese text as written in the original
- Include translations in parentheses if available in the source material
- Maintain speaker indicators (e.g., 男の人:, 女の人:)
- If the introduction, conversation, or question components are missing from the original, indicate with [Not provided in transcript]

Example output format:

```
## Question 1 Converstaion Comprehension

**Introduction:** これから、会話とそれについての質問を聞きます。(You will hear a conversation and a question about it.)

**Conversation:**
男の人: すみません、郵便局はどこですか。
女の人: あの、交差点を右に曲がって、まっすぐ行くと左側にあります。

**Question:** 郵便局はどこにありますか。
```

Please process the entire transcript following this format, focusing only on the actual test content.