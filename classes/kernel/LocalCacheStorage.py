from classes.singleton import Singleton


class LocalCacheStorage (metaclass=Singleton):

	dob_submissions = {}


	def add_submission(self, user_id,  submission, overwrite = False):
		if user_id not in self.dob_submissions or overwrite:
			self.dob_submissions[user_id] = submission
		return self.get_submission(user_id)

	def get_submission(self, user_id):
		return self.dob_submissions.get(user_id)

	def clear_submissions(self):
		self.dob_submissions.clear()

	def remove_submission(self, user_id):
		self.dob_submissions.pop(user_id, None)


