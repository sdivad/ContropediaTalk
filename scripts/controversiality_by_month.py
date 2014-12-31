#
#This script is part of the Contropedia project
#
#It computes the controversiality of "actors" in Wikipedia articles over time,
#based on discussion threads (in the article talk page) associated to each actor
#
#Input is needed from projects: 
# https://github.com/sdivad/WikiTalkParser
# https://github.com/boogheta/contropedia-sprint-scripts
#

import codecs
import sys
import datetime
import math


page_title = sys.argv[1]
datadir = "../../contropedia-sprint-scripts/discussions_match/data/%s" % page_title

#If True, it will print annoying messages on the screen
debug = False

#weight to make stronger the association between a thread and an actor when the actor is mentioned in the thread title
TITLE_WEIGHT = 2

#weight to make stronger the association between a given comment and an actor when the actor is mentioned in the comment
COMMENT_WEIGHT = 1

#weight to give more importance to reply chains (when a user replies back: A -> B -> A) when computing controversiality of comments
CHAIN_WEIGHT = 3

#Input file containing one comment with metadata per line. Discussion associated to one only article is expected
#Format of the input file is described here:
#https://github.com/sdivad/WikiTalkParser/tree/master/discussions
f = open(datadir + '/discussions.tsv', 'r')
#~ f = open('../data/discussions.tsv', 'r')

#Input file containing matching between actors (elements in the article) to discussion threads mentioning them 
#(file 'actors_matched.csv' produced in https://github.com/boogheta/contropedia-sprint-scripts/ )
f_actors = open(datadir + '/actors_matched.csv', 'r')
#~ f_actors = open('../data/actors_matched.csv', 'r')


#Output file
#~ output_folder = '../discussion-metrics/'
#~ f_out = open(output_folder + 'actor_controversiality_by_month.csv', 'w')
f_out = open(datadir + '/actor_controversiality_by_month.csv', 'w')
#~ f_out = codecs.open(sys.argv[3], 'w', 'UTF-8')

#Load thread-actor matchings into a dictionary
def load_actors_data(f):
	d = {}
	f.readline()
	for line in f:
		art, actor, thread, perma, n_title, n, timestamps, ids = line.strip('\n').split('\t')
		if thread not in d: d[thread] = {}
		if actor in d[thread] and debug: print 'duplicated actor-thread: %s --- %s' %(actor, thread)
		n_title = int(n_title)
		d[thread][actor] = [n_title, timestamps, ids] 
	return d		

		
actor_threads = load_actors_data(f_actors)
actor_comments = {}


f.readline()
l = 0

grand_parent_auth = ''
n_thread_comments = 0
prev_thread = ''

for line in f:
	if True:
		l += 1
		s = line.strip('\n').split('\t')
		thread = s[-1]
		cid = s[3]
		level = int(s[4])
		art = s[5]
		ts = int(s[8])
		auth = s[12]
		parent_auth = s[13]
		date = datetime.datetime.fromtimestamp(ts*60).strftime('%Y-%m-%d')

		if thread != prev_thread:
			n_thread_comments = 0
			grand_parent_auth = 0
			prev_thread = thread
		
		#Author is '0' only in structural nodes (thread or page titles). Discard such lines		
		if auth != '0':
			n_thread_comments += 1			
		
		if auth != '0' and date > '2001-01-01':			
			reply, reply_back = 0, 0
			if parent_auth != '0' and parent_auth != '-1' and parent_auth != auth: reply = 1
			if reply > 0 and auth == grand_parent_auth: reply_back = 1
			
			#to get this to work for days instead of months, just change next line to: day = date, and replace every occurrence of "month" with "day" (or simply replace each occurrence of "month" with "date")
			month = date[:-3]
			if thread in actor_threads:
				for actor in actor_threads[thread]:
					#compute the weight of the actor in each thread in which it appears, computing the number of comments in which it appears before the timestamp of the current comment, and normalize by the number of comments considered
					actor_thread_weight = 0
					for timestamp in actor_threads[thread][actor][1].strip("'").replace("'","").replace("[","").replace("]","").split(", "):
						if len(timestamp)>5: 
							if int(timestamp)<ts:
								actor_thread_weight += 1
					#weight each thread in which an actor has appeared (before the current comment) according to the proportion of previous comments in which it has appeared	
					#NOTE: there is no normalization based on the number of actors appearing in a thread; it could be added
					actor_thread_weight /= float(n_thread_comments)
					#add a special weight if the actor is mentioned in the text of the comment
					if cid in actor_threads[thread][actor][2].strip("'").replace("'","").replace("[","").replace("]","").split(", "): actor_thread_weight += COMMENT_WEIGHT
					#add a special weight if the actor is mentioned in the thread title
					if actor_threads[thread][actor][0]> 0: actor_thread_weight += TITLE_WEIGHT
								
					if actor_thread_weight > 0:	
						if actor not in actor_comments: actor_comments[actor] = {}
						#activity and controversiality values -> 0: n_comments, 1: n_comments_weighted, 2: depth_controversiality, 3: depth_log_controversiality, 4: chains_controversiality, 5: chains_only_controversiality
						#NOTE: more metrics can be added here; in particular, metrics accounting for the previous activity of the users involved in the discussion
						if month not in actor_comments[actor]: actor_comments[actor][month] = [0,0,0,0,0,0]
						actor_comments[actor][month][0] += 1	
						actor_comments[actor][month][1] += 1 * actor_thread_weight	
						if reply != 0 and level > 0: 
							actor_comments[actor][month][2] += level * actor_thread_weight
							actor_comments[actor][month][3] += math.log(level+1) * actor_thread_weight
							if reply_back > 0:
								actor_comments[actor][month][4] += CHAIN_WEIGHT * actor_thread_weight
								actor_comments[actor][month][5] += 1 * actor_thread_weight
							else:	
								if debug: print '%s - %s -> %d, %d' % (auth, grand_parent_auth, reply, reply_back)
								actor_comments[actor][month][4] += 1 * actor_thread_weight
								
			grand_parent_auth = parent_auth
			

#Write output
def write_actors(art, actor_comments, f_out):
	f_out.write('article\tactor\tmonth\tn_comments\tn_comments_weighted\tdepth_controversiality\tdepth_log_controversiality\tchains_controversiality\tchains_only_controversiality\n')
	for a in actor_comments:
		for month in actor_comments[a]:
			f_out.write('\t'.join(map(str, [art, a, month] + actor_comments[a][month])) + '\n')
		
		
write_actors(art, actor_comments, f_out)		
					
	
