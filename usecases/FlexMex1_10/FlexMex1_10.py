import os
from oemoflex.usecase import Usecase

basepath = os.path.dirname(os.path.realpath(__file__))

usecase = Usecase(
    name='FlexMex1_10',
    year='2050',
    basepath=basepath,
    datapath=os.path.join(basepath, '..', 'data_raw'),
    components=[
        'electricity-shortage',
        'electricity-curtailment',
        'electricity-demand',
        'electricity-transmission',
        'wind-offshore',
        'wind-onshore',
        'solar-pv',
    ],
)

usecase.run()
