import logging

import FlexMex1_10_preprocessing
import FlexMex1_10_infer
import FlexMex1_10_optimization
import FlexMex1_10_postprocessing


if __name__ == '__main__':
    logging.info("Start running the whole modelling pipeline")

    FlexMex1_10_preprocessing.main()

    FlexMex1_10_infer.main()

    # FlexMex1_10_optimization.main()

    # FlexMex1_10_postprocessing.main()
