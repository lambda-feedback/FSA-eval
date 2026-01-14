from .fsa import FSA, Transition

import matplotlib.pyplot as plt
import networkx as nx

# plt is not thread safe, but graphviz is harder to install for cross-env compiles
# this is sequentially safe anyway
# notice that if relative path, it is relative to where you execute the code, 
# and invalid fsa always look weird as nx+plt cannot find a equilibrium
def draw_fsa(fsa:FSA, show=False, save=True, filename="./fsa.png"):
    # 1. Initialize Graph and collect all possible states
    G = nx.MultiDiGraph()
    
    # Start with declared states, but use a set to allow for "orphans"
    all_states = set(fsa.states)
    
    # Always include initial and accept states in the set (even if missing from fsa.states)
    if fsa.initial_state:
        all_states.add(fsa.initial_state)
    all_states.update(fsa.accept_states)
    
    # 2. Add Transitions and discover states used in transitions
    for t in fsa.transitions:
        all_states.add(t.from_state)
        all_states.add(t.to_state)
        G.add_edge(t.from_state, t.to_state, label=t.symbol)

    # Ensure all discovered states are in the graph
    G.add_nodes_from(all_states)

    # 3. Layout and Figure
    # Kamada-Kawai is more stable than Spring for state machines
    pos = nx.kamada_kawai_layout(G)
    plt.figure(figsize=(10, 7))

    # 4. Draw Nodes with specific styling
    for node in G.nodes():
        # Default Style
        color = 'skyblue'
        linewidth = 1.0
        edgecolor = 'black'
        label_suffix = ""

        # Initial State Styling (Green fill)
        if node == fsa.initial_state:
            color = '#90ee90'  # Light green
            label_suffix = "\n(start)"
            
        # Accept State Styling (Double-circle effect/Thick border)
        if node in fsa.accept_states:
            linewidth = 4.0
            edgecolor = '#ff4500' # Orange-red border for visibility

        nx.draw_networkx_nodes(
            G, pos, 
            nodelist=[node],
            node_color=color,
            edgecolors=edgecolor,
            linewidths=linewidth,
            node_size=2500
        )

    # 5. Draw Edges (Arcing handles multi-edges/non-determinism)
    nx.draw_networkx_edges(
        G, pos, 
        arrowstyle='->', 
        arrowsize=25, 
        connectionstyle='arc3,rad=0.15', 
        edge_color='gray'
    )

    # 6. Edge and Node Labels
    # Use bracket notation for the 'label' key in the data dict
    edge_labels = {(u, v): d['label'] for u, v, k, d in G.edges(data=True, keys=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=10)
    
    node_labels = {node: f"{node}{'(start)' if node == fsa.initial_state else ''}" for node in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=11, font_weight='bold')

    plt.title(f"FSA:\n(Accept states marked with thick borders)")
    plt.axis('off')

    # 7. Save and Clean Up
    if save:
        plt.savefig(filename, bbox_inches='tight')
    
    if show:
        plt.show()

    plt.close()
    print(f"Process complete. Memory flushed.")

def make_fsa(states, alphabet, transitions, initial, accept):
    return FSA(
        states=states,
        alphabet=alphabet,
        transitions=[
            Transition(**t) for t in transitions
        ],
        initial_state=initial,
        accept_states=accept,
    )

if __name__ == "__main__":
    fsa = make_fsa(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[
                {"from_state": "q0", "to_state": "q0", "symbol": "a"},
                {"from_state": "q0", "to_state": "q1", "symbol": "a"},  # Non-deterministic
            ],
            initial="q0",
            accept=["q1"],
        )
    draw_fsa(fsa, False, True, "./valid.png")
    fsa = make_fsa(
            states=["q0"],
            alphabet=["a"],
            transitions=[],
            initial="q0",
            accept=["q1"],  # q1 is not in states
        )
    draw_fsa(fsa, False, True, "./invalid.png")
    