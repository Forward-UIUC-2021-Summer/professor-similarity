<h1>Module for finding related and similar professors</h1>

<h2>Run relation_graph.py</h2>

The code will operate in the following steps:

<h3>1. Dynamically constructing a Relation Graph</h3>
This python file will connect to an online database with two tables: <p>Professor names and their weighted keywords ;
  NPMI scores for most pairs of keywords appeared in computer science research fields</p>

Then a dynamic relation graph is constructed. The strucutre and logic of the graph is as follows:

<h4>Graph Structure</h4>
Each node in the graph represents a professor in the database. And every node contains a dictionary that maps each keyword of this professors to its corresponding weight.

The distance between two nodes, which is the closeness of two professors, is calculated by comparing each pair of keywords of the two professors and adding up their NPMI scores multiplied by the keywords' weights. The higher the value, the closer in the two professors' research area.

<h3>2. Certain graph algorithms are performed</h3>
Next, this module will run Dijkstr'a Algorithm starting from each professor.

In this way, we get a list for each node(professor) of its minimum distances to all the other professors.

<h3>3. Populating the website database</h3>
<p>The code then populates a new database, which we call the website database, with the lists above of distances between every pairs of professors.</p>

<p>At the meantime, the code also computes the similarity of each keyword with each professor by adding up the NPMI scores of this certain keyword with all the keywords of this professor. And all these keyword-professor pairs will be populated into the new database. This table will in the future be used for calculating similar professors based on users' inputs of list of keywords.</p>

<h2>Interacting with user_interaction.py</h2>
After the new database is successfully populated with all the information we need, users will be interacting through the user_intereaction.py to realize the functionality.

<h3>1. related_professors(name, ...)</h3>
Scroll down to the bottom of this file, user can find the related_professor() function in the main field. Changing the {name} parameter can return the related professors of each given professor.

<h3>2. rank_list_of_professors([keywords...], ...)</h3>
Also at the bottom of the file, there is the rank_list_of_professors() function that returns the rank list of similar professors based on the user's input of a list of keywords. Changing the {[keywords...]} parameter of the function to any list of keywords the user wants.

