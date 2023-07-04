import os

from nipype.interfaces.base import (
    TraitedSpec,
    File,
    traits,
)
from nipype.interfaces.freesurfer.base import (
    FSTraitedSpecOpenMP,
    FSCommandOpenMP,
)
from nipype.interfaces.freesurfer.utils import copy2subjdir


class MRIsCALabelInputSpec(FSTraitedSpecOpenMP):
    # required
    subject_id = traits.String(
        "subject_id",
        argstr="%s",
        position=-5,
        usedefault=True,
        mandatory=True,
        desc="Subject name or ID",
    )
    hemisphere = traits.Enum(
        "lh",
        "rh",
        argstr="%s",
        position=-4,
        mandatory=True,
        desc="Hemisphere ('lh' or 'rh')",
    )
    canonsurf = File(
        argstr="%s",
        position=-3,
        mandatory=True,
        exists=True,
        desc="Input canonical surface file",
    )
    classifier = File(
        argstr="%s",
        position=-2,
        mandatory=True,
        exists=True,
        desc="Classifier array input file",
    )
    smoothwm = File(
        mandatory=False,
        exists=True,
        desc="implicit input {hemisphere}.smoothwm",
    )
    curv = File(
        mandatory=False, exists=True, desc="implicit input {hemisphere}.curv"
    )
    sulc = File(
        mandatory=False, exists=True, desc="implicit input {hemisphere}.sulc"
    )
    out_file = File(
        argstr="%s",
        position=-1,
        exists=False,
        name_source=["hemisphere"],
        keep_extension=True,
        hash_files=False,
        name_template="%s.aparc.annot",
        desc="Annotated surface output file",
    )
    # optional
    label = File(
        argstr="-l %s",
        exists=True,
        desc="Undocumented flag. Autorecon3 uses ../label/{hemisphere}.cortex.label as input file",
    )
    aseg = File(
        argstr="-aseg %s",
        exists=True,
        desc="Undocumented flag. Autorecon3 uses ../mri/aseg.presurf.mgz as input file",
    )
    seed = traits.Int(argstr="-seed %d", desc="")
    copy_inputs = traits.Bool(
        desc="Copies implicit inputs to node directory "
        + "and creates a temp subjects_directory. "
        + "Use this when running as a node"
    )


class MRIsCALabelOutputSpec(TraitedSpec):
    out_file = File(exists=False, desc="Output volume from MRIsCALabel")


class MRIsCALabel(FSCommandOpenMP):
    """
    For a single subject, produces an annotation file, in which each
    cortical surface vertex is assigned a neuroanatomical label.This
    automatic procedure employs data from a previously-prepared atlas
    file. An atlas file is created from a training set, capturing region
    data manually drawn by neuroanatomists combined with statistics on
    variability correlated to geometric information derived from the
    cortical model (sulcus and curvature). Besides the atlases provided
    with FreeSurfer, new ones can be prepared using mris_ca_train).

    Examples
    ========

    >>> from nipype.interfaces import freesurfer
    >>> ca_label = freesurfer.MRIsCALabel()
    >>> ca_label.inputs.subject_id = "test"
    >>> ca_label.inputs.hemisphere = "lh"
    >>> ca_label.inputs.canonsurf = "lh.pial"
    >>> ca_label.inputs.curv = "lh.pial"
    >>> ca_label.inputs.sulc = "lh.pial"
    >>> ca_label.inputs.classifier = "im1.nii" # in pracice, use .gcs extension
    >>> ca_label.inputs.smoothwm = "lh.pial"
    >>> ca_label.cmdline
    'mris_ca_label test lh lh.pial im1.nii lh.aparc.annot'
    """

    _cmd = "mris_ca_label"
    input_spec = MRIsCALabelInputSpec
    output_spec = MRIsCALabelOutputSpec

    def run(self, **inputs):
        if self.inputs.copy_inputs:
            self.inputs.subjects_dir = os.getcwd()
            if "subjects_dir" in inputs:
                inputs["subjects_dir"] = self.inputs.subjects_dir
            copy2subjdir(self, self.inputs.canonsurf, folder="surf")
            copy2subjdir(
                self,
                self.inputs.smoothwm,
                folder="surf",
                basename="{0}.smoothwm".format(self.inputs.hemisphere),
            )
            copy2subjdir(
                self,
                self.inputs.curv,
                folder="surf",
                basename="{0}.curv".format(self.inputs.hemisphere),
            )
            copy2subjdir(
                self,
                self.inputs.sulc,
                folder="surf",
                basename="{0}.sulc".format(self.inputs.hemisphere),
            )

        # The label directory must exist in order for an output to be written
        label_dir = os.path.join(
            self.inputs.subjects_dir, self.inputs.subject_id, "label"
        )
        if not os.path.isdir(label_dir):
            os.makedirs(label_dir)

        return super(MRIsCALabel, self).run(**inputs)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        out_basename = os.path.basename(self.inputs.out_file)
        outputs["out_file"] = os.path.join(
            self.inputs.subjects_dir,
            self.inputs.subject_id,
            "label",
            out_basename,
        )
        return outputs


class MRIsAnatomicalStatsInputSpec(FSTraitedSpecOpenMP):
    # required
    subject_id = traits.String(
        "subject_id",
        argstr="%s",
        position=-2,
        mandatory=True,
        desc="Subject name or ID",
    )
    hemisphere = traits.Enum(
        "lh",
        "rh",
        argstr="%s",
        position=-1,
        mandatory=True,
        desc="Hemisphere ('lh' or 'rh')",
    )
    mgz = traits.Bool(
        argstr="-mgz",
        mandatory=False,
        desc="Output in mgz format (default is text)",
    )
    cortex = File(
        argstr="-cortex %s",
        mandatory=True,
        exists=True,
        desc="Cortical surface file",
    )
    annot = File(
        argstr="-a %s",
        mandatory=True,
        exists=True,
        desc="Annotation file",
    )
    tabulr_output = traits.Bool(
        argstr="-b",
        mandatory=False,
        default_value=True,
        usedefault=True,
        desc="Output in tabular format (default is text)",
    )
    out_file = File(
        argstr="-f %s",
        exists=False,
        name_source=["hemisphere"],
        keep_extension=True,
        hash_files=False,
        name_template="%s.aparc.stats",
        desc="Table output file",
    )


class MRIsAnatomicalStatsOutputSpec(TraitedSpec):
    out_file = File(
        exists=False, desc="Output in tabular format (default is text)"
    )


class MRIsAnatomicalStats(FSCommandOpenMP):
    """
    For a single subject, produces a table of neuroanatomical statistics
    for each cortical region. The statistics are computed from the
    annotation file, which assigns a neuroanatomical label to each
    cortical surface vertex. The table is written to the file
    <hemisphere>.aparc.stats in the subject's stats/ directory.

    Examples
    ========

    >>> from nipype.interfaces import freesurfer
    >>> anatomical_stats = freesurfer.MRIsAnatomicalStats()
    >>> anatomical_stats.inputs.subject_id = "test"
    >>> anatomical_stats.inputs.hemisphere = "lh"
    >>> anatomical_stats.inputs.cortex = "lh.cortex.label"
    >>> anatomical_stats.inputs.annot = "lh.aparc.annot"
    >>> anatomical_stats.cmdline
    'mris_anatomical_stats -b -cortex lh.cortex.label -a lh.aparc.annot test lh'
    """

    _cmd = "mris_anatomical_stats"
    input_spec = MRIsAnatomicalStatsInputSpec
    output_spec = MRIsAnatomicalStatsOutputSpec

    def run(self, **inputs):
        # The label directory must exist in order for an output to be written
        label_dir = os.path.join(
            self.inputs.subjects_dir, self.inputs.subject_id, "label"
        )
        if not os.path.isdir(label_dir):
            os.makedirs(label_dir)

        return super(MRIsAnatomicalStats, self).run(**inputs)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        out_basename = os.path.basename(self.inputs.out_file)
        outputs["out_file"] = os.path.join(
            self.inputs.subjects_dir,
            self.inputs.subject_id,
            "stats",
            out_basename,
        )
        return outputs


class MRISegStatsInputSpec(FSTraitedSpecOpenMP):
    # required
    segmentation = File(
        argstr="--seg %s",
        mandatory=True,
        desc="input segmentation volume",
    )
    ctab = File(
        argstr="--ctab %s",
        mandatory=True,
        exists=True,
        desc="Freesurfer color table file.",
    )
    excludeid = traits.List(
        traits.Int,
        argstr="--excludeid %s",
        mandatory=False,
        desc="list of segmentation ids to exclude",
    )
    out_file = File(
        argstr="--sum %s",
        mandatory=True,
        exists=False,
        keep_extension=True,
        hash_files=False,
        desc="ASCII file in which summary statistics are saved",
    )
    # optional
    partial_volume = File(
        argstr="--pv %s",
        mandatory=False,
        exists=True,
        desc="Use pvvol to compenstate for partial voluming.",
    )


class MRISegStatsStatsOutputSpec(TraitedSpec):
    out_file = File(
        exists=False, desc="ASCII file in which summary statistics are saved"
    )


class MRISegStats(FSCommandOpenMP):
    """
    Computes statistics on a segmentation volume.

    Examples
    ========
    >>> from nipype.interfaces import freesurfer
    >>> segstats = freesurfer.MRIsSegStats()
    >>> segstats.inputs.segmentation = 'aseg.mgz'
    >>> segstats.inputs.ctab = 'FreeSurferColorLUT.txt'
    >>> segstats.inputs.out_file = 'aseg.stats'
    >>> segstats.cmdline
    'mri_segstats --ctab FreeSurferColorLUT.txt --seg aseg.mgz --sum aseg.stats'
    """

    _cmd = "mri_segstats"
    input_spec = MRISegStatsInputSpec
    output_spec = MRISegStatsStatsOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = self.inputs.out_file
        return outputs
