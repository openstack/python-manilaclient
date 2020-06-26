populate-manilaclient-config
============================

An ansible role to use devstack's helper scripts and create a configuration
file for running python-manilaclient's functional tests.

Role Variables
--------------

.. zuul:rolevar:: base_dir
     :type: string
     :default: /opt/stack

   The base directory for the installation. The devstack folder is expected
   to be found in this location


.. zuul:rolevar:: manilaclient_config
     :type: string
     :default: "{{ zuul.project.src_dir }}/etc/manilaclient/manilaclient.conf"

   The location of the manilaclient test configuration file.


.. zuul:rolevar:: neutron_network_name
     :type: string
     :default: private

   A pre-created neutron network that the tests can use. This network must
   be accessible to the "demo" and "admin" users within the "demo" project.


.. zuul:rolevar:: neutron_subnet_name
     :type: string
     :default: private-subnet

   A pre-created neutron subnet that the tests can use. This network must
   be accessible to the "demo" and "admin" users within the "demo" project.


.. zuul:rolevar:: share_network_name
     :type: string
     :default: ci

   The name to give the share network created by this role, and configured
   for use by the tests.
