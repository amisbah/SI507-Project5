import requests_oauthlib
import webbrowser
import json
import secret_data_tumblr
import csv
import unittest
from datetime import datetime

##### CACHING SETUP #####
#--------------------------------------------------
# Caching constants
#--------------------------------------------------

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
DEBUG = True
CACHE_FNAME = "cache_contents.json"
CREDS_CACHE_FILE = "creds.json"

#--------------------------------------------------
# Load cache files: data and credentials
#--------------------------------------------------
# Load data cache
try:
    with open(CACHE_FNAME, 'r') as cache_file:
        cache_json = cache_file.read()
        CACHE_DICTION = json.loads(cache_json)
except:
    CACHE_DICTION = {}

# Load creds cache
try:
    with open(CREDS_CACHE_FILE,'r') as creds_file:
        cache_creds = creds_file.read()
        CREDS_DICTION = json.loads(cache_creds)
except:
    CREDS_DICTION = {}

#---------------------------------------------
# Cache functions
#---------------------------------------------
def has_cache_expired(timestamp_str, expire_in_days):
    """Check if cache timestamp is over expire_in_days old"""
    # gives current datetime
    now = datetime.now()

    # datetime.strptime converts a formatted string into datetime object
    cache_timestamp = datetime.strptime(timestamp_str, DATETIME_FORMAT)

    # subtracting two datetime objects gives you a timedelta object
    delta = now - cache_timestamp
    delta_in_days = delta.days


    # now that we have days as integers, we can just use comparison
    # and decide if cache has expired or not
    if delta_in_days > expire_in_days:
        return True # It's been longer than expiry time
    else:
        return False

def get_from_cache(identifier, dictionary):
    """If unique identifier exists in specified cache dictionary and has not expired, return the data associated with it from the request, else return None"""
    identifier = identifier.upper() # Assuming none will differ with case sensitivity here
    if identifier in dictionary:
        data_assoc_dict = dictionary[identifier]
        if has_cache_expired(data_assoc_dict['timestamp'],data_assoc_dict["expire_in_days"]):
            if DEBUG:
                print("Cache has expired for {}".format(identifier))
            # also remove old copy from cache
            del dictionary[identifier]
            data = None
        else:
            data = dictionary[identifier]['values']
    else:
        data = None
    return data


def set_in_data_cache(identifier, data, expire_in_days):
    """Add identifier and its associated values (literal data) to the data cache dictionary, and save the whole dictionary to a file as json"""
    identifier = identifier.upper()
    CACHE_DICTION[identifier] = {
        'values': data,
        'timestamp': datetime.now().strftime(DATETIME_FORMAT),
        'expire_in_days': expire_in_days
    }

    with open(CACHE_FNAME, 'w') as cache_file:
        cache_json = json.dumps(CACHE_DICTION)
        cache_file.write(cache_json)

def set_in_creds_cache(identifier, data, expire_in_days):
    """Add identifier and its associated values (literal data) to the credentials cache dictionary, and save the whole dictionary to a file as json"""
    identifier = identifier.upper() # make unique
    CREDS_DICTION[identifier] = {
        'values': data,
        'timestamp': datetime.now().strftime(DATETIME_FORMAT),
        'expire_in_days': expire_in_days
    }

    with open(CREDS_CACHE_FILE, 'w') as cache_file:
        cache_json = json.dumps(CREDS_DICTION)
        cache_file.write(cache_json)

#####

## OAuth1 API Constants - vary by API
### Private data in a hidden secret_data.py file
CLIENT_KEY = secret_data_tumblr.client_key 
CLIENT_SECRET = secret_data_tumblr.client_secret

### Specific to API URLs, not private
REQUEST_TOKEN_URL = "https://www.tumblr.com/oauth/request_token"
BASE_AUTH_URL = "https://www.tumblr.com/oauth/authorize"
ACCESS_TOKEN_URL = "https://www.tumblr.com/oauth/access_token"


def get_tokens(client_key=CLIENT_KEY, client_secret=CLIENT_SECRET,request_token_url=REQUEST_TOKEN_URL,base_authorization_url=BASE_AUTH_URL,access_token_url=ACCESS_TOKEN_URL,verifier_auto=False):
    oauth_inst = requests_oauthlib.OAuth1Session(client_key,client_secret=client_secret)

    fetch_response = oauth_inst.fetch_request_token(request_token_url)

    # Using the dictionary .get method in these lines
    resource_owner_key = fetch_response.get('oauth_token')
    resource_owner_secret = fetch_response.get('oauth_token_secret')

    auth_url = oauth_inst.authorization_url(base_authorization_url)
    # Open the auth url in browser:
    webbrowser.open(auth_url) # For user to interact with & approve access of this app -- this script

    # Deal with required input, which will vary by API
    if verifier_auto:
        verifier = input("Please input the verifier:  ")
    else:
        redirect_result = input("Paste the full redirect URL here:  ")
        oauth_resp = oauth_inst.parse_authorization_response(redirect_result) # returns a dictionary -- you may want to inspect that this works and edit accordingly
        verifier = oauth_resp.get('oauth_verifier')

    # Regenerate instance of oauth1session class with more data
    oauth_inst = requests_oauthlib.OAuth1Session(client_key, client_secret=client_secret, resource_owner_key=resource_owner_key, resource_owner_secret=resource_owner_secret, verifier=verifier)

    oauth_tokens = oauth_inst.fetch_access_token(access_token_url) # returns a dictionary

    # Use that dictionary to get these things
    # Tuple assignment syntax
    resource_owner_key, resource_owner_secret = oauth_tokens.get('oauth_token'), oauth_tokens.get('oauth_token_secret')

    return client_key, client_secret, resource_owner_key, resource_owner_secret, verifier

def get_tokens_from_service(service_name_ident, expire_in_days=7): # Default: 7 days for creds expiration
    creds_data = get_from_cache(service_name_ident, CREDS_DICTION)
    if creds_data:
        if DEBUG:
            print("Loading creds from cache...")
            print()
    else:
        if DEBUG:
            print("Fetching fresh credentials...")
            print("Prepare to log in via browser.")
            print()
        creds_data = get_tokens()
        set_in_creds_cache(service_name_ident, creds_data, expire_in_days=expire_in_days)
    return creds_data

# def create_request_identifier(url, params_diction):
#     sorted_params = sorted(params_diction.items(),key=lambda x:x[0])
#     params_str = "_".join([str(e) for l in sorted_params for e in l]) # Make the list of tuples into a flat list using a complex list comprehension
#     total_ident = url + "?" + params_str
#     return total_ident.upper() # Creating the identifier

def get_data_from_api(request_url,service_ident, expire_in_days=7):
    """Check in cache, if not found, load data, save in cache and then return that data"""
    # ident = create_request_identifier(request_url)
    data = get_from_cache(request_url,CACHE_DICTION)
    if data:
        if DEBUG:
            print("Loading from data cache: {}... data".format(request_url))
    else:
        if DEBUG:
            print("Fetching new data from {}".format(request_url))

        # Get credentials
        client_key, client_secret, resource_owner_key, resource_owner_secret, verifier = get_tokens_from_service(service_ident)

        # Create a new instance of oauth to make a request with
        oauth_inst = requests_oauthlib.OAuth1Session(client_key, client_secret=client_secret,resource_owner_key=resource_owner_key,resource_owner_secret=resource_owner_secret)
        # Call the get method on oauth instance
        # Work of encoding and "signing" the request happens behind the sences, thanks to the OAuth1Session instance in oauth_inst
        resp = oauth_inst.get(request_url)
        # Get the string data and set it in the cache for next time
        data_str = resp.text
        data = json.loads(data_str)
        set_in_data_cache(request_url, data, expire_in_days)
    return data

## ADDITIONAL CODE for program should go here...
## Perhaps authentication setup, functions to get and process data, a class definition... etc.

if __name__ == "__main__":
    if not CLIENT_KEY or not CLIENT_SECRET:
        print("You need to fill in client_key and client_secret in the secret_data.py file.")
        exit()
    if not REQUEST_TOKEN_URL or not BASE_AUTH_URL:
        print("You need to fill in this API's specific OAuth2 URLs in this file.")
        exit()

class Blog(object):
	def __init__(self,object):
		self.title = object["response"]["blog"]["title"]
		self.name = object["response"]["blog"]["name"]
		self.num_posts = object["response"]["blog"]["total_posts"]
		self.url = object["response"]["blog"]["url"]
		if object["response"]["blog"]["description"] == "":
			self.description = None
		else:
			self.description = object["response"]["blog"]["description"]

	def __str__(self):
		return "{} posts in {}".format(self.num_posts,self.title)

class Post(object):
	def __init__(self,object):
		self.type = object["type"]
		self.url = object["short_url"]
		self.summary = object["summary"]
		self.caption = object["caption"]
		self.tags_list = object["tags"]

	def formattedtags(self):
		tag_str = ", ".join(self.tags_list)
		return tag_str

def blog_posts_baseurl(blog_identifier):
	baseurl = "https://api.tumblr.com/v2/blog/{0}/posts?api_key={1}".format(blog_identifier,CLIENT_KEY)
	return baseurl

tumblr_hony_result = get_data_from_api(blog_posts_baseurl("www.humansofnewyork.com"),"TUMBLR")
hony_posts_list = tumblr_hony_result["response"]["posts"]

tumblr_npr_result = get_data_from_api(blog_posts_baseurl("nprontheroad.tumblr.com"),"TUMBLR")
npr_posts_list = tumblr_npr_result["response"]["posts"]

hony_blog = Blog(tumblr_hony_result)
npr_blog = Blog(tumblr_npr_result)

hony_post_objects = []
for each in hony_posts_list:
	hony_post_objects.append(Post(each))

npr_post_objects = []
for each in npr_posts_list:
	npr_post_objects.append(Post(each))

# a_post = npr_post_objects[13]
# tags_post = a_post.formattedtags()

f_blogs = open("blogs.csv","w")
f_blogs.write("Blog Title, Number of posts, URL, Description\n")
f_blogs.write('"{}", {}, {}, "{}"\n'.format(hony_blog.title, hony_blog.__str__(),hony_blog.url,hony_blog.description))
f_blogs.write('"{}", {}, {}, "{}"\n'.format(npr_blog.title, npr_blog.__str__(),npr_blog.url,npr_blog.description))
f_blogs.close()

f_npr_posts = open("npr_posts.csv","w")
f_npr_posts.write("Post Summary,URL,Tags,Type\n")
for each in npr_post_objects:
	f_npr_posts.write('"{}",{},"{}",{}\n'.format(each.summary,each.url,each.formattedtags(),each.type))
f_npr_posts.close()

f_hony_posts = open("hony_posts.csv","w")
f_hony_posts.write("Post Summary,URL,Tags,Type\n")
for each in hony_post_objects:
	f_hony_posts.write('"{}",{},"{}",{}\n'.format(each.summary,each.url,each.formattedtags(),each.type))
f_hony_posts.close()

## Make sure to run your code and write CSV files by the end of the program.
