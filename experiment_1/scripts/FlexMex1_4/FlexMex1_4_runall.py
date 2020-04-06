import logging

import FlexMex1_4_preprocessing
import FlexMex1_4_infer
import FlexMex1_4_optimization
import FlexMex1_4_postprocessing


if __name__ == '__main__':
    logging.info("Start running the whole modelling pipeline")

    FlexMex1_4_preprocessing.main()

    FlexMex1_4_infer.main()

    FlexMex1_4_optimization.main()

    FlexMex1_4_postprocessing.main()
