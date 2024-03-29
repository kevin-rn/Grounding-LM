# Hover
This repo contains the source code of the baseline models described in the following paper 
* *"HoVer: A Dataset for Many-Hop Fact Extraction And Claim Verification"* in Findings of EMNLP, 2020. ([paper](https://arxiv.org/abs/2011.03088)).

The basic code structure was adapted from [Transformers](https://github.com/huggingface/transformers).

## 0. Preparation
### Dependencies
* PyTorch 1.4.0/1.6.0
* See `requirements.txt`.

Note: the dependencies are part of the ``hover_env.yml``

## 1. Document Retrieval
This section remains the same as the original HoVer repository, for more information on the retrieval methods see the README in ``src/retrieval``.

### TF-IDF Pre-retrieval
We provide the top-100 Wikipedia articles retrieved by running [DRQA](https://github.com/facebookresearch/DrQA) on the HoVer dataset. It was already downloaded in `data/hover/tfidf_retrieved`.

### Training Neural-based Document Retrieval Model
* Prepare the data by running:
```
python prepare_data_for_doc_retrieval.py --data_split=train --doc_retrieve_range=20 [-dataset_name=CLAIM_DATA_NAME] [--db_name=DB_NAME]
python prepare_data_for_doc_retrieval.py --data_split=dev --doc_retrieve_range=20 [-dataset_name=CLAIM_DATA_NAME] [--db_name=DB_NAME]
```
This will add the top-20 TF-IDF retrieved documents to the data as candidates of the following neural document retrieval stage.

* Run `./cmds/train_scripts/train_doc_retrieval.sh modified`. The model checkpoints are saved in `out/hover/exp1.0/doc_retrieval`.

### Evaluating Neural-based Document Retrieval Model
* Run the evaluation:
```
./cmds/eval_scripts/eval_doc_retrieval_on_train.sh CLAIM_DATA_NAME
./cmds/eval_scripts/eval_doc_retrieval_on_dev.sh CLAIM_DATA_NAME
``` 
This will evaluate the model on both the training set and dev set because we need both predictions to construct the training/dev set for the sentence selection.

## 2. Sentence Selection
### Training Sentence-selection Model
* First, start the Stanford Corernlp in the background. We use Corenlp to split the sentences:
```
java -mx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -annotators "tokenize,ssplit,pos,lemma,parse,sentiment" -port 9000 -timeout 30000
```

* Prepare the data by running:
```
python prepare_data_for_sent_retrieval.py --data_split=train --sent_retrieve_range=5 [-dataset_name=CLAIM_DATA_NAME] [--db_name=DB_NAME]
python prepare_data_for_sent_retrieval.py --data_split=dev --sent_retrieve_range=5 [-dataset_name=CLAIM_DATA_NAME] [--db_name=DB_NAME]
```
This will add the sentences from the top-5 retrieved documents as candidates of the following sentence selection stage.

* Run `./cmds/train_scripts/train_sent_retrieval.sh`. The model checkpoints are saved in `out/hover/exp1.0/sent_retrieval`.

### Evaluating Sentence-selection Model
* Run the evaluation:
```
./cmds/eval_scripts/eval_sent_retrieval_on_train.sh
./cmds/eval_scripts/eval_sent_retrieval_on_dev.sh
``` 
This will evaluate the model on both the training set and dev set because we need both predictions to construct the training/dev set for the claim verification.

## (Alternative) 2. Immediate Claim verification
* Prepare data for Claim verification for the reranking setup (requires the grounding environment)
```
python prepare_doc_retrieve_for_claim_verification.py --data_split=train --doc_retrieve_range=5
python prepare_doc_retrieve_for_claim_verification.py --data_split=dev --doc_retrieve_range=5
```

## 3. Claim Verification
### Training Claim-verification Model
* Prepare the data by running:
```
python prepare_data_for_claim_verification.py --data_split=train [-dataset_name=CLAIM_DATA_NAME] [--db_name=DB_NAME]
python prepare_data_for_claim_verification.py --data_split=dev [-dataset_name=CLAIM_DATA_NAME] [--db_name=DB_NAME]
```

* Run `./cmds/train_scripts/train_claim_verification.sh`. The model checkpoints are saved in `out/hover/exp1.0/claim_verification`.

### Evaluating Claim-verification Model
* Run the evaluation:
```
./cmds/eval_scripts/eval_claim_verification_on_dev.sh
```

## Citation
```
@inproceedings{jiang2020hover,
  title={{HoVer}: A Dataset for Many-Hop Fact Extraction And Claim Verification},
  author={Yichen Jiang and Shikha Bordia and Zheng Zhong and Charles Dognin and Maneesh Singh and Mohit Bansal.},
  booktitle={Findings of the Conference on Empirical Methods in Natural Language Processing ({EMNLP})},
  year={2020}
}
```