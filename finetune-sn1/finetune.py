# This POC finetunes model-data on openai model via API
# TODO: scripts to fine-tune open-source models.

import openai
from openai import OpenAI
import sys

openai.api_key = ""

training_filename = sys.argv[1]
validation_filename = sys.argv[2]

# Create an OpenAI client
client = OpenAI()
training_file = client.files.create(
  file=open(training_filename, "rb"),
  purpose="fine-tune"
)
validation_file = client.files.create(
  file=open(validation_filename, "rb"),
  purpose="fine-tune"
)
print(training_file)
print(validation_file)

output = client.fine_tuning.jobs.create(
  training_file=training_file.id, 
  validation_file=validation_file.id,
  model="gpt-3.5-turbo-0125"
)
print(output)