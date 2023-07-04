from pathlib import Path
from pysurfparcel.procedures.atlas2subject.register_parcellation import (
    RegisterParcellation,
)
from pysurfparcel.reoncall.layout.layout import Layout
from qsipost.parcellations.atlases.atlas import Atlas
from pysurfparcel.interfaces.freesurfer.preprocess import (
    MRISegStats,
)
from nipype.interfaces.freesurfer import CALabel
from freesurfer_statistics.subcortical_stats import SubCorticalStats


# from freesurfer_statistics.subcortical_stats import SubcorticalStats


class RegisterSubCorticalParcellation(RegisterParcellation):
    """
    Register the cortical parcellation to the subject space
    """

    REQUIRED_PARCELLATION_KEYS = ["subcortex_gcs", "lut"]
    REQUIRED_LAYOUT_KEYS = ["brain", "talairach_xfm", "norm"]

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

    def map_to_subject(self, force: bool = False) -> Path:
        """
        Map parcelation to a single hemisphere

        Parameters
        ----------
        hemi : str
            Hemisphere to map
        force : bool, optional
            Force overwrite of existing files, by default False

        Returns
        -------
        Path
            Path to the mapped parcellation
        """
        out_file = (
            self.layout.subject_dir
            / "mri"
            / f"subcortex.{self.parcellation.name}.mgz"
        )
        if not out_file.exists() or force:
            ca_label = CALabel()
            ca_label.inputs.in_file = str(self.layout.outputs["brain"])
            ca_label.inputs.template = str(self.parcellation.subcortex_gcs)
            ca_label.inputs.transform = str(
                self.layout.outputs["talairach_xfm"]
            )
            ca_label.inputs.out_file = str(out_file)
            ca_label.inputs.subjects_dir = str(self.layout.subject_dir.parent)
            ca_label.run()
        return out_file

    def calculate_parcellation_statistics(self, force: bool = False) -> Path:
        """
        Calculate parcellation statistics

        Parameters
        ----------
        hemi : str
            Hemisphere to map
        force : bool, optional
            Force overwrite of existing files, by default False

        Returns
        -------
        Path
            Path to the calculated statistics
        """
        out_file = (
            self.layout.subject_dir
            / "stats"
            / f"subcortex.{self.parcellation.name}.stats"
        )
        if not out_file.exists() or force:
            stats = MRISegStats()
            stats.inputs.subjects_dir = str(self.layout.subject_dir.parent)
            stats.inputs.segmentation = str(
                self.layout.outputs["subcortex_segmentation"]
            )
            stats.inputs.ctab = str(self.parcellation.lut)
            stats.inputs.excludeid = [0]
            stats.inputs.partial_volume = str(self.layout.outputs["norm"])
            stats.inputs.out_file = str(out_file)
            stats.run()
        return out_file

    def convert_stats_to_dataframe(self, force: bool = True) -> Path:
        """
        Convert the cortical statistics to a dataframe

        Parameters
        ----------
        hemi : str
            Hemisphere to map
        force : bool, optional
            Force overwrite of existing files, by default True

        Returns
        -------
        Path
            Path to the dataframe
        """
        out_regionwise_stats = (
            self.layout.subject_dir
            / "stats"
            / f"subcortex.{self.parcellation.name}.roi_stats.csv"
        )
        if not out_regionwise_stats.exists() or force:
            stats = SubCorticalStats(
                str(self.layout.outputs["subcortex_stats"])
            )
            stats.structural_measurements.to_csv(out_regionwise_stats)
        return out_regionwise_stats

    def run(self, force: bool = True) -> None:
        """
        Run the registration

        Parameters
        ----------
        force : bool, optional
            Force overwrite of existing files, by default True
        """
        self.layout.outputs["subcortex_segmentation"] = {}
        self.layout.outputs["subcortex_stats"] = {}
        self.layout.outputs["subcortex_stats_df"] = {}
        self.layout.outputs["subcortex_segmentation"] = self.map_to_subject(
            force=force
        )
        self.layout.outputs[
            "subcortex_stats"
        ] = self.calculate_parcellation_statistics(force=force)
        hemi_df = self.convert_stats_to_dataframe(force=force)
        self.layout.outputs["subcortex_stats_df"] = {"regional": hemi_df}
