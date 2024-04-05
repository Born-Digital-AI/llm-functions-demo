# llm-functions-demo

## save_conversations

Talk via API (when app is running on http://0.0.0.0:8824):
```
python talk.py [CID] text
python talk.py 301 "Dobrý den"
```

Simulate conversation (when app is running on http://0.0.0.0:8824):

```
python simulate.py [CID]
```

Conversations are stored in files named messages_{CID}.json.

Files are further processed and uploaded in the notebook ft_chatgpt_baker.ipynb to be used for fine-tuning.

