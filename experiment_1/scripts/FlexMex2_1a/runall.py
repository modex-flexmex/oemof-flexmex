import logging

import preprocessing
import infer
import optimization
import postprocessing


if __name__ == '__main__':
    logging.info("Start running the whole modelling pipeline")

    preprocessing.main()

    infer.main()
    #
    # optimization.main()
    #
    # postprocessing.main()
