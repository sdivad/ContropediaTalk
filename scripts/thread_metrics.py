import sys
import re

verbose = True
debug = False
debug_hard = False
write_chains = True

#usage: python thread_metrics.py input_file

filename_in = sys.argv[1]  #'../data/discussions.tsv' 

out_folder = '../discussion-metrics/'
filename_out = out_folder + 'thread_metrics.csv' #sys.argv[2]

if write_chains:
	chains_file = out_folder + 'chains.csv'
	f_chains = open(chains_file, 'w')
	f_chains.write('art_id\tthread_id\tUser1\tUser2\tlength\n')

chains_num = 0
chains_comments = 0

chain_threshold = 3

n_threads = 0

ipP = re.compile(r'\d+\.\d+\.\d+\.\d+')
botP = re.compile(r'.+[bB][oO][tT]$')


def main():
	global chains_comments
	global chains_num	
	if verbose: print 'Processing file %s' %filename_in
	with open(filename_in) as f:
		with open(filename_out, 'w') as f_out:

			f_out.write('\t'.join(['article_id', 'talk_id', 'thread_id', 'thread_title', 'comments', 'users', 'users_hindex', 'max_depth', 'tree_hindex', 'chains_num', 'chains_comments', 'tree_string']) + '\n')

			art_id = -1
			talk_id = -1			
			thread_id = -1
			thread_title = ''
			hist = {}
			depth = {}
			
			authors = {}
			children = {}
			root = 0
			
			chains_num = 0
			chains_comments = 0
			
			f.readline()
			for line in f:
				s = line.split('\t')
				id = int(s[2])
				parent = int(s[3])
				level = int(s[4])+1
				art_id = int(s[5])	
				talk_id = int(s[6])			
				thread_id = int(s[7])				
				author = s[12]
	
				if level <= 0:					
					#if id != 1: print 'something strange: article=%d, last_article=%d, id=%d' %(article, last_article, id)
					#~ tree_hindex = hindex(tree_hist)
					write_thread_metrics(f_out, art_id, talk_id, thread_id, thread_title, children, authors, root, depth) #, chains_num, chains_comments)
					
					
					thread_title = s[-1].strip('\n= ') 
					depth = {}
					depth[id] = 0
					
					chains_num = 0
					chains_comments = 0
					
					authors = {}
					authors[id] = 0
					children = {}
					root = 0
											
				else:
					if level > 0:
						if parent not in depth:
							d = 1
						else:
							d = depth[parent]+1	
						depth[id] = d

						authors[id] = author
						
						if root == 0: 
							root = id
						else:	
							if parent not in children:
								children[parent] = []
							children[parent].append(id)
							
			write_thread_metrics(f_out, art_id, talk_id, thread_id, thread_title, children, authors, root, depth) #, chains_num, chains_comments)		
	print 'written metrics for %d threads on file %s' %(n_threads, filename_out) 			


def tree2string(children, authors, root):
	
	nodes = ''
	if root in children and len(children[root])>0: 
		nodes = ', "children": ['
		i = 0
		for n in children[root]:
			if i > 0: nodes += ','
			nodes += tree2string(children, authors, n) 
			i += 1
		nodes += ']'
	
	username = authors[root]
	user_type = 'registered'
	if username == '-1': user_type = 'unsigned'
	elif ipP.match(username): user_type = 'IP'
	elif botP.match(username): user_type = 'bot'
		
	return '{"user":' + '"' + username + '"' + '"user_type":' + '"' + user_type + '"' + nodes + '}'


def get_max(dic):
	M = 0
	for v in dic.values():
		if v > M: M = v
	return M
	
	
def get_hist(dic):
	hist = {}
	for el in dic.values():
		if el != 0: 
			if el not in hist:
				hist[el] = 0			
			hist[el] += 1
	return hist
		
		
def hindex(dic):
	h = 0
	for v in dic:
		if dic[v] >= v: h = v
	return h


def count_chains(children, authors, root, chain, art_id, thread_id):

	global chains_comments
	global chains_num
	
	if debug_hard: print 'children: %s\nauthors: %s\nroot: %s\nchain: %s'%(str(children), str(authors), str(root), str(chain))

	chain_continuing = False
	prev_chain = chain
	
	a = authors[root]
	if a>0 and len(chain) > 1 and chain[-2] == a and chain[-1] != a:
		chain.append(a)
		if len(chain) >= chain_threshold:
			chains_comments += 1
			if debug: print 'found chain!!! ' + str(chain)
		
	else:
		if len(prev_chain) >= chain_threshold:
			chains_num += 1
			if debug: print 'chain ended!  ' + str(prev_chain)
			f_chains.write(str(art_id) + '\t' + str(thread_id) + '\t' + prev_chain[0] + '\t' + prev_chain[1] + '\t' + str(len(prev_chain)) + '\n' )
		if a <= 0: chain = []
		elif len(chain) > 0 and chain[-1] > 0: chain = [chain[-1], a]
		else: chain = [a]
			
	if root not in children or len(children[root]) == 0:
		if chain_continuing and len(prev_chain) >= chain_threshold:
			chains_num += 1
			f_chains.write(str(art_id) + '\t' + thread_title + '\t' + prev_chain[0] + '\t' + prev_chain[1] + '\t' + str(len(prev_chain)) + '\n' )	
			if debug: print 'chain ended at the end of a thread!  ' + str(prev_chain)
	else: 
		if root in children:
			for c in children[root]:
				count_chains(children, authors, c, chain, art_id, thread_id)
				
				
def write_thread_metrics(f_out, art_id, talk_id, thread_id, thread_title, children, authors, root, depth):
	global n_threads
	if len(authors) > 1:
		authors_hist = get_hist(authors)					
		tree_hist = get_hist(depth)
		count_chains(children, authors, root, [], art_id, thread_id)
		tree_string = tree2string(children, authors, root)
		f_out.write('\t'.join(map(str, [art_id, talk_id, thread_id, thread_title, len(authors)-1, len(authors_hist), hindex(get_hist(authors_hist)), get_max(depth), hindex(tree_hist), chains_num, chains_comments, tree_string])) + '\n')
		n_threads += 1

if __name__ == '__main__':	
	main()

	
		
	
		
