import logging
import json
import copy
import requests

from fastapi import FastAPI, Query
from openai import OpenAI

logging.basicConfig(
    format='%(asctime)s.%(msecs)-03d %(name)s.%(funcName)s:%(lineno)-4s %(levelname)-8s %(message)s',
    level="INFO",
    datefmt='%Y/%m/%d-%H:%M:%S',
    force=True
)

from vector_db import available_items, available_items_db
from utils import get_openai_func_def

app = FastAPI()
client = OpenAI(timeout=10.0, max_retries=2)

DEFAULT_MSG = [
    {"role": "system", "content": "You are a Bakery Salesman John. Help user buy bakery goods. Briefly introduce yourself and ask user how you can help. Komunikuj v češtině."},
]

IN_MEM_DATA = {}

def llm_command(query: str, options: str) -> str:   
    messages = [
        {
            "role": "system",
            "content": "The user selects goods and has 3 options to choose from. If the choice is unambiguous, return only one value. If the choice is ambiguous, return a list of products that are considered. If nothing matches, do not return anything. Respond in JSON format in the parameter item_list (list)."
        },
        {
            "role": "user",
            "content": f"User query: {query}; available options: {options}"
        }
    ]
    try:
        # Requesting the AI to generate a Python function
        response = client.chat.completions.create(
            model="gpt-4o-2024-05-13",
            messages=messages,
            max_tokens=2000,
            response_format={ "type": "json_object" }
        )
        returned_text = response.choices[0].message.content
        logging.info(f"LLM answer: {returned_text}")
        return returned_text
    except Exception as e:
        raise ValueError(f"An error occurred while generating the function: {str(e)}")


def get_data(CID):
    global IN_MEM_DATA
    try:
        data = IN_MEM_DATA[CID]
        logging.info("Continue existing conversation")
        return data["messages"], data["cart"]
    except KeyError:
        logging.info("Creating new conversation")
        return copy.deepcopy(DEFAULT_MSG), []


@app.get("/conversation/{CID}/user/")
async def get_conversation_user(CID: str, text: str = Query(None)):

    messages, cart = get_data(CID)

    def get_cart_items() -> str:
        """Returns what is in the cart"""
        logging.info("Getting the cart content")
        return str(cart)

    def checkout() -> str:
        """Confirms order and sents confirmation sms with a cart content to user phone number"""
        logging.info("Confirming the order")
        return "Done"

    def add_item_to_cart(item_name: str, count: int) -> str:
        """Add item to a cart"""
        logging.info(f"Trying to add item {item_name} with count {count} to a cart.")
        if item_name in available_items:
            cart.append({"item_name": item_name, "count": count})
            logging.info("Item added to the cart")
            return f"Item '{item_name}' with count {count} added to the cart"
        else:
            items = str([item.page_content for item in available_items_db.similarity_search(item_name)][:3])
            result = json.loads(llm_command(item_name, items))["item_list"]
            if len(result) == 1:
                cart.append({"item_name": result[0], "count": count})
                logging.info("LLM filter. Item added to the cart")
                return f"Item '{result[0]}' with count {count} added to the cart"
            elif len(result) == 0:
                return f"This nor similar items are not in the stock."    
            else:
                logging.info(f"Found options for a query {items}")
                return f"Wrong item name.\n Offer user these possible options: {items}"    

    available_functions = {
        "add_item_to_cart": add_item_to_cart,
        "checkout": checkout,
        "get_cart_items": get_cart_items
    }  

    counter = 0

    if text:
        messages.append({"role": "user", "content": text})

    while counter < 5:
        counter += 1 

        logging.info(f"\n Input messages: {messages}")

        response = client.chat.completions.create(
            model="gpt-4o-2024-05-13",
            messages=messages,
            tools=[get_openai_func_def(get_cart_items), get_openai_func_def(add_item_to_cart), get_openai_func_def(checkout)],
        )
        response_message = response.choices[0].message
        logging.info(f"\n Response messages: {response_message}")
        
        messages.append(response_message)  
        tool_calls = response_message.tool_calls

        if tool_calls:
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(**function_args)
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                )
        else:
            IN_MEM_DATA[CID] = {"cart": cart, "messages": messages}
            logging.info(f"\n GPT message: {response_message.content}")
            return {"text": response_message.content}
        