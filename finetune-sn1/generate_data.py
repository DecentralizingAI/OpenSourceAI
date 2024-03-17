import wandb
import pandas as pd
import plotly.express as px
import json
import os

file_dir = os.path.join(os.path.dirname(__file__), 'data')



class SubtensorDataGeneration:
	def __init__(self, projectpath):
		self.api = wandb.Api()
		self.projectpath = projectpath
	
	def get_system_prompt(self, challenge):
		pass

	def supplementFile(self, filename):
		with open(os.path.join(file_dir, filename), 'r', encoding='utf-8') as f:
			dataset = [json.loads(line) for line in f]

	
	def getRawData(self):
		training_tuples = []
		validation_tuples = []

		challenge = set()
		challenge.add('')
		reference = set()
		reference.add('')

		runs = self.get_aggregate_run(self.projectpath)
		for i, run in enumerate(runs):
			df = pd.DataFrame(list(run.scan_history()))
			try: 
				df1 = df[['challenge', 'reference']]
				df1_tuples = list(df1.itertuples(index=False, name=None))
			
				for j, t in enumerate(df1_tuples):
					if t[0] in challenge and t[1] in reference:
						continue
					if j % 20 != 1:
						training_tuples.append(t)
					else:
						validation_tuples.append(t)

					challenge.add(t[0])
					reference.add(t[1])
				all_tuples = len(training_tuples) + len(validation_tuples)
				print(f"run: {i}/{len(runs)}: {run}--> {len(df1_tuples)}/{all_tuples}")
			except Exception as e:
				print(e)
				print(df.head())
				print(f"run: {i}/{len(runs)}: {run}--> FAILED...")

			if i % 15 == 0:
				print("snapshottting")
				self.dump(training_tuples, f"opentensor-train-{i}")
				self.dump(validation_tuples, f"opentensor-validation-{i}")
		self.dump(training_tuples, 'opentensor-train')
		self.dump(validation_tuples, 'opentensor-validation')
	
	def dump(self, tuples, filename):
		filepath = os.path.join(file_dir, filename + '.jsonl')
		print(filepath)
		systemPrompt = 'Respond neutrally to the query'
		ai_input = [{'messages': [{'role': 'system', 'content': systemPrompt}, {'role': 'user', 'content': t[0]}, {'role': 'assistant', 'content': t[1]}]} for t in tuples]
		with open(filepath, 'w') as f:
			for item in ai_input:
				json.dump(item, f)
				f.write('\n')


	def get_single_run(self, path):
		return self.api.run(path)
	
	def get_aggregate_run(self, path):
		runs = self.api.runs(path)
		return runs


if __name__ == '__main__':
	project_path = 'opentensor-dev/alpha-validators' 
	s = SubtensorDataGeneration(project_path)
	s.run()

