# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  # TODO: update to xenial64 when that comes out
  config.vm.box = "ubuntu/trusty64"

  # On startup, run our bootstrap script to setup the VM
  config.vm.provision :shell, :path => "vagrant_bootstrap.sh"

  config.vm.provider "virtualbox" do |v|
    # MAGIC for faster guest networking
    v.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
    v.customize ["modifyvm", :id, "--natdnsproxy1", "on"]
    v.customize ["modifyvm", :id, "--nictype1", "virtio"]

    # We need quite a bit of memory to compile more than one ycmd C++ file at a
    # time.
    v.memory = 3072
    v.cpus = 2
  end

  config.vm.provider "parallels" do |v|
    config.vm.box = 'parallels/ubuntu-14.04'

    v.memory = 3072
    v.cpus = 4

    v.linked_clone = true
    v.update_guest_tools = true
  end
end
