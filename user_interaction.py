import mysql.connector
from relation_graph import convert_str_list


# input a professor's name, return a rank list of related professors
# all the data involved in this function is already stored in the database
def related_professors(prof_name, fos_cursor):
    fos_cursor.execute("SELECT Related_Prof, Related_Factor FROM Related WHERE Prof='" + prof_name + "'")
    rank_pairs = fos_cursor.fetchall()
    if rank_pairs is None:
        return []
    else:
        rank_pairs.sort(key=lambda x: x[1])
    return rank_pairs


# input a list of keywords, return a rank list of similar professors
# all the data involved in this function is already stored in the database
def rank_list_of_professors(focuses, fos_cursor):
    ret_pairs = {}
    set = {}
    focuses_str = convert_str_list(focuses)
    fos_cursor.execute("SELECT Keyword, Similar_Prof, Similar_Factor FROM Similar WHERE Keyword in " + focuses_str)
    rank_pairs = fos_cursor.fetchall()
    for pair in rank_pairs:
        if (pair[0], pair[1]) in set:
            continue
        else:
            set[(pair[0], pair[1])] = 1
        if pair[1] in ret_pairs:
            ret_pairs[pair[1]] += pair[2]
        else:
            ret_pairs[pair[1]] = pair[2]
    ret_list = list(ret_pairs.items())
    ret_list.sort(key=lambda x : -x[1])
    return ret_list


# Assume the website database has already been populated by relation_graph.py
if __name__ == '__main__':
    fos_data = mysql.connector.connect(
        host="104.198.163.126",
        user="root",
        password="yEBpALG6zHDoCFLn",
        database="project"
    )
    fos_cursor = fos_data.cursor()

    # to return a rank list of related professors with their closeness
    # given a single professors' name (id)
    print(related_professors("Andrew Zisserman", fos_cursor))

    # to return a rank list of similar professors with their weights
    # given a list of keyword strings
    print(rank_list_of_professors(["algorithm", "security"], fos_cursor))