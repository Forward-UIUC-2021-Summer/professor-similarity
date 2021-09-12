import math
import mysql.connector
import operator
import time


# Convert an integer list into a string of integer list
# that can be used in MySQL query.
# A helper function for getting a list of professor ids and their information
# [1,2,3]  ->  "(1,2,3)"
def convert_int_list(some_list):
    ret = "("
    for i in some_list:
        ret += str(i)
        ret += ","
    ret = ret[:-1]
    ret += ")"
    return ret


# Convert a string list into a string of string list
# that can be used in MySQL query.
# A helper function for getting a list of professor names and their information
# ["A", "B", "C"]  ->  "('A','B','C')"
def convert_str_list(some_list):
    ret = "("
    for i in some_list:
        ret += "'"
        ret += i
        ret += "',"
    ret = ret[:-1]
    ret += ")"
    return ret


# The class for node in the relation graph to be constructed
# Each node is a professor with his/her weighted keywords.
class Professor:

    def __init__(self, name, dict_of_focus_to_weight):
        self.name = name
        self.focus_to_weight_dict = self.update_to_standard_dict(dict_of_focus_to_weight.copy())
        self.adjacent = {}  # neighbor node  ->  edge weight

    # so the sum of all the weights of key-words for a professor is 100
    # And we only consider the top ten weighted keywords
    @staticmethod
    def update_to_standard_dict(diction):
        # Only take the top 20 weighted keywords of each professor for this whole program
        if len(diction) <= 20:
            opt_dict = diction.copy()
        else:
            opt_dict = dict(sorted(diction.items(), key=operator.itemgetter(1), reverse=True)[:20])
        total = sum(opt_dict.values())
        for k in opt_dict.keys():
            opt_dict[k] = opt_dict[k] / total
            opt_dict[k] = round(opt_dict[k] * 100)
        return opt_dict

    def get_connections(self):
        return list(self.adjacent.keys())

    def get_name(self):
        return self.name

    # returns the weight of the edge between this professor and a neighbor
    def get_weight(self, neighbor):
        return self.adjacent[neighbor]

    def get_focuses(self):
        return self.focus_to_weight_dict.keys()

    def get_focus_weight(self, focus):
        return self.focus_to_weight_dict[focus]


class Graph:
    def __init__(self, fos_cursor):
        self.prof_name_dict = {}  # professor name string  ->  professor node
        self.num_vertices = 0
        self.focus_to_prof_names_dict = {}  # focus string  ->  list of professor name strings
        self.fos_cursor = fos_cursor  # dataset about professors recorded
        self.fos_cursor = fos_cursor  # dataset about similarity between two words
        self.construct_graph()

    # print the information of the relation graph in a straight-forward way
    def __str__(self):
        ret = ""
        for name in self.prof_name_dict.keys():
            ret += name
            ret += ", whose neighbors are: { "
            node = self.get_professor_node(name)
            for neighbor in node.get_connections():
                ret += neighbor
                ret += " : "
                ret += str(node.get_weight(neighbor))
                ret += "; "
            ret += "} \n"
        return ret

    # Add the new professor as a node in the relation graph
    # Use the calc_distance function to find the distance of current professor to all the others
    # Then connect the edges.
    def add_professor_node(self, name, dict_of_focus_to_weight):
        self.num_vertices += 1
        new_vertex = Professor(name, dict_of_focus_to_weight)
        self.prof_name_dict[name] = new_vertex
        for focus in new_vertex.focus_to_weight_dict.keys():
            if focus not in self.focus_to_prof_names_dict:
                self.focus_to_prof_names_dict[focus] = [name]
            else:
                self.focus_to_prof_names_dict[focus].append(name)
        for other_prof in self.prof_name_dict.keys():
            if other_prof == name:
                continue
            edge_weight = self.calc_distance(new_vertex, self.get_professor_node(other_prof))
            self.add_edge(name, other_prof, edge_weight)
        return new_vertex

    # Fetch all the professors and their weighted focus in the database
    # Add them to the relation graph as individual nodes using the add_professor_node() function
    def construct_graph(self):
        self.fos_cursor.execute("SELECT name FROM Professor")
        list_of_professors = list(self.fos_cursor.fetchall())
        for name in list_of_professors:
            self.fos_cursor.execute("SELECT keyword, occurrence FROM Keywords WHERE name = '%s'" % name[0])
            rows = list(self.fos_cursor.fetchall())
            dict_of_focus_to_weight = {}
            for r in rows:
                dict_of_focus_to_weight[r[0]] = r[1]
            self.add_professor_node(name[0], dict_of_focus_to_weight)

    # returns all the professor names of this graph
    def get_vertices(self):
        return self.prof_name_dict.keys()

    # return the node object with professor name n
    def get_professor_node(self, n):
        return self.prof_name_dict[n]

    def add_edge(self, frm, to, cost):
        self.prof_name_dict[frm].adjacent[to] = cost
        self.prof_name_dict[to].adjacent[frm] = cost

    def calc_distance_helper(self, prof_node1, sim_dict, id_name1, id_name2, value):
        for a in id_name1.keys():
            max_factor = 0
            for b in id_name2.keys():
                if (a, b) in sim_dict:
                    s_score = sim_dict[(a, b)]
                elif (b, a) in sim_dict:
                    s_score = sim_dict[(b, a)]
                elif a == b:
                    s_score = 1
                else:
                    s_score = 0
                if s_score > max_factor:
                    max_factor = s_score
            if id_name1[a] not in prof_node1.get_focuses():
                continue
            value -= max_factor * prof_node1.get_focus_weight(id_name1[a])
        return value

    # Return the distance between two professor nodes based on their key words and NPMI scores
    # The algorithm goes as follows:
    # The initial distance between any two professors is 200
    # For each keyword for each professor, compare it to all the keywords in the other professor
    # Then take the largest NPMI score (highest semantic similarity), a float between 0 and 1
    # Multiply this score with its weight in its corresponding professor, which should be from 0 to 100
    # Subtract this result from the initial distance
    # After running the above steps for all keywords, we will get a distance between this pair of professors
    # Which is certainly to be in the range of 0 to 200
    def calc_distance(self, prof_node1, prof_node2):
        focus1 = prof_node1.get_focuses()
        focus2 = prof_node2.get_focuses()
        focus1_list = convert_str_list(focus1)
        focus2_list = convert_str_list(focus2)
        self.fos_cursor.execute("SELECT * FROM FoS WHERE FoS_name in " + focus1_list)
        id_name1 = self.fos_cursor.fetchall()
        self.fos_cursor.execute("SELECT * FROM FoS WHERE FoS_name in " + focus2_list)
        id_name2 = self.fos_cursor.fetchall()

        id_name1 = {a[0]: a[1] for a in id_name1}
        id_name2 = {a[0]: a[1] for a in id_name2}  # Dictionary of id to focus for each professor
        id1_list = convert_int_list(id_name1.keys())
        id2_list = convert_int_list(id_name2.keys())
        self.fos_cursor.execute("SELECT id1, id2, npmi FROM FoS_npmi_Springer " +
                                 "WHERE (id1 in " + id1_list + " AND id2 in " + id2_list + " )")
        sim_pairs = self.fos_cursor.fetchall()

        sim_dict = {}  # Dictionary of every pair of focuses and their NPMI score
        for p in sim_pairs:
            sim_dict[(p[0], p[1])] = p[2]
        value = self.calc_distance_helper(prof_node1, sim_dict, id_name1, id_name2, 200)
        value = self.calc_distance_helper(prof_node2, sim_dict, id_name2, id_name1, value)

        return round(value, 3)

    # Input a focus, first get all the focuses that have NPMI scores with it greater that 0.2
    # Find all the professors that have focuses in them, multiply them with their corresponding weights
    # Then populate the website database with (this focus, a professor, factor of similarity with this professor)
    def populate_for_focus(self, focus):
        focus_id_dict = {}
        id_factor_dict = {}
        prof_factor_dict = {}
        self.fos_cursor.execute("SELECT id FROM FoS WHERE FoS_name='" + focus + "'")
        id = self.fos_cursor.fetchone()
        if id is None:
            return {}
        id = id[0]
        self.fos_cursor.execute("SELECT id1, id2, npmi FROM FoS_npmi_Springer "
                                "WHERE (id1 = %s OR id2 = %s) AND npmi > 0.3", (id, id))
        triple = self.fos_cursor.fetchall()
        id_factor_dict[id] = 1
        for t in triple:
            if t[0] == id:
                id_factor_dict[t[1]] = t[2]
            else:
                id_factor_dict[t[0]] = t[2]
        ids = id_factor_dict.keys()
        ids = convert_int_list(ids)
        self.fos_cursor.execute("SELECT * FROM FoS WHERE id in " + ids)
        pairs = self.fos_cursor.fetchall()
        for p in pairs:
            focus_id_dict[p[1]] = p[0]

        focuses = focus_id_dict.keys()
        for f in focuses:
            try:
                names = self.focus_to_prof_names_dict[f]
            except:
                continue
            for p in names:
                node = self.get_professor_node(p)
                if f not in node.get_focuses():
                    continue
                factor = id_factor_dict[focus_id_dict[f]]
                if p in prof_factor_dict:
                    tmp = prof_factor_dict[p]
                    prof_factor_dict[p] = round(factor * node.get_focus_weight(f) + tmp, 3)
                else:
                    prof_factor_dict[p] = round(factor * node.get_focus_weight(f), 3)
        return prof_factor_dict

    @staticmethod
    def merge_dicts(dict1, dict2):
        for k in dict2.keys():
            if k in dict1:
                dict1[k] += dict2[k]
            else:
                dict1[k] = dict2[k]
        return dict1

    # return a list of (name, int) pairs, sorted based on the int part,
    # larger value means more related to the input focus
    def rank_list_of_professors(self, focuses):
        rank_map = {}
        for focus in focuses:
            focus_map = self.populate_for_focus(focus)
            rank_map = self.merge_dicts(rank_map, focus_map)
        rank_list = list(zip(rank_map.keys(), rank_map.values()))
        rank_list.sort(key=lambda x: -x[1])
        return rank_list

    # a helper function for the Dijkstra's Algorithm, could be improved by using heap sort
    def min_distance_node(self, dist, sptset):
        math_min = math.inf
        min_name = ""
        for name in self.prof_name_dict.keys():
            if dist[name] < math_min and not sptset[name]:
                math_min = dist[name]
                min_name = name
        return min_name

    # input the name of a professor as a string, return related professors as a rank list
    def dijkstra(self, src):
        dist_dict = {name: math.inf for name in self.prof_name_dict.keys()}
        dist_dict[src] = 0
        sptset = {name: False for name in self.prof_name_dict.keys()}
        # which stands for "shortest path tree"

        for count in range(5):
            # Pick the minimum distance vertex from
            # the set of vertices not yet processed.
            u = self.min_distance_node(dist_dict, sptset)
            sptset[u] = True
            # Update dist value of the adjacent vertices
            # of the picked vertex only if the current
            # distance is greater than new distance and
            # the vertex in not in the shortest path tree
            for name in self.prof_name_dict.keys():
                if name not in self.get_professor_node(u).get_connections():
                    continue
                if not sptset[name] and dist_dict[name] > dist_dict[u] + self.get_professor_node(u).get_weight(
                        name):
                    dist_dict[name] = dist_dict[u] + self.get_professor_node(u).get_weight(name)
        return dist_dict

    # returns a rank list of related professor to the give professor based only on key words
    # Use Dijkstra's algorithm to return a list of (name, int) pairs,
    # sorted based on the int part, with smaller value meaning more closely related
    def related_professors(self, src_prof):
        dist_dict = self.dijkstra(src_prof)
        rank_list = []
        for prof in dist_dict:
            rank_list.append((prof, dist_dict[prof]))
        rank_list.sort(key=lambda x: x[1])
        return rank_list


def populate_similar_professors(relation_graph, fos_cursor, fos_data):
    keyword_list = relation_graph.focus_to_prof_names_dict.keys()
    keyword_list = set(keyword_list)
    for k in keyword_list:
        print(k)
        rank_map = relation_graph.populate_for_focus(k[0])
        for r in rank_map.keys():
            try:
                fos_cursor.execute("INSERT INTO Similar (Keyword, Similar_Prof, Similar_Factor) VALUES " 
                                   "(%s, %s, %s )", (k[0], r, rank_map[r]))
            except:
                fos_cursor.execute("REPLACE INTO Similar (Keyword, Similar_Prof, Similar_Factor) VALUES "
                                   "(%s, %s, %s )", (k[0], r, rank_map[r]))
    fos_data.commit()


def populate_related_professors(relation_graph, fos_cursor, fos_data):
    for prof in relation_graph.prof_name_dict.keys():
        relation_list = relation_graph.related_professors(prof)
        for pair in relation_list:
            if pair[0] == prof:
                continue
            try:
                fos_cursor.execute("INSERT INTO Related (Prof, Related_Prof, Related_Factor) VALUES (%s, %s, %s )",
                                   (prof, pair[0], pair[1]))
            except:
                fos_cursor.execute("REPLACE INTO Related (Prof, Related_Prof, Related_Factor) VALUES (%s, %s, %s )",
                                   (prof, pair[0], pair[1]))
    fos_data.commit()


if __name__ == '__main__':
    fos_data = mysql.connector.connect(
        host="104.198.163.126",
        user="root",
        password="yEBpALG6zHDoCFLn",
        database="project"
    )
    fos_cursor = fos_data.cursor()
    print("data base connected")
    relation_graph = Graph(fos_cursor)
    print("relation graph constructed")

    # to populate the website database, uncomment the following codes:
    populate_similar_professors(relation_graph, fos_cursor, fos_data)

    # to populate the website database, uncomment the following codes:
    populate_related_professors(relation_graph, fos_cursor, fos_data)

