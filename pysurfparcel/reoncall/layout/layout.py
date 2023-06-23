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
        self.subject_id = self.subject_dir.name
        self.parse_run_metadata()
        self.outputs = self.collect_outputs()

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

    def collect_outputs(self, output_spec: dict = OUTPUTS) -> dict:
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
        outputs = {}
        for output_name, output_path in output_spec.items():
            outputs[output_name] = None
            results = list(self.subject_dir.glob(output_path))
            if len(results) == 1:
                outputs[output_name] = results[0]
            elif len(results) > 1:
                hemis = {}
                for result in results:
                    if result.name.startswith("lh"):
                        hemis["lh"] = result
                    elif result.name.startswith("rh"):
                        hemis["rh"] = result
                outputs[output_name] = hemis
        return outputs
