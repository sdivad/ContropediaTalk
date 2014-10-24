File thread_metrics.csv

article_id	article id
talk_id		id of the talk page containing the thread
thread_id	id of the thread
thread_title	title of the thread
comments	number of signed comments in the thread
users		number of distinct users participating to the thread
users_hindex	h-index of the users participating to the thread (maximum number h such that there are at least h users who have written at least h comments each)
max_depth	maximum indentation level
tree_hindex	maximum number h such that there are at least h comments at depth h
chains_num	total number of reply chains, i.e. number of occurrences of the pattern A -> B -> A (eventually continued with more mutual replies between A and B), in which a user replies back to the user who has just replied back to his/her comment
chains_comments	maximum number h such that there are at least h comments at depth h
tree_string	compact crepresentation of the thread's tree structure, for visualization as a tree


