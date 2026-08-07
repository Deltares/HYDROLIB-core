import os
import hydrolib.core.dflowfm as hcdfm

model_name = 'test_model'
dir_output = r'c:\test_model'

path_style = 'unix' # windows / unix

#create dummy files
if not os.path.exists(dir_output):
    os.mkdir(dir_output)
file_pli = os.path.join(dir_output,f'{model_name}.pli')
with open(file_pli,'w') as f:
    f.write("""name
                1    2
                1.0    2.0
                3.0    4.0
                """)

file_bc = os.path.join(dir_output,f'{model_name}.bc')
with open(file_bc,'w') as f:
    f.write("""[Forcing]
               name              = right01_0001
               function          = timeseries
               timeInterpolation = linear
               quantity          = time
               unit              = minutes since 2001-01-01
               quantity          = waterlevelbnd
               unit              = m
                  0.000000 2.50
               1440.000000 2.50
                """)

ForcingModel_object = hcdfm.ForcingModel(file_bc)
boundary_object = hcdfm.Boundary(quantity='waterlevelbnd',
                                 locationfile=file_pli, #TODO: does not check if name of forcing is found in plifile
                                 forcingfile=ForcingModel_object)

mdu_file = os.path.join(dir_output, f'{model_name}.mdu')
mdu = hcdfm.FMModel()
ext_file_new = os.path.join(dir_output, f'{model_name}_bc.ext')
ext_bnd = hcdfm.ExtModel()

ext_bnd.boundary.append(boundary_object)
ext_bnd.save(ext_file_new,path_style=path_style)

mdu.external_forcing.extforcefilenew = ext_bnd #TODO: file not found if unix path_style