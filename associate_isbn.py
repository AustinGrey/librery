import requests
import collections
import sqlite3 as sql
import os
import time

filename = os.path.join(os.path.dirname(__file__), 'example.db')
conn = sql.connect(filename)
c = conn.cursor()

# required API key for the ISBN db website API v2
filename = os.path.join(os.path.dirname(__file__), 'api.key')
with open(filename) as tokenFile:
	api_key = tokenFile.read()

# Keys from the isbndb website API v2 that return single values
ISBN_DB_API_2_DATA_SINGLE_KEYS = [
	"awards_text",
	"marc_enc_level",
	"summary",
	"isbn13",
	"dewey_normal",
	"title_latin",
	"publisher_id",
	"dewey_decimal",
	"publisher_text",
	"language",
	"physical_description_text",
	"isbn10",
	"edition_info",
	"urls_text",
	"lcc_number",
	"publisher_name",
	"book_id",
	"notes",
	"title",
	"title_long"
	]
	
# Keys from the isbndb website API v2 that return multiple values
ISBN_DB_API_2_DATA_LIST_KEYS = [
	{"author_data":{
		"name":"Richards, Rowland",
		"id":"richards_rowland"
	}},
	"subject_ids"
]

ISBN_DB_TO_LIBRERY_DB_CONVERSION_TABLE = {
	"awards_text":"awards_text",
	"book_id":"book_id",
	"dewey_decimal":"dewey_decimal",
	"dewey_normal":"dewey_normal",
	"edition_info":"edition_info",
	"isbn10":"isbn10",
	"isbn13":"isbn13",
	"language":"language",
	"lcc_number":"lcc_number",
	"marc_enc_level":"marc_enc_level",
	"notes":"notes",
	"physical_description_text":"physical_description_text",
	"publisher_id":"publisher_id",
	"publisher_name":"publisher_name",
	"publisher_text":"publisher_text",
	"summary":"summary",
	"title":"title",
	"title_latin":"title_latin",
	"title_long":"title_long",
	"urls_text":"urls_text",
}
	


def scrape():
	print("Begin new scrape at " + time.strftime("%a, %d %b %Y %H:%M:%S %Z", time.localtime()))
	
	
	BOOK_STRING = "http://isbndb.com/api/v2/json/" + api_key + "/book/"
	
	# get all the books with isbn13 that haven't been handled
	c.execute("SELECT b_id, isbn13 FROM books WHERE isbndb_scraped is NULL and isbn13 != ''")
	book_13s = c.fetchall()
	# get all the ones with isbn10 that haven't been handled and dont have an isbn13
	c.execute("SELECT b_id, isbn10 FROM books WHERE isbndb_scraped is NULL and isbn13 == '' and isbn10 != ''") 
	book_10s = c.fetchall()
	# for feed in db.feeds
	i = 0
	for book13 in book_13s:
		print(book13[1])
		c.execute('INSERT OR IGNORE INTO isbndb_books (b_id) VALUES (?)', (book13[0],))
		r = requests.get(BOOK_STRING + book13[1])
		json = r.json()
		if 'error' in json.keys():
			print("Book with ISBN13 " + book13[1] + " was not found in the ISBNDB database")
			c.execute('''
				UPDATE books
				SET isbndb_scraped = 0 
				WHERE b_id=? ''' , (book13[0],))
			continue
		for key in json['data'][0]:
			if (key in ISBN_DB_API_2_DATA_SINGLE_KEYS):
				c.execute('''
					UPDATE isbndb_books 
					SET ''' + ISBN_DB_TO_LIBRERY_DB_CONVERSION_TABLE[key] + '''=? 
					WHERE b_id =? ''' , (json['data'][0][key], book13[0]))
			else:
				print("Unhandled key for book with ISBN13 " + book13[1] + " '" + key + "' has value '", end="")
				print(json['data'][0][key], end="")
				print("'")
			c.execute('''
					UPDATE books
					SET isbndb_scraped = 1 
					WHERE b_id=? ''' , (book13[0],))
		
	for book10 in book_10s:
		print(book10)
	
	conn.commit()
	'''
		print("\tScraping feed:", fid)
		# strip out the id (first field)
		fid = fid[0]
		# submit the computed request for the feed's info
		feed = graph.get_object(id=fid, fields=FEED_SCRAPE, filter='stream', date_format="U")
		print("\t\tResponse Received")
		# update the feed meta data
		c.execute('INSERT OR REPLACE INTO feeds (id, name, picture, description) VALUES (?,?,?,?)', 
					  (fid, 
					   feed['name'], 
					   feed['cover']['source'] if 'cover' in feed else None, 
					   ######################
					   # @TODO THIS COVER NEEDS TO BE TRANSLATED TO FIT THE SAME WINDOW THAT IT WOULD ON Facebook
					   # The method is as follows
						#					   
						#Of the solutions you linked to above, the third is the closest to being 100% accurate (and may very well be for his use cases).
						#
						#Here's how it worked out for me for event covers (change fw and fh for different types of covers).
						#
						#You need:
						#
						#fw - the width that Facebook displays the cover image
						#fh - the height that Facebook displays the cover image
						#nw - the natural width of the image retrieved from Facebook
						#nh - the natural height of the image retrieved from Facebook
						#ow - the width to which you're scaling the image down in your UI
						#oy - the offset_y value for the cover photo
					   #
					   # then the top margin must become calc(- (oy * ow / 100) * ((nh / nw) - (fh / fw)))
					   #
					   # note that for group cover photos, fw = 820 and fh = 250
					   #
					   feed['description'] if 'description' in feed else None))
		# for posts in response !!not in database - not handled yet!! , get information, store into database
		posts = feed['feed']['data']
		posts = [x for x in posts]
		for post in posts:
			print("\t\tScraping post:", post['id'])
			c.execute('INSERT OR REPLACE INTO posts (id, feed_id, author, message, created, updated) VALUES (?,?,?,?,?,?)', 
					  (post['id'], 
					   fid, 
					   post['from']['id'], 
					   post.get('message'), # the message might not exist if it was just a simple link share
					   post['created_time'], 
					   post['updated_time']))
			scrape_person(post['from'])
			print('\t\tScraping comments')
			
			# not all posts have comments
			try:
				comment_data = post['comments']['data']
			except:
				print('\t\t\tno available comments')
				comment_data = []
				
			for comment in comment_data:
				print('\t\t\tcomment:',comment['id'])
				#for comments in set not in database, get information, store into database
				c.execute('INSERT OR REPLACE INTO comments (id, parent_post, author, text, created, parent_comment) VALUES (?,?,?,?,?,?)', 
					(comment['id'], 
					 post['id'], 
					 comment['from']['id'], 
					 comment['message'], 
					 comment['created_time'], 
					 None))
				scrape_person(comment['from'])
				
				try:
					child_comment_data = comment['comments']['data']
				except:
					print('\t\t\tno available child comments')
					child_comment_data = []
				
				for child_comment in child_comment_data:
					print('\t\t\t\tchild_comment:',child_comment['id'])
					c.execute('INSERT OR REPLACE INTO comments (id, parent_post, author, text, created, parent_comment) VALUES (?,?,?,?,?,?)', 
						(child_comment['id'], 
						 post['id'], 
						 child_comment['from']['id'], 
						 child_comment['message'], 
						 child_comment['created_time'], 
						 comment['id']))
					scrape_person(child_comment['from'])
		print('\tDone scraping feed')
		
	conn.commit()
	'''
	
def scrape_person(person):
	# person is a data object returned from a 'from{fields}' graph API call
	print('\t\tScraping person:',person['id'])
	c.execute('INSERT OR REPLACE INTO people (id, name, picture) VALUES (?,?,?)', (
		person['id'], 
		person['name'], 
		person['picture']['data']['url']) )
	
	
scrape()