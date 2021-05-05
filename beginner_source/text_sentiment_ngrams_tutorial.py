"""
torchtext 라이브러리로 텍스트 분류하기
===============================================

**번역**: `김강민 <https://github.com/gangsss>`_ , `김진현 <https://github.com/lewhe0>`_

이 튜토리얼에서는 torchtext 라이브러리를 사용하여 어떻게 텍스트 분류 분석을 위한 데이터셋을 만드는지를 살펴보겠습니다.
다음과 같은 내용들을 알게 됩니다:

   - 반복자(iterator)로 가공되지 않은 데이터(raw data)에 접근하기
   - 가공되지 않은 텍스트 문장들을 모델 학습에 사용할 수 있는 ``torch.Tensor`` 로 변환하는 데이터 처리 파이프라인 만들기
   - `torch.utils.data.DataLoader <https://pytorch.org/docs/stable/data.html?highlight=dataloader#torch.utils.data.DataLoader>`__ 를 사용하여 데이터를 섞고 반복하기(shuffle and iterate)
"""

######################################################################
# 기초 데이터셋 반복자(raw data iterator)에 접근하기
# -------------------------------------------------------------
#
# torchtext 라이브러리는 가공되지 않은 텍스트 문장들을 만드는(yield) 몇 가지 기초 데이터셋 반복자(raw dataset iterator)를 제공합니다.
# 예를 들어, ``AG_NEWS`` 데이터셋 반복자는 레이블(label)과 문장의 튜플(tuple) 형태로 가공되지 않은 데이터를 만듭니다.

import torch
from torchtext.datasets import AG_NEWS
train_iter = AG_NEWS(split='train')

######################################################################
# ::
#
#     next(train_iter)
#     >>> (3, "Wall St. Bears Claw Back Into the Black (Reuters) Reuters -
#     Short-sellers, Wall Street's dwindling\\band of ultra-cynics, are seeing green
#     again.")
#
#     next(train_iter)
#     >>> (3, 'Carlyle Looks Toward Commercial Aerospace (Reuters) Reuters - Private
#     investment firm Carlyle Group,\\which has a reputation for making well-timed
#     and occasionally\\controversial plays in the defense industry, has quietly
#     placed\\its bets on another part of the market.')
#
#     next(train_iter)
#     >>> (3, "Oil and Economy Cloud Stocks' Outlook (Reuters) Reuters - Soaring
#     crude prices plus worries\\about the economy and the outlook for earnings are
#     expected to\\hang over the stock market next week during the depth of
#     the\\summer doldrums.")
#

######################################################################
# 데이터 처리 파이프라인 준비하기
# ---------------------------------
#
# 어휘집(vocab), 단어 벡터(word vector), 토크나이저(tokenizer)를 포함하여 torchtext 라이브러리의 가장 기본적인 구성요소를 재검토했습니다.
# 이들은 가공되지 않은 텍스트 문자열에 대한 기본적인 데이터 처리 빌딩 블록(data processing building block)입니다.
#
# 다음은 토크나이저 및 어휘집을 사용한 일반적인 NLP 데이터 처리의 예입니다.
# 첫번째 단계는 가공되지 않은 학습 데이터셋으로 어휘집을 만드는 것입니다.
# 사용자는 Vocab 클래스의 생성자에 인자를 설정하여 사용자 정의된 어휘집(customized vocab)을 만들 수 있습니다.
# 토큰(token)들의 최소 빈도 ``min_freq`` 에 대한 예시는 아래와 같습니다.


from torchtext.data.utils import get_tokenizer
from collections import Counter
from torchtext.vocab import Vocab

tokenizer = get_tokenizer('basic_english')
train_iter = AG_NEWS(split='train')
counter = Counter()
for (label, line) in train_iter:
    counter.update(tokenizer(line))
vocab = Vocab(counter, min_freq=1)


######################################################################
# 어휘집 블록(vocabulary block)은 토큰 목록을 정수로 변환합니다.
#
# ::
#
#     [vocab[token] for token in ['here', 'is', 'an', 'example']]
#     >>> [476, 22, 31, 5298]
#
# 토크나이저와 어휘집을 갖춘 텍스트 처리 파이프라인을 준비합니다.
# 텍스트 파이프라인과 레이블(label) 파이프라인은 데이터셋 반복자로부터 얻어온 가공되지 않은 문장 데이터를 처리하기 위해 사용됩니다.

text_pipeline = lambda x: [vocab[token] for token in tokenizer(x)]
label_pipeline = lambda x: int(x) - 1


######################################################################
# 텍스트 파이프라인은 어휘집에 정의된 룩업 테이블(순람표; lookup table)에 기반하여 텍스트 문장을 정수 목록으로 변환합니다.
# 레이블(label) 파이프라인은 레이블을 정수로 변환합니다. 예를 들어,
#
# ::
#
#     text_pipeline('here is the an example')
#     >>> [475, 21, 2, 30, 5286]
#     label_pipeline('10')
#     >>> 9
#



######################################################################
# 데이터 배치(batch)와 반복자 생성하기
# ----------------------------------------
#
# `torch.utils.data.DataLoader <https://pytorch.org/docs/stable/data.html?highlight=dataloader#torch.utils.data.DataLoader>`__ 를
# 권장합니다. (튜토리얼은 `여기 <https://tutorials.pytorch.kr/beginner/data_loading_tutorial.html>`__ 있습니다.)
# 이는 ``getitem()`` 과 ``len()`` 프로토콜을 구현한 맵 형태(map-style)의 데이터셋으로 동작하며, 맵(map)처럼 인덱스/키로 데이터 샘플을 얻어옵니다.
# 또한, 셔플(shuffle) 인자를 ``False`` 로 설정하면 반복 가능한(iteratable) 데이터셋처럼 동작합니다.
#
# 모델로 보내기 전, ``collate_fn`` 함수는 ``DataLoader`` 로부터 생성된 샘플 배치로 동작합니다.
# ``collate_fn`` 의 입력은 ``DataLoader`` 에 배치 크기(batch size)가 있는 배치(batch) 데이터이며,
# ``collate_fn`` 은 이를 미리 선언된 데이터 처리 파이프라인에 따라 처리합니다.
# ``collate_fn`` 이 최상위 수준으로 정의(top level def)되었는지 확인합니다. 이렇게 하면 모든 워커에서 이 함수를 사용할 수 있습니다.
#
# 아래 예제에서, 주어진(original) 데이터 배치의 텍스트 항목들은 리스트(list)에 담긴(pack) 뒤 ``nn.EmbeddingBag`` 의 입력을 위한 하나의 텐서(tensor)로 합쳐(concatenate)집니다.
# 오프셋(offset)은 텍스트 텐서(text tensor)에서 개별 시퀀스 시작 인덱스를 표현하기 위한 구분자(delimiter) 텐서입니다.
# 레이블(label)은 개별 텍스트 항목의 레이블을 저장하는 텐서입니다.


from torch.utils.data import DataLoader
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def collate_batch(batch):
    label_list, text_list, offsets = [], [], [0]
    for (_label, _text) in batch:
         label_list.append(label_pipeline(_label))
         processed_text = torch.tensor(text_pipeline(_text), dtype=torch.int64)
         text_list.append(processed_text)
         offsets.append(processed_text.size(0))
    label_list = torch.tensor(label_list, dtype=torch.int64)
    offsets = torch.tensor(offsets[:-1]).cumsum(dim=0)
    text_list = torch.cat(text_list)
    return label_list.to(device), text_list.to(device), offsets.to(device)

train_iter = AG_NEWS(split='train')
dataloader = DataLoader(train_iter, batch_size=8, shuffle=False, collate_fn=collate_batch)


######################################################################
# 모델 정의하기
# ---------------
#
# 모델은
# `nn.EmbeddingBag <https://pytorch.org/docs/stable/nn.html?highlight=embeddingbag#torch.nn.EmbeddingBag>`__
# 레이어와 분류(classification) 목적을 위한 선형 레이어로 구성됩니다.
# 기본 모드가 "평균(mean)"인 ``nn.EmbeddingBag`` 은 임베딩들의 "가방(bag)"의 평균 값을 계산합니다.
# 이때 텍스트(text) 항목들은 각기 그 길이가 다를 수 있지만, ``nn.EmbeddingBag`` 모듈은 텍스트의 길이를
# 오프셋(offset)으로 저장하고 있으므로 패딩(padding)이 필요하지는 않습니다.
#
# 덧붙여서, ``nn.EmbeddingBag`` 은 임베딩의 평균을 즉시 계산하기 때문에,
# 텐서들의 시퀀스를 처리할 때 성능 및 메모리 효율성 측면에서의 장점도
# 갖고 있습니다.
#
# .. image:: ../_static/img/text_sentiment_ngrams_model.png
#


from torch import nn

class TextClassificationModel(nn.Module):

    def __init__(self, vocab_size, embed_dim, num_class):
        super(TextClassificationModel, self).__init__()
        self.embedding = nn.EmbeddingBag(vocab_size, embed_dim, sparse=True)
        self.fc = nn.Linear(embed_dim, num_class)
        self.init_weights()

    def init_weights(self):
        initrange = 0.5
        self.embedding.weight.data.uniform_(-initrange, initrange)
        self.fc.weight.data.uniform_(-initrange, initrange)
        self.fc.bias.data.zero_()

    def forward(self, text, offsets):
        embedded = self.embedding(text, offsets)
        return self.fc(embedded)


######################################################################
# 인스턴스 생성하기
# -----------------
#
# ``AG_NEWS`` 데이터셋에는 4종류의 레이블이 존재하므로 클래스의 개수도 4개입니다.
#
# ::
#
#    1 : World (세계)
#    2 : Sports (스포츠)
#    3 : Business (경제)
#    4 : Sci/Tec (과학/기술)
#
# 임베딩 차원이 64인 모델을 만듭니다.
# 어휘집의 크기(Vocab size)는 어휘집(vocab)의 길이와 같습니다.
# 클래스의 개수는 레이블의 개수와 같습니다.
#

train_iter = AG_NEWS(split='train')
num_class = len(set([label for (label, text) in train_iter]))
vocab_size = len(vocab)
emsize = 64
model = TextClassificationModel(vocab_size, emsize, num_class).to(device)


######################################################################
# 모델을 학습하고 결과를 평가하는 함수 정의하기
# ---------------------------------------------
#


import time

def train(dataloader):
    model.train()
    total_acc, total_count = 0, 0
    log_interval = 500
    start_time = time.time()
    for idx, (label, text, offsets) in enumerate(dataloader):
        optimizer.zero_grad()
        predited_label = model(text, offsets)
        loss = criterion(predited_label, label)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 0.1)
        optimizer.step()
        total_acc += (predited_label.argmax(1) == label).sum().item()
        total_count += label.size(0)
        if idx % log_interval == 0 and idx > 0:
            elapsed = time.time() - start_time
            print('| epoch {:3d} | {:5d}/{:5d} batches '
                  '| accuracy {:8.3f}'.format(epoch, idx, len(dataloader),
                                              total_acc/total_count))
            total_acc, total_count = 0, 0
            start_time = time.time()

def evaluate(dataloader):
    model.eval()
    total_acc, total_count = 0, 0

    with torch.no_grad():
        for idx, (label, text, offsets) in enumerate(dataloader):
            predited_label = model(text, offsets)
            loss = criterion(predited_label, label)
            total_acc += (predited_label.argmax(1) == label).sum().item()
            total_count += label.size(0)
    return total_acc/total_count


######################################################################
# 데이터셋을 분할하고 모델 수행하기
# ---------------------------------
#
# 원본 ``AG_NEWS`` 에는 검증용 데이터가 포함되어 있지 않기 때문에, 우리는 학습
# 데이터를 학습 및 검증 데이터로 분할하려 합니다. 이때 데이터를 분할하는
# 비율은 0.95(학습)와 0.05(검증) 입니다. 우리는 여기서 PyTorch의
# 핵심 라이브러리 중 하나인
# `torch.utils.data.dataset.random_split <https://pytorch.org/docs/stable/data.html?highlight=random_split#torch.utils.data.random_split>`__
# 함수를 사용합니다.
#
# `CrossEntropyLoss <https://pytorch.org/docs/stable/nn.html?highlight=crossentropyloss#torch.nn.CrossEntropyLoss>`__
# 기준(criterion)은 각 클래스에 대해 ``nn.LogSoftmax()`` 와 ``nn.NLLLoss()`` 를
# 합쳐놓은 방식입니다.
# `SGD <https://pytorch.org/docs/stable/_modules/torch/optim/sgd.html>`__
# optimizer는 확률적 경사 하강법를 구현해놓은 것입니다. 처음의 학습률은
# 5.0으로 두었습니다. 매 에폭을 진행하면서 학습률을 조절할 때는
# `StepLR <https://pytorch.org/docs/master/_modules/torch/optim/lr_scheduler.html#StepLR>`__
# 을 사용합니다.
#

from torch.utils.data.dataset import random_split
# Hyperparameters
EPOCHS = 10 # epoch
LR = 5  # learning rate
BATCH_SIZE = 64 # batch size for training

criterion = torch.nn.CrossEntropyLoss()
optimizer = torch.optim.SGD(model.parameters(), lr=LR)
scheduler = torch.optim.lr_scheduler.StepLR(optimizer, 1.0, gamma=0.1)
total_accu = None
train_iter, test_iter = AG_NEWS()
train_dataset = list(train_iter)
test_dataset = list(test_iter)
num_train = int(len(train_dataset) * 0.95)
split_train_, split_valid_ = \
    random_split(train_dataset, [num_train, len(train_dataset) - num_train])

train_dataloader = DataLoader(split_train_, batch_size=BATCH_SIZE,
                              shuffle=True, collate_fn=collate_batch)
valid_dataloader = DataLoader(split_valid_, batch_size=BATCH_SIZE,
                              shuffle=True, collate_fn=collate_batch)
test_dataloader = DataLoader(test_dataset, batch_size=BATCH_SIZE,
                             shuffle=True, collate_fn=collate_batch)

for epoch in range(1, EPOCHS + 1):
    epoch_start_time = time.time()
    train(train_dataloader)
    accu_val = evaluate(valid_dataloader)
    if total_accu is not None and total_accu > accu_val:
      scheduler.step()
    else:
       total_accu = accu_val
    print('-' * 59)
    print('| end of epoch {:3d} | time: {:5.2f}s | '
          'valid accuracy {:8.3f} '.format(epoch,
                                           time.time() - epoch_start_time,
                                           accu_val))
    print('-' * 59)


######################################################################
# 이 모델을 GPU 상에서 수행하고 다음과 같은 결과를 얻었습니다:
#
# ::
#
#        | epoch   1 |   500/ 1782 batches | accuracy    0.684
#        | epoch   1 |  1000/ 1782 batches | accuracy    0.852
#        | epoch   1 |  1500/ 1782 batches | accuracy    0.877
#        -----------------------------------------------------------
#        | end of epoch   1 | time:  8.33s | valid accuracy    0.867
#        -----------------------------------------------------------
#        | epoch   2 |   500/ 1782 batches | accuracy    0.895
#        | epoch   2 |  1000/ 1782 batches | accuracy    0.900
#        | epoch   2 |  1500/ 1782 batches | accuracy    0.903
#        -----------------------------------------------------------
#        | end of epoch   2 | time:  8.18s | valid accuracy    0.890
#        -----------------------------------------------------------
#        | epoch   3 |   500/ 1782 batches | accuracy    0.914
#        | epoch   3 |  1000/ 1782 batches | accuracy    0.914
#        | epoch   3 |  1500/ 1782 batches | accuracy    0.916
#        -----------------------------------------------------------
#        | end of epoch   3 | time:  8.20s | valid accuracy    0.897
#        -----------------------------------------------------------
#        | epoch   4 |   500/ 1782 batches | accuracy    0.926
#        | epoch   4 |  1000/ 1782 batches | accuracy    0.924
#        | epoch   4 |  1500/ 1782 batches | accuracy    0.921
#        -----------------------------------------------------------
#        | end of epoch   4 | time:  8.18s | valid accuracy    0.895
#        -----------------------------------------------------------
#        | epoch   5 |   500/ 1782 batches | accuracy    0.938
#        | epoch   5 |  1000/ 1782 batches | accuracy    0.935
#        | epoch   5 |  1500/ 1782 batches | accuracy    0.937
#        -----------------------------------------------------------
#        | end of epoch   5 | time:  8.16s | valid accuracy    0.902
#        -----------------------------------------------------------
#        | epoch   6 |   500/ 1782 batches | accuracy    0.939
#        | epoch   6 |  1000/ 1782 batches | accuracy    0.939
#        | epoch   6 |  1500/ 1782 batches | accuracy    0.938
#        -----------------------------------------------------------
#        | end of epoch   6 | time:  8.16s | valid accuracy    0.906
#        -----------------------------------------------------------
#        | epoch   7 |   500/ 1782 batches | accuracy    0.941
#        | epoch   7 |  1000/ 1782 batches | accuracy    0.939
#        | epoch   7 |  1500/ 1782 batches | accuracy    0.939
#        -----------------------------------------------------------
#        | end of epoch   7 | time:  8.19s | valid accuracy    0.903
#        -----------------------------------------------------------
#        | epoch   8 |   500/ 1782 batches | accuracy    0.942
#        | epoch   8 |  1000/ 1782 batches | accuracy    0.941
#        | epoch   8 |  1500/ 1782 batches | accuracy    0.942
#        -----------------------------------------------------------
#        | end of epoch   8 | time:  8.16s | valid accuracy    0.904
#        -----------------------------------------------------------
#        | epoch   9 |   500/ 1782 batches | accuracy    0.942
#        | epoch   9 |  1000/ 1782 batches | accuracy    0.941
#        | epoch   9 |  1500/ 1782 batches | accuracy    0.942
#        -----------------------------------------------------------
#          end of epoch   9 | time:  8.16s | valid accuracy    0.904
#        -----------------------------------------------------------
#        | epoch  10 |   500/ 1782 batches | accuracy    0.940
#        | epoch  10 |  1000/ 1782 batches | accuracy    0.942
#        | epoch  10 |  1500/ 1782 batches | accuracy    0.942
#        -----------------------------------------------------------
#        | end of epoch  10 | time:  8.15s | valid accuracy    0.904
#        -----------------------------------------------------------


######################################################################
# 평가 데이터로 모델 평가하기
# -------------------------------
#



######################################################################
# 평가 데이터셋을 통한 결과를 확인합니다...

print('Checking the results of test dataset.')
accu_test = evaluate(test_dataloader)
print('test accuracy {:8.3f}'.format(accu_test))

################################################
#
# ::
#
#        test accuracy    0.906
#


######################################################################
# 임의의 뉴스로 평가하기
# ----------------------
#
# 현재까지 최고의 모델로 골프 뉴스를 테스트해보겠습니다.
#

ag_news_label = {1: "World",
                 2: "Sports",
                 3: "Business",
                 4: "Sci/Tec"}

def predict(text, text_pipeline):
    with torch.no_grad():
        text = torch.tensor(text_pipeline(text))
        output = model(text, torch.tensor([0]))
        return output.argmax(1).item() + 1

ex_text_str = "MEMPHIS, Tenn. – Four days ago, Jon Rahm was \
    enduring the season’s worst weather conditions on Sunday at The \
    Open on his way to a closing 75 at Royal Portrush, which \
    considering the wind and the rain was a respectable showing. \
    Thursday’s first round at the WGC-FedEx St. Jude Invitational \
    was another story. With temperatures in the mid-80s and hardly any \
    wind, the Spaniard was 13 strokes better in a flawless round. \
    Thanks to his best putting performance on the PGA Tour, Rahm \
    finished with an 8-under 62 for a three-stroke lead, which \
    was even more impressive considering he’d never played the \
    front nine at TPC Southwind."

model = model.to("cpu")

print("This is a %s news" %ag_news_label[predict(ex_text_str, model, vocab, 2)])

################################################
#
# ::
#
#        This is a Sports news
#