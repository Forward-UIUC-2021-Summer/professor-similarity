Module for finding related professors(based on another professor), and similar professors(based on an input list of keywords)<br />
First run relation_graph.py. This module will connect to an online database with two tables ---- professor names and their weighted keywords ; NPMI scores for most pairs of keywords appeared in computer science research fields.<br />
Then a dynamic relation graph is constructed based on their weighted keywords, where the distance(closeness) between every two pair of professors are calculated.<br />
Next, this module will run Dijkstr'a Algorithm starting from each professor, and populate a new database with the minimum distance(relativeness) between every pairs of professors.<br />
At the meantime, it will also create a table in the new database with the similarity between every pair of keyword and professor. This table will in the future be used for calculating similar professors based on users' inputs of list of keywords.<br />
Finally, the new database is successfully populated with all the information we need. Users will be interacting through the user_intereaction.py to realize the functionality.
