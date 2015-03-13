FROM ubuntu:14.04

RUN apt-get -qq update && apt-get install --no-install-recommends -y apt-transport-https  software-properties-common && \
    apt-add-repository -y ppa:ansible/ansible && \
    apt-get -qq update && \
    apt-get -qq install ansible && \
    apt-get purge -y software-properties-common

RUN mkdir /tmp/ansible
WORKDIR /tmp/ansible
ADD local.yml /tmp/ansible/local.yml
ADD defaults /tmp/ansible/defaults
ADD tasks /tmp/ansible/tasks
RUN ansible-playbook -i localhost, local.yml -e "@defaults/main.yml"
