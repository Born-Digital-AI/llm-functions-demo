import inspect
import json

def get_openai_func_def(func):
    signature = inspect.signature(func)
    arguments = signature.parameters
    
    if arguments:
        parameters = {
              "type": "object",
              "properties": {k: {"type": "string"} for k, v in dict(arguments).items()},
              "required": [name for name, param in inspect.signature(func).parameters.items() if param.default == inspect.Parameter.empty]
                }
    else:
        parameters = {
              "type": "object",
              "properties": {},
              "required": []
              }

  #      parameters = None
        
    func_def = {
            "type": "function",
              "function": {
                "name": func.__name__,
                "description": func.__doc__,
                "parameters": parameters
              }
            }
    return func_def