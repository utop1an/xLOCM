import itertools
import os
from tabulate import tabulate
from IPython.display import display, Markdown
import networkx as nx
import pandas as pd
import string
from ipycytoscape import *

def print_table(matrix):
    display(tabulate(matrix, headers='keys', tablefmt='html'))

    # utils
def findsubsets(S,m):
    return set(itertools.combinations(S, m))
    
def printmd(string):
    display(Markdown(string))

def check_well_formed(
        subset_df
    ):
    # got the adjacency matrix subset
    df = subset_df.copy()
    well_formed_flag = True
    
    
    if (df == 0).all(axis=None): # all elements are zero
        well_formed_flag = False
        
    # for particular adjacency matrix's copy, loop over all pairs of rows
    for i in range(0, df.shape[0]-1):
        for j in range(i + 1, df.shape[0]):
            idx1, idx2 = i, j
            row1, row2 = df.iloc[idx1, :], df.iloc[idx2, :]  # we have now all pairs of rows
            common_values_flag = False  # for each two rows we have a common_values_flag
            # if there is a common value between two rows, turn common value flag to true
            for col in range(row1.shape[0]):
                if row1.iloc[col] > 0 and row2.iloc[col] > 0:
                    common_values_flag = True
                    break
        
            if common_values_flag:
                for col in range(row1.shape[0]): # check for holes if common value
                    if row1.iloc[col] > 0 and row2.iloc[col] == 0:
                        well_formed_flag = False
                    elif row1.iloc[col] == 0 and row2.iloc[col] > 0:
                        well_formed_flag = False
    
    if not well_formed_flag:
        return False
    elif well_formed_flag:
        return True
    
def check_valid(
        subset_df,
        consecutive_transitions_per_sort
    ):
    df = subset_df.copy()
    # for particular adjacency matrix's copy, loop over all pairs of rows
    for i in range(df.shape[0]):
        for j in range(df.shape[0]):
            if df.iloc[i,j] > 0:
                valid_val_flag = False
                ordered_pair = (df.index[i], df.columns[j])
                for ct_list in consecutive_transitions_per_sort:
                    for ct in ct_list:
                        if ordered_pair == ct:
                            valid_val_flag=True
                # if after all iteration ordered pair is not found, mark the subset as invalid.
                if not valid_val_flag:
                    return False
                
    # return True if all ordered pairs found.
    return True

def read_action_seqs(filename):
    '''
    Read the input data and return list of action sequences.
    Each sequence is a list of action-argumentlist tuples.
    '''
    sequences = []
    filepath = os.getcwd() + '/data/' + filename
    file = open(filepath, 'r')
    for seq in file:
        actions = []
        arguments = []
        if seq and not seq.isspace() and len(seq)>1:
            sequence = seq.rstrip("\n\r").lstrip("\n\r").lower() 
            action_defs = sequence.split("),")

            for action_def in action_defs:
                action = action_def.split('(')[0].strip(")\n\r").strip()
                argument = action_def.split('(')[1].strip(")\n\r")
                actions.append(action.translate(str.maketrans('', '', string.punctuation)))
                argument_list = argument.split(',')
                argument_list = [x.strip() for x in argument_list]
                #argument_list.insert(0,'zero')
                arguments.append(argument_list)
                
            
            actarg_tuples = zip(actions,arguments)
            sequences.append(list(actarg_tuples))
    return sequences

def print_sequences(sequences):
    for seq in sequences:
        for index,action in enumerate(seq):
            print(str(index) + ": " + str(action))
        print("="*50)

def empty_directory(folder):
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            # elif os.path.isdir(file_path): shutil.rmtree(file_path)
        except Exception as e:
            print(e)

def plot_cytographs(graphs,sort_names, aml):
    cytoscapeobs = []
    for index, G in enumerate(graphs):
            cytoscapeobj = CytoscapeWidget()
            cytoscapeobj.graph.add_graph_from_networkx(G)
            edge_list = list()
            for source, target, data in G.edges(data=True):
                edge_instance = Edge()
                edge_instance.data['source'] = source
                edge_instance.data['target'] = target
                for k, v in data.items():
                    cyto_attrs = ['group', 'removed', 'selected', 'selectable',
                        'locked', 'grabbed', 'grabbable', 'classes', 'position', 'data']
                    if k in cyto_attrs:
                        setattr(edge_instance, k, v)
                    else:
                        edge_instance.data[k] = v
                    edge_list.append(edge_instance)
            cytoscapeobj.graph.edges = edge_list
#             cytoscapeobj.graph.add_graph_from_df(aml[index],aml[index].columns.tolist())
            cytoscapeobs.append(cytoscapeobj)
#             print(cytoscapeobj)
            printmd('## class **'+sort_names[index]+'**')
            
            print_table(aml[index])
    #         print("Nodes:{}".format(G.nodes()))
    #         print("Edges:{}".format(G.edges()))
            cytoscapeobj.set_style([{
                            'width':400,
                            'height':400,

                            'selector': 'node',
                            'style': {
                                'label': 'data(id)',
                                'font-family': 'helvetica',
                                'font-size': '8px',
                                'background-color': '#11479e',
                                'height':'10px',
                                'width':'10px',


                                }

                            },
                            {
                            'selector': 'node:parent',
                            'css': {
                                'background-opacity': 0.333,
                                'background-color': '#bbb'
                                }
                            },
                            {
                            'selector': '$node > node',
                            'css': {
                                'padding-top': '10px',
                                'padding-left': '10px',
                                'padding-bottom': '10px',
                                'padding-right': '10px',
                                'text-valign': 'top',
                                'text-halign': 'center',
                                'background-color': '#bbb'
                              }
                            },
                           {
                                'selector': 'edge',

                                'style': {
                                    'label':'data(weight)',
                                    'width': 1,
                                    'line-color': '#9dbaea',
                                    'target-arrow-shape': 'triangle',
                                    'target-arrow-color': '#9dbaea',
                                    'arrow-scale': 0.5,
                                    'curve-style': 'bezier',
                                    'font-family': 'helvetica',
                                    'font-size': '8px',
                                    'text-valign': 'top',
                                    'text-halign':'center'
                                }
                            },
                            ])
            cytoscapeobj.max_zoom = 4.0
            cytoscapeobj.min_zoom = 0.5
            display(cytoscapeobj)
    return cytoscapeobs


def plot_cytographs_fsm(graph, domain_name):
    cytoscapeobj = CytoscapeWidget()
    cytoscapeobj.graph.add_graph_from_networkx(graph)
    edge_list = list()
    for source, target, data in graph.edges(data=True):
        edge_instance = Edge()
        edge_instance.data['source'] = source
        edge_instance.data['target'] = target
        for k, v in data.items():
            cyto_attrs = ['group', 'removed', 'selected', 'selectable',
                'locked', 'grabbed', 'grabbable', 'classes', 'position', 'data']
            if k in cyto_attrs:
                setattr(edge_instance, k, v)
            else:
                edge_instance.data[k] = v
            edge_list.append(edge_instance)

    cytoscapeobj.graph.edges = edge_list
#     print("Nodes:{}".format(graph.nodes()))
#     print("Edges:{}".format(graph.edges()))
    cytoscapeobj.set_style([{
                    'width':400,
                    'height':500,

                    'selector': 'node',
                    'style': {
                        'label': 'data(id)',
                        'font-family': 'helvetica',
                        'font-size': '8px',
                        'background-color': '#11479e',
                        'height':'10px',
                        'width':'10px',


                        }

                    },
                    {
                    'selector': 'node:parent',
                    'css': {
                        'background-opacity': 0.333,
                        'background-color': '#bbb'
                        }
                    },
                    {
                    'selector': '$node > node',
                    'css': {
                        'padding-top': '10px',
                        'padding-left': '10px',
                        'padding-bottom': '10px',
                        'padding-right': '10px',
                        'text-valign': 'top',
                        'text-halign': 'center',
                        'background-color': '#bbb'
                      }
                    },
                   {
                        'selector': 'edge',

                        'style': {
                            'label':'data(weight)',
                            'width': 1,
                            'line-color': '#9dbaea',
                            'target-arrow-shape': 'triangle',
                            'target-arrow-color': '#9dbaea',
                            'arrow-scale': 0.5,
                            'curve-style': 'bezier',
                            'font-family': 'helvetica',
                            'font-size': '8px',
                            'text-valign': 'top',
                            'text-halign':'center'
                        }
                    },
                    ])
    cytoscapeobj.max_zoom = 2.0
    cytoscapeobj.min_zoom = 0.5
    display(cytoscapeobj)