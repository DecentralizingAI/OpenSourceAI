# Finetune your SN-1 Model

Scripts are provided here to generate training data for your SN-1 mode.
Replace base model in all scripts to the model you are running. OpenAI models are used as the default example. 


The following pulls prior validator-generated examples from hugging face, 
and generates examples containing {system, user, assistant} roles + desired output.
```
python3 generate_data.py
```

You can try using this data to fine-tune an openai model with:
```
python3 finetune.py
```
