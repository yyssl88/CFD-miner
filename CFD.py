import os

import pandas as pd


class Node:
    def __init__(self, y, x, candidates):
        self.y = y
        self.x = x
        self.candidates = candidates
        self.constant_predicates = {}

    def delete_candidate(self, delete_column):
        candidates = []
        for column in self.candidates:
            if column == delete_column:
                continue
            candidates.append(column)
        self.candidates = candidates

    def create_constant_predicates(self, constant_predicates):
        for column, values in constant_predicates.items():
            if column == self.y:
                continue
            self.constant_predicates[column] = values


class Rule:
    def __init__(self, y, x, ree, support, confidence):
        self.y = y
        self.x = x
        self.check_error = []
        self.correct_error = {}
        self.constant_predicates = {}
        self.ree = ree
        self.support = support
        self.confidence = confidence

    def cal_error(self, df):
        x = self.x
        y = self.y
        e = {}
        c = []
        df_ = df
        for column, value in self.constant_predicates.items():
            df_ = df_[df_[column] == value]
        for name, group in df_.groupby(x):
            most_common_y = group[y].mode()[0]
            other_indices = group[group[y] != most_common_y].index.tolist()
            c += other_indices
            if most_common_y in e:
                e[most_common_y] += other_indices
            else:
                e[most_common_y] = other_indices
        #             print(f"{y}={most_common_y}:{other_indices}")
        self.check_error = c
        self.correct_error = e


def select_enum_columns(df, k):
    columns = list(df.columns)
    enum_columns = []
    for column in columns:
        if k >= len(df[column].value_counts()) > 1:
            enum_columns.append(column)
    return enum_columns


def get_x_columns(y, enum_columns):
    x_columns = []
    for column in enum_columns:
        if column == y:
            continue
        x_columns.append(column)
    return x_columns


def cal_nodes(df, nodes):
    x_supp_s, xy_supp_s = [], []
    for node in nodes:
        x_supp, xy_supp = cal_node(df, node)
        x_supp_s.append(x_supp)
        xy_supp_s.append(xy_supp)
    return x_supp_s, xy_supp_s


def cal_node(df, node):
    y = node.y
    x = node.x
    x_supp, xy_supp = 0, 0
    x_group_size = len(df.groupby(x).size())
    if x_group_size == 0:
        return x_supp, xy_supp
    x_group = list(df.groupby(x).size().reset_index(name='counts')['counts'])
    for count in x_group:
        x_supp += count * (count - 1)
    xy_columns = list(x)
    xy_columns.append(y)
    #     print(xy_columns)
    xy_group = list(df.groupby(xy_columns).size().reset_index(name='counts')['counts'])
    for count in xy_group:
        xy_supp += count * (count - 1)
    return x_supp, xy_supp


def cal_tree(root_node, df, conf, constant_predicates):
    rules = []
    tree_level = conf['tree_level']
    support, confidence = conf['support'], conf['confidence']
    y = root_node.y
    row_size = float(len(df) * (len(df) - 1))
    cur_layer = [root_node]
    next_layer = []
    for i in range(tree_level):
        nodes = []
        for node in cur_layer:
            for j in range(len(node.candidates)):
                add_column = node.candidates[j]
                x = list(node.x)
                candidates = node.candidates[j + 1:]
                x.append(add_column)
                son_node = Node(y, x, candidates)
                nodes.append(son_node)
        x_supp_s, xy_supp_s = cal_nodes(df, nodes)
        for j in range(len(nodes)):
            son_node = nodes[j]
            rule_supp = float(xy_supp_s[j]) / row_size
            if x_supp_s[j] != 0:
                rule_conf = float(xy_supp_s[j]) / float(x_supp_s[j])
            else:
                rule_conf = 0
            if rule_supp >= support and rule_conf >= confidence:
                ree = create_ree(son_node)
                print(f"find rule:{ree},supp:{rule_supp}, conf:{rule_conf}")
                rule = Rule(son_node.y, son_node.x, ree, rule_supp, rule_conf)
                rules.append(rule)
                for node in next_layer:
                    node.delete_candidate(son_node.x[-1])
            elif rule_supp < support:
                for node in next_layer:
                    node.delete_candidate(son_node.x[-1])
            else:
                next_layer.append(son_node)
                cfd_rule_info = cal_CFD(df, son_node, constant_predicates)
                for column, values in cfd_rule_info.items():
                    for value, info in values.items():
                        rule_supp = float(info[1]) / row_size
                        if info[0] != 0:
                            rule_conf = float(info[1]) / float(info[0])
                        if rule_supp >= support and rule_conf >= confidence:
                            ree = create_ree(son_node, column, value)
                            print(f"find rule:{ree},supp:{rule_supp}, conf:{rule_conf}")
                            rule = Rule(son_node.y, son_node.x, ree, rule_supp, rule_conf)
                            rule.constant_predicates = {column: value}
                            rules.append(rule)
        cur_layer = next_layer
        next_layer = []
    return rules


def create_ree(node, column=None, value=None):
    ree = '^'.join([f"t0.{x}=t1.{x}" for x in node.x])
    if column is not None and value is not None:
        ree += f"^t0.{column}='{value}'^t1.{column}='{value}'"
    ree += f"->t0.{node.y}=t1.{node.y}"
    return ree


def create_constant_predicates(df, enum_columns):
    constant_predicates = {}
    for column in enum_columns:
        values = list(df[column].unique())
        constant_predicates[column] = values
    return constant_predicates


def cal_CFD(df, node, constant_predicates):
    node.create_constant_predicates(constant_predicates)
    result = {}
    for column, values in node.constant_predicates.items():
        result[column] = {}
        for value in values:
            df_ = df[df[column] == value]
            x_supp, xy_supp = cal_node(df_, node)
            result[column][value] = [x_supp, xy_supp]
    return result


def check_error_cfd(req_json):
    data_path = req_json['data_path']
    output_path = req_json['output_path']
    try:
        os.makedirs(output_path)
        print(f"Directory '{output_path}' created。")
    except OSError as error:
        print(f"create directory '{output_path}' failed: {error}")
    conf = {
        "enum_k": 10,
        "support": 0.00005,
        "confidence": 0.8,
        "tree_level": 3
    }
    df_data = pd.read_csv(data_path)
    enum_columns = select_enum_columns(df_data, conf['enum_k'])
    print(enum_columns)
    constant_predicates = create_constant_predicates(df_data, enum_columns)
    print(constant_predicates)

    rules = []
    for y in enum_columns:
        x_columns = get_x_columns(y, enum_columns)
        root_node = Node(y, [], x_columns)
        rules += cal_tree(root_node, df_data, conf, constant_predicates)
    print(f"find {len(rules)} rules")

    df_rule = pd.DataFrame()
    rees, supports, confidences = [], [], []
    for rule in rules:
        rees.append(rule.ree)
        supports.append(rule.support)
        confidences.append(rule.confidence)
    df_rule['rule'] = rees
    df_rule['support'] = supports
    df_rule['confidence'] = confidences
    df_rule.to_csv(os.path.join(output_path, 'rules.csv'), index=False)

    return {"message": "finish", "data": {"rule size": len(rules)}}


if __name__ == "__main__":
    json = {'data_path': './data/hospital_dirty_cfd.csv',
            'output_path': ''}
    check_error_cfd(json)
