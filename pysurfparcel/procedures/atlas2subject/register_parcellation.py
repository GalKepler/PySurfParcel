from pathlib import Path
from pysurfparcel.reoncall.layout.layout import Layout
from qsipost.parcellations.atlases.atlas import Atlas
from pysurfparcel.interfaces.freesurfer.preprocess import (
    MRIsAnatomicalStats,
    MRIsCALabel,
)
from freesurfer_statistics.cortical_stats import CorticalStats


class RegisterParcellation:
    """
    Register the cortical parcellation to the subject space
    """

    REQUIRED_PARCELLATION_KEYS = []
    REQUIRED_LAYOUT_KEYS = []

    def __init__(
        self, layout: Layout, parcellation: Atlas, seed: int = 42
    ) -> None:
        self.layout = layout
        self.parcellation = parcellation
        self.seed = seed
        self.validate_required_inputs()

    def validate_required_inputs(self):
        """
        Validate that the required inputs for both the layout and parcellation are present.
        """
        for key in self.REQUIRED_LAYOUT_KEYS:
            if self.layout.outputs.get(key) is None:
                raise FileNotFoundError(
                    f"Missing required recon-all output: {key}"
                )
        for key in self.REQUIRED_PARCELLATION_KEYS:
            if not hasattr(self.parcellation, key):
                raise FileNotFoundError(
                    f"Missing required parcellation file: {key}"
                )

    def run(self, force: bool = True) -> None:
        """
        Run the registration

        Parameters
        ----------
        force : bool, optional
            Force overwrite of existing files, by default True
        """
        raise NotImplementedError(
            "This method should be implemented in a subclass"
        )
