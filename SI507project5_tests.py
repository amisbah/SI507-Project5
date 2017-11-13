import unittest
from SI507project5_code import *

class BlogTest(unittest.TestCase):
	def setUp(self):
		testblog = get_data_from_api(blog_posts_baseurl("astrophysics-daily.tumblr.com"),"TUMBLR")
		self.testobject = Blog(testblog)

	def test_Blog_class(self):
		self.assertTrue(type(self.testobject.title),type("string"))
		self.assertTrue(type(self.testobject.name),type("string"))
		self.assertTrue(type(self.testobject.num_posts),type(3))

	def tearDown(self):
		pass

class PostTest(unittest.TestCase):
	def setUp(self):
		testblog2 = get_data_from_api(blog_posts_baseurl("latenightseth.tumblr.com"),"TUMBLR")
		test_posts_list = testblog2["response"]["posts"]
		self.post_objects = []
		for each in test_posts_list:
			self.post_objects.append(Post(each))

	def test_Post_class(self):
		self.assertTrue(len(self.post_objects) <=20)
		self.assertTrue(type(self.post_objects[0].summary),type("string"))
		self.assertTrue(type(self.post_objects[3].caption),type("string"))
		self.assertIsInstance(self.post_objects[5].tags_list, list)
		self.assertIsInstance(self.post_objects[8], Post)
		self.assertTrue(type(self.post_objects[10].formattedtags()),type("string"))

class TestCSVs(unittest.TestCase):
	def setUp(self):
		self.blogs = open("blogs.csv",'r')
		self.npr = open("npr_posts.csv",'r')
		self.hony = open("hony_posts.csv",'r')

	def test_csv_files(self):
		self.assertTrue(self.blogs.read())
		self.assertTrue(self.npr.read())
		self.assertTrue(self.hony.read())

	def tearDown(self):
		self.blogs.close()
		self.npr.close()
		self.hony.close()

if __name__ == "__main__":
    unittest.main(verbosity=2)
