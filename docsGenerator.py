import inspect
import os
import sys
from glob import glob

from project.data import VERSION


class DocGenerator() :

	def __init__(self) :
		self.start()

	def start(self) :
		sys.path.append(os.path.dirname(os.path.abspath(__file__)))
		count = 9
		for file in glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "modules", "*.py")) :
			self.load_file(file, nav=count)
			count += 1


	def document_header(self, module_name: str) :


		return f"""
---
layout: default
title: Whitelisting
nav_order: 8
---		
		
<h1>{module_name}</h1>
<h6>version: {VERSION}</h6>
<h6>Documentation automatically generated from docstrings.</h6>


"""
	def command_line(self, docfile, function, tclass):
		if function.startswith("_") or function.startswith('cog') or function.startswith('cog') :
			return

		func_obj = getattr(tclass, function)

		docstring = ""
		# Check if it's a decorated command with a callback
		if hasattr(func_obj, 'callback') :
			docstring = inspect.getdoc(func_obj.callback)
		# Check if it's a callable function
		elif callable(func_obj) :
			docstring = inspect.getdoc(func_obj)

		if not docstring :
			docstring = "Missing Documentation"
		param_string = ""
		try :
			sig = inspect.signature(func_obj)
			# Filter out 'self' and 'interaction' from the parameters
			params = [p for p in sig.parameters if p not in ('self', 'interaction')]
			if params :
				# Format parameters like: <param1> <param2>
				param_string = " " + " ".join([f"<{p}:>" for p in params])
		except (ValueError, TypeError) :
			# This can happen for objects that are not inspectable
			pass



		docfile.write(f"### `{function}`\n\n"
		              f"**Usage:** `/{function}{param_string}`\n\n"
		              f"> {docstring}\n\n"
		              f"---\n\n")


	def load_file(self, file, nav = 9) :
		name = os.path.splitext(os.path.basename(file))[0]
		document = f"docs/{name}.md"
		if name == "__init__" :
			return
		# create the document
		if os.path.exists(document) :
			os.remove(document)

		with open(document, "w", encoding="utf-8") as docfile :
			docfile.write(self.document_header(name))

			# add package prefix to name
			module_name = f"modules.{name}"
			module = __import__(module_name, fromlist=[name])
			for member in dir(module) :
				# do something with the member named ``member``
				if member.startswith("_") :
					continue

				if member == name :
					tclass = getattr(module, member)
					if inspect.ismodule(tclass) :
						continue

					print(tclass)
					for function in tclass.__dict__ :
						self.command_line(docfile, function, tclass)



DocGenerator()