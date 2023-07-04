from pathlib import Path
from pysurfparcel.procedures.atlas2subject.register_parcellation import (
    RegisterParcellation,
)
from pysurfparcel.reoncall.layout.layout import Layout
from qsipost.parcellations.atlases.atlas import Atlas
from pysurfparcel.interfaces.freesurfer.preprocess import (
    MRIsAnatomicalStats,
    MRIsCALabel,
)
from freesurfer_statistics.cortical_stats import CorticalStats


class RegisterCorticalParcellation(RegisterParcellation):
    """
    Register the cortical parcellation to the subject space
    """

    REQUIRED_PARCELLATION_KEYS = ["rh_gcs", "lh_gcs", "lut"]
    REQUIRED_LAYOUT_KEYS = [
        "cortex_label",
        "surfreg",
    ]

    # init super class
    def __init__(
        self, layout: Layout, parcellation: Atlas, seed: int = 42
    ) -> None:
        super().__init__(layout, parcellation, seed)

    def map_to_hemisphere(self, hemi: str, force: bool = False) -> Path:
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
        if hemi == "lh":
            gcs = self.parcellation.lh_gcs
        elif hemi == "rh":
            gcs = self.parcellation.rh_gcs
        else:
            raise ValueError(f"Invalid hemisphere: {hemi}")
        out_file = (
            self.layout.subject_dir
            / "label"
            / f"{hemi}.{self.parcellation.name}.annot"
        )
        if not out_file.exists() or force:
            ca_label = MRIsCALabel()
            ca_label.inputs.hemisphere = hemi
            ca_label.inputs.classifier = str(gcs)
            ca_label.inputs.subject_id = self.layout.subject_id
            ca_label.inputs.canonsurf = str(
                self.layout.outputs["surfreg"][hemi]
            )
            ca_label.inputs.subjects_dir = str(self.layout.subject_dir.parent)
            ca_label.inputs.label = str(
                self.layout.outputs["cortex_label"][hemi]
            )
            ca_label.inputs.seed = self.seed
            ca_label.inputs.out_file = str(out_file)
            ca_label.run()
        return out_file

    def calculate_parcellation_statistics(
        self, hemi: str, force: bool = False
    ) -> Path:
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
            / f"{hemi}.{self.parcellation.name}.stats"
        )
        if not out_file.exists() or force:
            stats = MRIsAnatomicalStats()
            stats.inputs.mgz = True
            stats.inputs.hemisphere = hemi
            stats.inputs.subject_id = self.layout.subject_id
            stats.inputs.subjects_dir = str(self.layout.subject_dir.parent)
            stats.inputs.annot = str(
                self.layout.outputs["cortical_annotation"][hemi]
            )
            stats.inputs.cortex = str(
                self.layout.outputs["cortex_label"][hemi]
            )
            stats.inputs.out_file = str(out_file)
            stats.run()
        return out_file

    def convert_stats_to_dataframe(
        self, hemi: str, force: bool = True
    ) -> Path:
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
            / f"{hemi}.{self.parcellation.name}.roi_stats.csv"
        )
        out_global_stats = (
            self.layout.subject_dir
            / "stats"
            / f"{hemi}.{self.parcellation.name}.global_stats.csv"
        )
        if (
            (not out_regionwise_stats.exists())
            or (not out_global_stats.exists())
            or force
        ):
            stats = CorticalStats(
                str(self.layout.outputs["cortical_stats"][hemi])
            )
            stats.structural_measurements.to_csv(out_regionwise_stats)
            stats.whole_brain_measurements.to_csv(out_global_stats)
        return out_regionwise_stats, out_global_stats

    def run(self, force: bool = True) -> None:
        """
        Run the registration

        Parameters
        ----------
        force : bool, optional
            Force overwrite of existing files, by default True
        """
        self.layout.outputs["cortical_annotation"] = {}
        self.layout.outputs["cortical_stats"] = {}
        self.layout.outputs["cortical_stats_df"] = {}
        for hemi in ["lh", "rh"]:
            self.layout.outputs["cortical_annotation"][
                hemi
            ] = self.map_to_hemisphere(hemi, force=force)
            self.layout.outputs["cortical_stats"][
                hemi
            ] = self.calculate_parcellation_statistics(hemi, force=force)
            hemi_df, hemi_global_df = self.convert_stats_to_dataframe(
                hemi, force=force
            )
            self.layout.outputs["cortical_stats_df"][hemi] = {
                "regional": hemi_df,
                "global": hemi_global_df,
            }
