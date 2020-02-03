# -*- coding: utf-8 -*-
"""
적대적 예제 생성(Adversarial Example Generation)
==============================

**저자:** `Nathan Inkawhich <https://github.com/inkawhich>`__
**번역:** `BONGMO KIM <https://github.com/bongmo>`__

If you are reading this, hopefully you can appreciate how effective some
machine learning models are. Research is constantly pushing ML models to
be faster, more accurate, and more efficient. However, an often
overlooked aspect of designing and training models is security and
robustness, especially in the face of an adversary who wishes to fool
the model.
이 글을 읽고 있다면, 머신 러닝 모델이 얼마나 효과적인지 알 수 있을 것입니다. 
연구는 ML(Machine Learming) 모델을 더욱 빠르고 정확하며 효율적이 되는 방향으로 진행됩니다. 
그러나 모델을 설계하고 훈련하는 데 종종 간과되는 측면은 특히 모델을 속이려하는 적을 대면했을 때 보안과 견고성입니다.

This tutorial will raise your awareness to the security vulnerabilities
of ML models, and will give insight into the hot topic of adversarial
machine learning. You may be surprised to find that adding imperceptible
perturbations to an image *can* cause drastically different model
performance. Given that this is a tutorial, we will explore the topic
via example on an image classifier. Specifically we will use one of the
first and most popular attack methods, the Fast Gradient Sign Attack
(FGSM), to fool an MNIST classifier.
이 튜토리얼은 ML 모델들의 보안 취약점에 대한 인식을 높이고, 요즘 이슈가 되는 적대적 머신 러닝 주제에 대한 통찰력을 제공합니다. 
이미지에 감지 할 수 없는 변화를 추가하면 모델 성능이 크게 달라질 수 있다는 사실에 놀랄 수 있습니다.
이번 튜토리얼에서는 이미지 분류기의 예제를 통해 위 내용에 대해 살펴볼 것입니다.
특히 우리는 가장 많이 사용되는 공격 방법 중 하나인 FGSM (Fast Gradient Sign Attack)을 이용해 MNIST 분류자를 속여 볼 것입니다.
"""


######################################################################
# Threat Model
# 위협 모델
# ------------
# 
# For context, there are many categories of adversarial attacks, each with
# a different goal and assumption of the attacker’s knowledge. However, in
# general the overarching goal is to add the least amount of perturbation
# to the input data to cause the desired misclassification. There are
# several kinds of assumptions of the attacker’s knowledge, two of which
# are: **white-box** and **black-box**. A *white-box* attack assumes the
# attacker has full knowledge and access to the model, including
# architecture, inputs, outputs, and weights. A *black-box* attack assumes
# the attacker only has access to the inputs and outputs of the model, and
# knows nothing about the underlying architecture or weights. There are
# also several types of goals, including **misclassification** and
# **source/target misclassification**. A goal of *misclassification* means
# the adversary only wants the output classification to be wrong but does
# not care what the new classification is. A *source/target
# misclassification* means the adversary wants to alter an image that is
# originally of a specific source class so that it is classified as a
# specific target class.
# 상황에 따라 다양한 범주의 적대적 공격이 있는데 각각은 목표가 다르고 공격자의 지식에
# 대한 가정도 다릅니다. 그러나 보통 가장 중요한 목표는 입력 데이터에 최소한의 작은 변화(Perturbation)을 
# 추가하여 이것이 의도하는대로 잘못 분류되게 하는 것입니다. 공격자의 지식에 대한 
# 가정도는 여러 종류가 있는데, 보통 **화이트박스**와 **블랙박스** 두 가지가 있습니다. 
# *화이트박스* 공격은 공격자가 모델에 대해 아키텍처, 입력, 출력, 가중치를 포함한 모든 것을
# 알고 있고 접근할 수 있다고 가정합니다. *블랙박스* 공격은 공격자가 모델의 입력과 출력에 
# 대해서만 접근 가능하고 모델의 가중치와 아키텍처에 관한 내용은 모른다고 가정합니다. 
# 공격자의 목표는 오분류 및 **소스/타겟 오분류**를 포함하는 여러 유형이 있습니다. 
# *오분류*의 목표는 공격자가 출력으로 나온 분류 결과가 잘못 되도록 하나 새로운 분류 결과가
# 어떤 것이 나오는지 신경 쓰지 않는 것을 의미합니다. *소스/타겟 오분류*는 공격자가 
# 원래 특정 소스 클래스의 이미지를 특정 대상의 클래스로 분류하도록 변경 함을 의미합니다.

# 
# In this case, the FGSM attack is a *white-box* attack with the goal of
# *misclassification*. With this background information, we can now
# discuss the attack in detail.
# 이 경우 FGSM 공격은 *오분류*를 목표로 하는 화이트 박스 공격입니다. 
# 이 배경 정보를 알고 공격에 대해 자세히 알아 보겠습니다.
# 
# Fast Gradient Sign Attack
# 빠른 경사 부호 공격
# -------------------------
# 
# One of the first and most popular adversarial attacks to date is
# referred to as the *Fast Gradient Sign Attack (FGSM)* and is described
# by Goodfellow et. al. in `Explaining and Harnessing Adversarial
# Examples <https://arxiv.org/abs/1412.6572>`__. The attack is remarkably
# powerful, and yet intuitive. It is designed to attack neural networks by
# leveraging the way they learn, *gradients*. The idea is simple, rather
# than working to minimize the loss by adjusting the weights based on the
# backpropagated gradients, the attack *adjusts the input data to maximize
# the loss* based on the same backpropagated gradients. In other words,
# the attack uses the gradient of the loss w.r.t the input data, then
# adjusts the input data to maximize the loss.
# 공격 방법에 있어 초기 방식이면서 가장 유명한 방식은 *빠른 경사 부호 공격 (FGSM)* 이라고 하며 
# `적대적 예제에 대한 설명과 활용 <https://arxiv.org/abs/1412.6572>`__ 에서 
# 이안 갓펠로우가 기고하였습니다.
# 이 공격법은 놀랍도록 강력하지만 직관적입니다. 학습 방식, *경사도*를 활용하여 신경망을 공격하도록 
# 설계 되었습니다. 아이디어는 간단합니다. 역전파 경사도를 기반으로 가중치를 조정하여 손실을 최소화하기보다는
# 공격이 동일한 역전파 경사도를 기반으로 *손실을 최대화하하는 방향으로 입력 데이터를 조정*합니다. 
# 다시 말해 공격은 입력 데이터에서 계산된 손실 기울기를 사용하고 입력 데이터를 조정하여 손실이 최대가 되게 합니다.


# 
# Before we jump into the code, let’s look at the famous
# `FGSM <https://arxiv.org/abs/1412.6572>`__ panda example and extract
# some notation.
# 코드로 넘어가기 전에 유명한 `FGSM <https://arxiv.org/abs/1412.6572>`__ 판다 예제를 
# 보고 몇 가지 표기법을 정리하겠습니다.
#
# .. figure:: /_static/img/fgsm_panda_image.png
#    :alt: fgsm_panda_image
#
# From the figure, :math:`\mathbf{x}` is the original input image
# correctly classified as a “panda”, :math:`y` is the ground truth label
# for :math:`\mathbf{x}`, :math:`\mathbf{\theta}` represents the model
# parameters, and :math:`J(\mathbf{\theta}, \mathbf{x}, y)` is the loss
# that is used to train the network. The attack backpropagates the
# gradient back to the input data to calculate
# :math:`\nabla_{x} J(\mathbf{\theta}, \mathbf{x}, y)`. Then, it adjusts
# the input data by a small step (:math:`\epsilon` or :math:`0.007` in the
# picture) in the direction (i.e.
# :math:`sign(\nabla_{x} J(\mathbf{\theta}, \mathbf{x}, y))`) that will
# maximize the loss. The resulting perturbed image, :math:`x'`, is then
# *misclassified* by the target network as a “gibbon” when it is still
# clearly a “panda”.
# 
# Hopefully now the motivation for this tutorial is clear, so lets jump
# into the implementation.
# 

from __future__ import print_function
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torchvision import datasets, transforms
import numpy as np
import matplotlib.pyplot as plt


######################################################################
# Implementation
# 구현
# --------------
# 
# In this section, we will discuss the input parameters for the tutorial,
# define the model under attack, then code the attack and run some tests.
# 이 섹션에서는 튜토리얼의 입력 매개 변수에 대해 설명하고 공격중인 모델을
# 정의한 다음 공격을 코딩하고 일부 테스트를 실행합니다.
# 
# Inputs
# 입력
# ~~~~~~
# 
# There are only three inputs for this tutorial, and are defined as
# follows:
# 이 학습서에는 입력이 3 개이며 다음과 같이 정의됩니다:
# 
# -  **epsilons** - List of epsilon values to use for the run. It is
#    important to keep 0 in the list because it represents the model
#    performance on the original test set. Also, intuitively we would
#    expect the larger the epsilon, the more noticeable the perturbations
#    but the more effective the attack in terms of degrading model
#    accuracy. Since the data range here is :math:`[0,1]`, no epsilon
#    value should exceed 1.
# - **epsilons** - 실행에 사용할 엡실론의 리스트입니다. 엡실론 0의 값은 원래 테스트 셋의 모델 성능을
#   나타내므로 목록에 유지하는 것이 중요합니다. 또한 직관적으로 엡실론이 클수록 작은 변화가 더 눈에 띄지만
#   모델 정확도를 저하 시키는 측면에서 더 효과가 있습니다. 여기서 데이터의 범위는 0-1 이기 때문에 
#   엡실론의 값은 1을 초과할 수 없습니다.
# 
# -  **pretrained_model** - path to the pretrained MNIST model which was
#    trained with
#    `pytorch/examples/mnist <https://github.com/pytorch/examples/tree/master/mnist>`__.
#    For simplicity, download the pretrained model `here <https://drive.google.com/drive/folders/1fn83DF14tWmit0RTKWRhPq5uVXt73e0h?usp=sharing>`__.
# - **pretrained_model** - `pytorch/examples/mnist <https://github.com/pytorch/examples/tree/master/mnist>`__ 
#    를 통해 미리 학습된 MNIST 모델의 경로. 
#    튜토리얼을 간편하게 하려면 `여기 <https://drive.google.com/drive/folders/1fn83DF14tWmit0RTKWRhPq5uVXt73e0h?usp=sharing>`__ 에서 미리 학습된 모델을 다운로드하세요.
# 
# -  **use_cuda** - boolean flag to use CUDA if desired and available.
#    Note, a GPU with CUDA is not critical for this tutorial as a CPU will
#    not take much time.
# -  **use_cuda** - CUDA 를 사용할지 말지 정하는 이진 플래그. 
#    본 튜토리얼에서는 CPU 시간이 오래 걸리지 않으므로 CUDA를 지원하는 GPU 의 여부는 중요하지 않습니다.
# 

epsilons = [0, .05, .1, .15, .2, .25, .3]
pretrained_model = "data/lenet_mnist_model.pth"
use_cuda=True


######################################################################
# Model Under Attack
# 공격을 받는 모델
# ~~~~~~~~~~~~~~~~~~
# 
# As mentioned, the model under attack is the same MNIST model from
# `pytorch/examples/mnist <https://github.com/pytorch/examples/tree/master/mnist>`__.
# You may train and save your own MNIST model or you can download and use
# the provided model. The *Net* definition and test dataloader here have
# been copied from the MNIST example. The purpose of this section is to
# define the model and dataloader, then initialize the model and load the
# pretrained weights.
# 앞서 말한대로, 공격을 받는 모델은 `pytorch/examples/mnist <https://github.com/pytorch/examples/tree/master/mnist>`__
# 와 동일한 MNIST 모델입니다. 본인의 MNIST 모델을 학습 및 저장하는 방식으로 하거나 제공된 모델을 다운로드 해 사용하는 식으로 진행할 수 있습니다.
# 여기서 *Net* 정의 및 테스트 데이터 로더는 MNIST 예제에서 복사 하였습니다. 
# 이 섹션의 목적은 모델과 데이터 로더를 정의한 다음, 모델을 초기화하고 미리 학습된 가중치를 읽어오는 것입니다.
# 

# LeNet Model definition
# LeNet 모델 정의
class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(1, 10, kernel_size=5)
        self.conv2 = nn.Conv2d(10, 20, kernel_size=5)
        self.conv2_drop = nn.Dropout2d()
        self.fc1 = nn.Linear(320, 50)
        self.fc2 = nn.Linear(50, 10)

    def forward(self, x):
        x = F.relu(F.max_pool2d(self.conv1(x), 2))
        x = F.relu(F.max_pool2d(self.conv2_drop(self.conv2(x)), 2))
        x = x.view(-1, 320)
        x = F.relu(self.fc1(x))
        x = F.dropout(x, training=self.training)
        x = self.fc2(x)
        return F.log_softmax(x, dim=1)

# MNIST Test dataset and dataloader declaration
# MNIST 테스트 데이터셋과 데이터로더 선언
test_loader = torch.utils.data.DataLoader(
    datasets.MNIST('../data', train=False, download=True, transform=transforms.Compose([
            transforms.ToTensor(),
            ])), 
        batch_size=1, shuffle=True)

# Define what device we are using
# 어떤 디바이스를 사용할지 정의
print("CUDA Available: ",torch.cuda.is_available())
device = torch.device("cuda" if (use_cuda and torch.cuda.is_available()) else "cpu")

# Initialize the network
# 모델 초기화하기
model = Net().to(device)

# Load the pretrained model
# 미리 학습된 모델 읽어오기
model.load_state_dict(torch.load(pretrained_model, map_location='cpu'))

# Set the model in evaluation mode. In this case this is for the Dropout layers
# 모델을 평가 모드로 설정하기. 드롭아웃 레이어들을 위해 사용됨
model.eval()


######################################################################
# FGSM Attack
# FGSM 공격
# ~~~~~~~~~~~
# 
# Now, we can define the function that creates the adversarial examples by
# perturbing the original inputs. The ``fgsm_attack`` function takes three
# inputs, *image* is the original clean image (:math:`x`), *epsilon* is
# the pixel-wise perturbation amount (:math:`\epsilon`), and *data_grad*
# is gradient of the loss w.r.t the input image
# (:math:`\nabla_{x} J(\mathbf{\theta}, \mathbf{x}, y)`). The function
# then creates perturbed image as
# 이제 원래 입력을 교란시켜 적대적인 예를 만드는 함수를 정의 할 수 있습니다. 
# ``fgsm_attack``` 함수는 입력 파라미터로 3가지를 가집니다. 첫번째는 원본 *이미지*(:math:`x`), 
# 두번째는 *엡실론*으로 픽셀 단위의 작은 변화를 주는 값입니다 (:math:`\epsilon`). 
# 마지막은 *data_grad* 로 입력 영상 (:math:`\nabla_{x} J(\mathbf{\theta}, \mathbf{x}, y)`) 에 대한 경사도 손실 값입니다. 
# 아래 식에 따른 작은 변화가 적용된 이미지를 생성합니다.
# 
# .. math:: perturbed\_image = image + epsilon*sign(data\_grad) = x + \epsilon * sign(\nabla_{x} J(\mathbf{\theta}, \mathbf{x}, y))
# 
# Finally, in order to maintain the original range of the data, the
# perturbed image is clipped to range :math:`[0,1]`.
# 마지막으로 데이터의 원래 범위를 유지하기 위해, 작은 변화가 적용된 이미지가 :math:`[0,1]` 범위로 잘립니다.
# 

# FGSM attack code
# FGSM 공격 코드
def fgsm_attack(image, epsilon, data_grad):
    # Collect the element-wise sign of the data gradient
    # data_grad 의 요소별 부호 값을 얻어옵니다
    sign_data_grad = data_grad.sign()
    # Create the perturbed image by adjusting each pixel of the input image
    # 입력 이미지의 각 픽셀에 sign_data_grad 를 적용해 작은 변화가 적용된 이미지를 생성합니다.
    perturbed_image = image + epsilon*sign_data_grad
    # Adding clipping to maintain [0,1] range
    # 값 범위를 [0,1]로 유지하기 위해 자르기(clipping)를 추가합니다
    perturbed_image = torch.clamp(perturbed_image, 0, 1)
    # Return the perturbed image
    # 작은 변화가 적용된 이미지를 리턴합니다
    return perturbed_image


######################################################################
# Testing Function
# 테스팅 함수
# ~~~~~~~~~~~~~~~~
# 
# Finally, the central result of this tutorial comes from the ``test``
# function. Each call to this test function performs a full test step on
# the MNIST test set and reports a final accuracy. However, notice that
# this function also takes an *epsilon* input. This is because the
# ``test`` function reports the accuracy of a model that is under attack
# from an adversary with strength :math:`\epsilon`. More specifically, for
# each sample in the test set, the function computes the gradient of the
# loss w.r.t the input data (:math:`data\_grad`), creates a perturbed
# image with ``fgsm_attack`` (:math:`perturbed\_data`), then checks to see
# if the perturbed example is adversarial. In addition to testing the
# accuracy of the model, the function also saves and returns some
# successful adversarial examples to be visualized later.
# 마지막으로 본 튜토리얼의 중심 결과는 ``테스트`` 함수에서 오게 됩니다. 
# 이 테스트 기능을 호출 할 때마다 MNIST 테스트 셋에서 전체 테스트 단계를 수행하고 최종 정확도를 보고합니다.
# 그러나 이 함수에는 *엡실론* 입력도 필요합니다. 이는 ``테스트``` 함수가 :math:`\epsilon` 크기에 따라 공격자의 공격을 받는 모델의 
# 정확성을 보고하기 때문입니다. 더 구체적으로 보면 테스트 셋의 각각의 샘플에서 테스트 함수는 입력 데이터에 대한 손실 경사도 (:math:`data\_grad`) 를 계산하고, 
#  ``FGSM 공격`` (:math:`perturbed\_data`) 을 받은 작은 변화가 적용된 이미지를 만들고 나서 작은 변화가 적용된 이미지가 적대적인지 확인을 합니다. 
# 추가로 모델의 정확도를 테스트하기 위해서 테스트 함수는 나중에 시각화하여 볼 수 있도록 성공적으로 얻은 적대적 이미지를 저장하고 반환합니다.
# 

def test( model, device, test_loader, epsilon ):

    # Accuracy counter
    # 정확도 카운터
    correct = 0
    adv_examples = []

    # Loop over all examples in test set
    # 테스트 셋의 모든 예제에 대해 루프를 돕니다
    for data, target in test_loader:

        # Send the data and label to the device
        # 디바이스(CPU or GPU) 에 데이터와 라벨 값을 보냅니다
        data, target = data.to(device), target.to(device)

        # Set requires_grad attribute of tensor. Important for Attack
        # 텐서의 속성 중 requires_grad 를 설정합니다. 공격에서 중요한 부분입니다
        data.requires_grad = True

        # Forward pass the data through the model
        # 데이터를 모델에 통과시킵니다
        output = model(data)
        init_pred = output.max(1, keepdim=True)[1] # get the index of the max log-probability

        # If the initial prediction is wrong, dont bother attacking, just move on
        # 만약 초기 예측이 틀리면, 공격하지 않도록 하고 계속 진행합니다
        if init_pred.item() != target.item():
            continue

        # Calculate the loss
        # 손실을 계산합니다
        loss = F.nll_loss(output, target)

        # Zero all existing gradients
        # 모델의 경사도들을 전부 0으로 설정합니다
        model.zero_grad()

        # Calculate gradients of model in backward pass
        # 후방 전달을 통해 모델의 경사도를 계산합니다
        loss.backward()

        # Collect datagrad
        # 경사도 값을 모읍니다
        data_grad = data.grad.data

        # Call FGSM Attack
        # FGSM 공격을 호출합니다
        perturbed_data = fgsm_attack(data, epsilon, data_grad)

        # Re-classify the perturbed image
        # 작은 변화가 적용된 이미지에 대해 재분류합니다
        output = model(perturbed_data)

        # Check for success
        # 올바른지 확인합니다
        final_pred = output.max(1, keepdim=True)[1] # get the index of the max log-probability
        if final_pred.item() == target.item():
            correct += 1
            # Special case for saving 0 epsilon examples
            # 0 엡실론 예제에 대해서 저장합니다
            if (epsilon == 0) and (len(adv_examples) < 5):
                adv_ex = perturbed_data.squeeze().detach().cpu().numpy()
                adv_examples.append( (init_pred.item(), final_pred.item(), adv_ex) )
        else:
            # Save some adv examples for visualization later
            # 추후 시각화를 위하 다른 예제들을 저장합니다
            if len(adv_examples) < 5:
                adv_ex = perturbed_data.squeeze().detach().cpu().numpy()
                adv_examples.append( (init_pred.item(), final_pred.item(), adv_ex) )

    # Calculate final accuracy for this epsilon
    # 해당 엡실론에서의 최종 정확도를 계산합니다
    final_acc = correct/float(len(test_loader))
    print("Epsilon: {}\tTest Accuracy = {} / {} = {}".format(epsilon, correct, len(test_loader), final_acc))

    # Return the accuracy and an adversarial example
    # 정확도와 적대적 예제를 리턴합니다
    return final_acc, adv_examples


######################################################################
# Run Attack
# 공격 실행
# ~~~~~~~~~~
# 
# The last part of the implementation is to actually run the attack. Here,
# we run a full test step for each epsilon value in the *epsilons* input.
# For each epsilon we also save the final accuracy and some successful
# adversarial examples to be plotted in the coming sections. Notice how
# the printed accuracies decrease as the epsilon value increases. Also,
# note the :math:`\epsilon=0` case represents the original test accuracy,
# with no attack.
# 구현의 마지막 부분은 공격을 실행하는 것입니다. 여기서 전체 테스트 스텝을 각 *엡실론* 값에 실행합니다. 
# 각 엡실론마다 최종 정확도와 성공적인 일부 적대 사례를 저장하여 다음 섹션에 표시합니다. 
# 엡실론 값이 증가함에 따라 출력된 정확도가 어떻게 감소하는지 보십시오. 
# 또한, :math:`\epsilon=0` 인 경우에는 공격이 없는 원본 테스트 정확도임을 보입니다.
# 

accuracies = []
examples = []

# Run test for each epsilon
# 각 엡실론에 대해 테스트 함수를 실행합니다
for eps in epsilons:
    acc, ex = test(model, device, test_loader, eps)
    accuracies.append(acc)
    examples.append(ex)


######################################################################
# Results
# 결과
# -------
# 
# Accuracy vs Epsilon
# 정확도 vs 엡실론
# ~~~~~~~~~~~~~~~~~~~
# 
# The first result is the accuracy versus epsilon plot. As alluded to
# earlier, as epsilon increases we expect the test accuracy to decrease.
# This is because larger epsilons mean we take a larger step in the
# direction that will maximize the loss. Notice the trend in the curve is
# not linear even though the epsilon values are linearly spaced. For
# example, the accuracy at :math:`\epsilon=0.05` is only about 4% lower
# than :math:`\epsilon=0`, but the accuracy at :math:`\epsilon=0.2` is 25%
# lower than :math:`\epsilon=0.15`. Also, notice the accuracy of the model
# hits random accuracy for a 10-class classifier between
# :math:`\epsilon=0.25` and :math:`\epsilon=0.3`.
# 첫 번째 결과는 정확도 vs 엡실론 을 도식 한 것 입니다. 
# 앞서 언급했듯이 엡실론이 증가함에 따라 테스트 정확도가 떨어질 것으로 기대합니다.
# 이는 학습을 더 진행해 갈수록 엡실론이 클수록 손실을 극대화 할 방향으로 진행되기 때문입니다.
# 엡실론 값이 선형적으로 분포하더라도 곡선의 추세는 선형의 형태가 아닙니다.
# 예를 들면, math:`\epsilon=0.05` 에서의 정확도가 :math:`\epsilon=0` 보다 약 4% 낮지만
# :math:`\epsilon=0.2` 에서의 정확도는 :math:`\epsilon=0.15` 보다 약 25% 정도 낮습니다.
# 또한, :math:`\epsilon=0.25` 와 :math:`\epsilon=0.3` 사이의 모델 정확도는 랜덤으로
# 10개중 1개를 선택했을 때의 정확도와 유사한 수준입니다.

plt.figure(figsize=(5,5))
plt.plot(epsilons, accuracies, "*-")
plt.yticks(np.arange(0, 1.1, step=0.1))
plt.xticks(np.arange(0, .35, step=0.05))
plt.title("Accuracy vs Epsilon")
plt.xlabel("Epsilon")
plt.ylabel("Accuracy")
plt.show()


######################################################################
# Sample Adversarial Examples
# 샘플 적대적 예제들
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
# 
# Remember the idea of no free lunch? In this case, as epsilon increases
# the test accuracy decreases **BUT** the perturbations become more easily
# perceptible. In reality, there is a tradeoff between accuracy
# degredation and perceptibility that an attacker must consider. Here, we
# show some examples of successful adversarial examples at each epsilon
# value. Each row of the plot shows a different epsilon value. The first
# row is the :math:`\epsilon=0` examples which represent the original
# “clean” images with no perturbation. The title of each image shows the
# “original classification -> adversarial classification.” Notice, the
# perturbations start to become evident at :math:`\epsilon=0.15` and are
# quite evident at :math:`\epsilon=0.3`. However, in all cases humans are
# still capable of identifying the correct class despite the added noise.
# 공짜 점심은 없다는 것을 기억하시나요? 이 경우에는 엡실론이 증가할수록 테스트 정확도는 떨어집니다. 
# **그러나** 작은 변화는 더 쉽게 인식할 수 있게 됩니다.
# 실제로 정확도 저하와 공격자가 고려해야 하는 이해도 사이에는 상충 관계(tradeoff)가 있습니다.
# 여기서 우리는 각 엡실론 값에서 성공적인 대적 사례를 보이는 몇 가지 예를 보겠습니다.
# 아래 이미지의 첫번째로 열은 :math:`\epsilon=0` 인 예제들로 작은 변화가 없는 원본의 "깨끗한" 이미지들을 나타냅니다.
# 각 이미지의 위의 글자는 "원래 분류 결과 -> 적대적 분류 결과"를 나타냅니다.
# :math:`\epsilon=0.15` 에서 작은 변화가 눈에 띄기 시작하고 :math:`\epsilon=0.3` 에서는 확실해 보입니다.
# 그러나 모든 경우에 대해서 노이즈가 추가되었더라도 사람은 올바르게 분류를 수행할 수 있습니다.

# Plot several examples of adversarial samples at each epsilon
# 각 엡실론에서 적대적 샘플의 몇 가지 예를 도식화합니다.
cnt = 0
plt.figure(figsize=(8,10))
for i in range(len(epsilons)):
    for j in range(len(examples[i])):
        cnt += 1
        plt.subplot(len(epsilons),len(examples[0]),cnt)
        plt.xticks([], [])
        plt.yticks([], [])
        if j == 0:
            plt.ylabel("Eps: {}".format(epsilons[i]), fontsize=14)
        orig,adv,ex = examples[i][j]
        plt.title("{} -> {}".format(orig, adv))
        plt.imshow(ex, cmap="gray")
plt.tight_layout()
plt.show()


######################################################################
# Where to go next?
# 다음 단계는?
# -----------------
# 
# Hopefully this tutorial gives some insight into the topic of adversarial
# machine learning. There are many potential directions to go from here.
# This attack represents the very beginning of adversarial attack research
# and since there have been many subsequent ideas for how to attack and
# defend ML models from an adversary. In fact, at NIPS 2017 there was an
# adversarial attack and defense competition and many of the methods used
# in the competition are described in this paper: `Adversarial Attacks and
# Defences Competition <https://arxiv.org/pdf/1804.00097.pdf>`__. The work
# on defense also leads into the idea of making machine learning models
# more *robust* in general, to both naturally perturbed and adversarially
# crafted inputs.
# 이번 튜토리얼에서 적대적 머신 러닝 주제의 인사이트를 얻을 수 있었기를 바랍니다.
# 여기에서부터 더 많은 것들을 알아나갈 수 있습니다.
# 튜토리얼의 적대적 공격 예제는 본 분야의 초급 단계이며 
# 적대적 상황으로부터 ML 모델을 공격하고 방어하는 방법에 대한 많은 후속 아이디어가 있습니다.
# 사실 NIPS 2017 에서 적대적 공격과 방어에 대한 경쟁(competition)이 있었고 여기서 사용된
# 다양한 방법들은 다음 논문에 정리 되어 있습니다: `적대적 공격과 방어 경쟁 <https://arxiv.org/pdf/1804.00097.pdf>`__.
# 방어에 대한 연구는 자연스럽게 교란 및 해킹 목적으로 제작된 입력에 대해 머신 러닝 모델을
# 보다 *강건하게(robust)* 만드는 아이디어로 이어집니다.
#  
# Another direction to go is adversarial attacks and defense in different
# domains. Adversarial research is not limited to the image domain, check
# out `this <https://arxiv.org/pdf/1801.01944.pdf>`__ attack on
# speech-to-text models. But perhaps the best way to learn more about
# adversarial machine learning is to get your hands dirty. Try to
# implement a different attack from the NIPS 2017 competition, and see how
# it differs from FGSM. Then, try to defend the model from your own
# attacks.
# 또 다른 방향은 다른 도메인에서의 적의 공격과 방어입니다. 적대적 연구는 이미지 도메인에 제한되어 있지 않습니다. 
# `여기 <https://arxiv.org/pdf/1801.01944.pdf>`__ 에서 음성-텍스트 변환 모델에서의 공격도 확인할 수 있습니다.
# 그러나 적대적 머신 러닝 분야에 대해서 많은 것을 알기 위한 최고의 방법은 많이 해보는 것입니다.
# NIPS 2017 경쟁에서 소개된 다양한 공격 방법을 직접 구현해 보고, FGSM 과 어떤 점이 다른지 연구해 보세요.
# 그리고 나서 직접 만든 공격에서부터 모델을 방어해 보세요.
# 

