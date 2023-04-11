#!/bin/bash

SCRIPT_DIR=/script
DATA_DIR=/data/2Env_2TrajsPer_Ver2_03212023/
WORK_DIR=/workdir

cd ${SCRIPT_DIR}

python3 -m scripts.test_api_dataset_player \
	--config-fn ${WORK_DIR}/conf.py \
	--dataset-dir ${DATA_DIR} \
	--output-dir ${DATA_DIR}/debug_dataset
	# --debug
