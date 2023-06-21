from pathlib import Path
from typing import Union
from pysurfparcel.reoncall.static.outputs import OUTPUTS


class Layout:
    """
    Class for parsing and storing the output of Freesurfer's recon-all command.
    """

    METADATA_DIRNAME = "scripts"

    def __init__(self, subject_dir: Union[str, Path]):
        """
        Class for parsing and storing the output of Freesurfer's recon-all command.

        Parameters
        ----------
        subject_dir : Union[str, Path]
            Path to the subject directory containing the output of Freesurfer's recon-all command.
        """
        self.subject_dir = Path(subject_dir)
        self.parse_run_metadata()

    def parse_run_metadata(self):
        """
        Parse the run metadata from the subject directory.
        """
        self.run_metadata = {}
        metadata_dir = self.subject_dir / self.METADATA_DIRNAME
        # read freesurfer's version from recon-all.env file
        with open(metadata_dir / "recon-all.env", "r") as f:
            for line in f:
                if line.startswith("FS_RECON_VERSION"):
                    self.run_metadata["freesurfer_version"] = (
                        line.split("=")[1].split(" ")[0].strip()
                    )
                    break
        # read the command line from unknown-args.txt file
        with open(metadata_dir / "unknown-args.txt", "r") as f:
            self.run_metadata["command_line"] = f.read().replace("\n", " ")

    def collect_outputs(self, outputs: dict = OUTPUTS) -> dict:
        """
        Collect the outputs specified in the outputs dictionary.

        Parameters
        ----------
        outputs : dict, optional
            Dictionary of outputs to collect, by default OUTPUTS

        Returns
        -------
        dict
            Dictionary of outputs collected
        """
        self.outputs = {}
        for output_name, output_path in outputs.items():
            result = self.subject_dir / output_path
            self.outputs[output_name] = result if result.exists() else None
        return self.outputs
