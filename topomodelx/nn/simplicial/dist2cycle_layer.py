"""Dist2Cycle Network Layer."""
import torch
import torch.nn as nn

from topomodelx.base.aggregation import Aggregation


class Dist2CycleLayer(torch.nn.Module):
    """Layer of Dist2Cycle [1]_."""

    def __init__(
        self,
        channels,
    ) -> None:
        super().__init__()
        self.channels = channels
        # feature learning
        self.fc_neigh = nn.Linear(channels, 1, bias=True)
        self.aggr_on_edges = Aggregation(aggr_func="sum", update_func="relu")
        # need to support for other update functions like leaky relu
        # which is main for dist2Cycle

    def reset_parameters(self) -> None:
        r"""Reset learnable parameters."""
        fc_nonlin = "relu"
        fc_alpha = 0.0
        self.fc_neigh.reset_parameters()

        nn.init.kaiming_uniform_(
            self.fc_neigh.weight, a=fc_alpha, nonlinearity=fc_nonlin
        )

    def forward(self, x_e, Linv, adjacency):
        r"""Forward pass.

        .. math::
            \begin{align*}
            &🟥 \quad m^{(1 \rightarrow 1)}\_{y \rightarrow x}  = (A \odot (I + L\downarrow)^+{xy}) \cdot h_{y}^{t,(1)}\cdot \Theta^t\\
            &🟧 \quad m_x^{(1 \rightarrow 1)}  = \sum_{y \in \mathcal{L}\_\downarrow(x)} m_{y \rightarrow x}^{(1 \rightarrow 1)}\\
            &🟩 \quad m_x^{(1)}  = m^{(1 \rightarrow 1)}_x\\
            &🟦 \quad h_x^{t+1,(1)} = \sigma(m_{x}^{(1)})
            \end{align*}

        References
        ----------
        .. [1] Papillon, Sanborn, Hajij, Miolane.
            Equations of topological neural networks (2023).
            https://github.com/awesome-tnns/awesome-tnns/

        Parameters
        ----------
        x: torch.Tensor, shape = (n_nodes, channels)
            Input features on the edges of the simplicial complex.
        incidence_1 : torch.sparse, shape = (n_nodes, n_edges)
            Incidence matrix :math:`B_1` mapping edges to nodes.
        adjacency_0 : torch.sparse, shape = (n_nodes, n_nodes)
            Adjacency matrix :math:`A_0^{\uparrow}` mapping nodes to nodes via edges.

        Returns
        -------
        torch.Tensor, shape = (n_nodes, channels)
            Output features on the nodes of the simplicial complex.
        """
        x_e = adjacency * Linv
        x_e = self.aggr_on_edges([x_e])
        rst = self.fc_neigh(x_e)
        return rst
