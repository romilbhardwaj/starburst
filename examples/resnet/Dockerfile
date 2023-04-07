FROM tensorflow/tensorflow:nightly
SHELL ["/bin/bash", "-c"]

RUN apt-get update 
RUN apt-get install -y python3
RUN apt-get install -y git
RUN apt-get install -y wget

RUN mkdir app
WORKDIR /app
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-py39_23.1.0-1-Linux-x86_64.sh -O miniconda.sh
RUN /bin/bash miniconda.sh -b -p /opt/conda
ENV PATH="${PATH}:/opt/conda/bin"

RUN git clone https://github.com/concretevitamin/tpu.git /app/tpu
WORKDIR /app/tpu
RUN git checkout 9459fee

RUN conda create -n resnet python=3.7
RUN echo "conda activate resnet" >> ~/.bashrc
RUN . ~/.bashrc
WORKDIR /app/tpu/models
SHELL ["conda", "run", "-n", "resnet", "/bin/bash", "-c"]
RUN conda install -c conda-forge cudatoolkit=11.2.2 cudnn=8.1.0 -y && \
conda install -c nvidia cuda-nvcc -y && \
pip install tensorflow==2.4.0 pyyaml && \
pip install protobuf==3.20 && \
pip install -e .

RUN mkdir /usr/local/cuda-11.0
RUN mkdir /usr/local/cuda-11.0/nvvm
RUN cp -r /opt/conda/pkgs/cuda-nvcc-12.0.140-0/nvvm/* /usr/local/cuda-11.0/nvvm

ENV LD_LIBRARY_PATH /opt/conda/envs/resnet/lib/
WORKDIR $LD_LIBRARY_PATH
RUN ln libcusolver.so.11 libcusolver.so.10

WORKDIR /app/tpu/
ENV PYTHONPATH $PYTHONPATH:models
ENV LD_LIBRARY_PATH $LD_LIBRARY_PATH:$CONDA_PREFIX/lib/
ENV XLA_FLAGS '--xla_gpu_cuda_data_dir=/usr/local/cuda-11.0'
ENV NVIDIA_VISIBLE_DEVICES all
ENV NVIDIA_DRIVER_CAPABILITIES compute,utility