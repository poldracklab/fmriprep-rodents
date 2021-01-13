from pathlib import Path

from nipype.utils.filemanip import fname_presuffix
from nipype.interfaces.base import (
    BaseInterfaceInputSpec,
    TraitedSpec,
    SimpleInterface,
    File,
)
import numpy as np


class Volreg2ITKInputSpec(BaseInterfaceInputSpec):
    in_file = File(
        exists=True, mandatory=True, desc="mat file generated by AFNI's 3dVolreg"
    )


class Volreg2ITKOutputSpec(TraitedSpec):
    out_file = File(desc="the output ITKTransform file")


class Volreg2ITK(SimpleInterface):

    """
    Convert an AFNI's mat file into an ITK Transform file.
    """

    input_spec = Volreg2ITKInputSpec
    output_spec = Volreg2ITKOutputSpec

    def _run_interface(self, runtime):
        # Load AFNI mat entries and reshape appropriately
        orig_afni_mat = np.loadtxt(self.inputs.in_file)
        afni_affines = [mat.reshape(3, 4, order="C") for mat in orig_afni_mat]

        out_file = Path(
            fname_presuffix(
                self.inputs.in_file,
                use_ext=False,
                suffix="_mc4d_itk.txt",
                newpath=runtime.cwd,
            )
        )

        fixed_params = "FixedParameters: 0 0 0"  # Center of rotation does not change
        lines = ["#Insight Transform File V1.0"]
        for i, affine in enumerate(afni_affines):
            lines.append("#Transform %d" % i)
            lines.append("Transform: AffineTransform_double_3_3")

            ants_affine_2d = np.hstack(
                (affine[:3, :3].reshape(1, -1), affine[:3, 3].reshape(1, -1))
            )
            params = ants_affine_2d.reshape(-1).astype("float64")
            params_list = ["%g" % i for i in params.tolist()]
            lines.append("Parameters: %s" % " ".join(params_list))
            lines.append(fixed_params)

        out_file.write_text("\n".join(lines))
        self._results["out_file"] = str(out_file)
        return runtime
