# -*- coding: utf-8 -*-

import json
import os
import requests
import uuid
import re

from prompts import MAIN_PROMPT 

CLOVA_API_HOST = os.getenv("HOST", "clovastudio.apigw.ntruss.com")
CLOVA_API_KEY = os.getenv("CLOVA_API_KEY", "your_api_key")
CLOVA_API_KEY_PRIMARY_VAL = os.getenv("CLOVA_API_KEY_PRIMARY_VAL", "your_primary_val")


def extract_first_answer(s):
    # Ensure input is a string
    if not isinstance(s, str):
        raise ValueError('Input should be a string.')
    
    # Check if "답변:" is in the string
    if "답변:" in s:
       # Split by "답변:"
        parts = s.split("답변:")
        # Remove leading and trailing whitespace
        answer_part = parts[1].strip()
    else:
        answer_part = s

    # If "질문:" is in the string, split by "질문:"
    if "질문:" in answer_part:
        first_answer = answer_part.split("질문:")[0].strip()
    else:
        first_answer = answer_part

    return first_answer



def clova_create(
    messages,
    request_id = str(uuid.uuid4()),
    maxTokens=512,
    temperature=0.5,
    topK=0,
    topP=0.8,
    repeatPenalty=5.0,
    start="",
    restart="",
    stopBefore=[],
    includeTokens=True,
    includeAiFilters=True,
    includeProbs=False,
):
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "X-NCP-CLOVASTUDIO-API-KEY": CLOVA_API_KEY,
        "X-NCP-APIGW-API-KEY": CLOVA_API_KEY_PRIMARY_VAL,
        "X-NCP-CLOVASTUDIO-REQUEST-ID": request_id,
    }

    text = ""
    for message in messages:
        if message["role"] == "user":
            text += "질문: " + str(message["content"]) + "\n"
        elif message["role"] == "assistant":
            text += "답변: " + str(message["content"]) + "\n"

    text = MAIN_PROMPT + text

    print(text)

    request_data = {
        "text": text,
        "maxTokens": maxTokens,
        "temperature": temperature,
        "topK": topK,
        "topP": topP,
        "repeatPenalty": repeatPenalty,
        "start": start,
        "restart": restart,
        "stopBefore": stopBefore,
        "includeTokens": includeTokens,
        "includeAiFilters": includeAiFilters,
        "includeProbs": includeProbs,
    }

    try:
        response = requests.post(
            f"https://{CLOVA_API_HOST}/testapp/v1/completions/LK-D2",
            headers=headers,
            json=request_data,
        )

        response.raise_for_status()
        result = response.json()
        if result["status"]["code"] == "20000":
            # If results in include text, remove the text part
            output = result["result"]["text"]
            if output.startswith(text):
                output = output[len(text) :]

            output = output.strip()
            if output.startswith("답변: "):
                output = output[len("답변: ") :]
        
            output = extract_first_answer(output)
            return {"role": "assistant", "content": output}
        else:
            return {"error": result["status"]["message"]}
    except Exception as e:
        print(f"Error occurred: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    request_id = str(uuid.uuid4())
    messages = [{"role": "user", "content": "오늘 날씨가 어때?"}]

    response_text = clova_create(messages)
    print(response_text)
