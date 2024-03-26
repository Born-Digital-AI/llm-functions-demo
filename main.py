import logging
import json
import copy
import datetime
import os


from fastapi import FastAPI, Query
from openai import OpenAI
import openai 
import urllib.parse

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
    {"role": "system", "content": f"You are a Bakery Salesman. Help user buy bakery goods. Introduce yourself and ask user how you can help. Komunikuj v češtině. Prodáváš různé chleby, rohlíky, koláče, vánočky atd."} #" Vždy uživateli nabízej varianty výrobků. Máš k dispozici tyto produkty: {available_items}"},
]

IN_MEM_DATA = {}


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
def get_conversation_user(CID: str, text: str = Query(None)):

    messages, cart = get_data(CID)
    text = urllib.parse.unquote(text)

    def get_cart_items() -> str:
        """Returns what is in the cart"""
        logging.info("Getting the cart content")
        return str(cart)

    def checkout() -> str:
        """Confirms order from a client"""
        logging.info("Confirming the order")
        return "Done"
    
    def give_options(item_name: str) -> str:
        """Offer options for what the customer wants"""
        logging.info(f"Offering products similar to {item_name}.")
        items = str([item.page_content for item in available_items_db.similarity_search(item_name)])
        logging.info(f"Found options for a query {items}")
        return f"We can offer these options: {items}. If some oh these items are not {item_name}, don't mention them. If none of these items is {item_name}, say that you are sorry and ask for something else."    

    def add_item_to_cart(item_name: str, count: int) -> str:
        """Add item to a cart or offer alternatives"""
        logging.info(f"Trying to add item {item_name} with count {count} to a cart.")
        if item_name in available_items:
            cart.append({"item_name": item_name, "count": count})
            logging.info("Item added to the cart")
            return "Item added to the cart"
        else:
            items = str([item.page_content for item in available_items_db.similarity_search(item_name)])
            logging.info(f"Found options for a query {items}")
            return f"Wrong item name. We can offer these similar items: {items}. If these are not similar to {item_name}, don't offer them. If none of these items is similar to {item_name}, say that you are sorry and ask for something else."    

    available_functions = {
        "add_item_to_cart": add_item_to_cart,
        "checkout": checkout,
        "get_cart_items": get_cart_items,
        "give_options": give_options,
    }  

    counter = 0
    done = False

    if text:
        messages.append({"role": "user", "content": text})

    while counter < 5:
        counter += 1 

        logging.info(f"\n Input messages: {messages}")

        
        messages_for_chat = copy.deepcopy(messages)
        for msg in messages_for_chat:
            if "arguments" in msg:
                del msg["arguments"]
                
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",#3"gpt-4-turbo-preview",#"ft:gpt-3.5-turbo-0125:born-digital-s-r-o:baker:96bl5pR7"
            messages= messages_for_chat,
            tools=[get_openai_func_def(get_cart_items), get_openai_func_def(add_item_to_cart), get_openai_func_def(checkout), get_openai_func_def(give_options)],
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
                        "arguments": function_args
                    }
                )
                if function_name == "checkout":
                    done = True
        else:
            IN_MEM_DATA[CID] = {"cart": cart, "messages": copy.deepcopy(messages)}
            logging.info(f"\n GPT message: {response_message.content}")
            timestamp = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
            dump_filename = f"messages_{CID}.json" 
            for i in range(len(messages)):
                if isinstance(messages[i], openai.types.chat.chat_completion_message.ChatCompletionMessage):
                    messages[i] = {"role" : "assistant", "content" : messages[i].content}
                if "tool_call_id" in messages[i]:
                    messages[i] = {"role" : "function", "name" : messages[i]["name"], "arguments" : messages[i]["arguments"], "content" : messages[i]["content"]}
                if messages[i]["role"] == "system":
                    messages[i]["content"] = "You are a Bakery Salesman. Help user buy bakery goods. Introduce yourself and ask user how you can help. Komunikuj v češtině."
                if messages[i]["role"] == "function": #trim function reponses after basic info
                    messages[i]["content"] = messages[i]["content"].split("If")[0]
                    
            if os.path.isfile(dump_filename):
                with open(dump_filename, "r", encoding = "UTF-8") as f:
                    dump = json.load(f)
                dump["messages"] = [msg for msg in messages if msg["content"] is not None]
            else:
                dump = {"messages": [msg for msg in messages if msg["content"] is not None], \
                        "functions": [get_openai_func_def(f)["function"] for key, f in available_functions.items()]}

            with open(dump_filename, "w", encoding = "UTF-8") as f:
                json.dump(dump, f, ensure_ascii=False, indent=4)  
 
            return {"text": response_message.content, "done": done}
    
@app.get("/conversation/simulate/{CID}")
def simulate_conversation(CID: str):   
    def bye() -> str:
        """Says goodbye when the purchase is finished and the seller asks no more questions"""
        logging.info("Finalizing purchase")
        return "Bye"
    
    client_user = OpenAI(timeout=10.0, max_retries=2)
    messages = []
    messages.append({"role": "system", "content": "Jsi zákazník obchodu s pečivem a chceš si koupit pečivo, například koláč, buchtu, vánočku, dort, bábovku, veku, chléb, nebo rohlík. Buď stručný."})#" Když se prodejce už na nic neptá, ukonči hovor slovy 'Na shledanou'"})
    messages.append({"role": "assistant", "content": "Dobrý den"})
    
    i = 0
    done = False
    while i < 10 and not done:
        sim_user = get_conversation_user(CID, messages[-1]["content"])
        messages.append({"role": "user", "content": sim_user["text"]})
        done = sim_user["done"]
  #      logging.info(f"\n User: {sim_user['text']}")
        response = client_user.chat.completions.create(
            model="gpt-3.5-turbo-0125",#"gpt-4-turbo-preview",#
            messages= messages)
           # tools=[get_openai_func_def(bye)])
        messages.append({"role": "assistant", "content": response.choices[0].message.content})
        i += 1
        
        if done: #or "shledanou" in response.choices[0].message.content:
       #     print(response.choices[0].message.content, flush=True)
       #     print(done,  flush=True)
       #     print("shledanou" in response.choices[0].message.content)
            return {"status" : f"Checkout completed after {i} turns."}
        
    
    return {"status" : "Interrupted after 10 turns."}

