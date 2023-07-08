Command Reference
=================

List of released CLI commands available in openstack client. These commands
can be referenced by executing ``openstack help share``.

======
shares
======

.. autoprogram-cliff:: openstack.share.v2
    :command: share create

.. autoprogram-cliff:: openstack.share.v2
    :command: share list

.. autoprogram-cliff:: openstack.share.v2
    :command: share show

.. autoprogram-cliff:: openstack.share.v2
    :command: share delete

.. autoprogram-cliff:: openstack.share.v2
    :command: share set

.. autoprogram-cliff:: openstack.share.v2
    :command: share unset

.. autoprogram-cliff:: openstack.share.v2
    :command: share properties show

.. autoprogram-cliff:: openstack.share.v2
    :command: share resize

.. autoprogram-cliff:: openstack.share.v2
    :command: share adopt

.. autoprogram-cliff:: openstack.share.v2
    :command: share abandon

.. autoprogram-cliff:: openstack.share.v2
    :command: share export location show

.. autoprogram-cliff:: openstack.share.v2
    :command: share export location list

.. autoprogram-cliff:: openstack.share.v2
    :command: share revert

.. autoprogram-cliff:: openstack.share.v2
    :command: share restore

===============
share instances
===============

.. autoprogram-cliff:: openstack.share.v2
    :command: share instance [!e]*

==================
share access rules
==================

.. autoprogram-cliff:: openstack.share.v2
    :command: share access *

===============
share migration
===============

.. autoprogram-cliff:: openstack.share.v2
    :command: share migration start

.. autoprogram-cliff:: openstack.share.v2
    :command: share migration cancel

.. autoprogram-cliff:: openstack.share.v2
    :command: share migration complete

.. autoprogram-cliff:: openstack.share.v2
    :command: share migration show

==============
share networks
==============

.. autoprogram-cliff:: openstack.share.v2
    :command: share network [!s]*

.. autoprogram-cliff:: openstack.share.v2
    :command: share network show

.. autoprogram-cliff:: openstack.share.v2
    :command: share network set

=====================
share network subnets
=====================

.. autoprogram-cliff:: openstack.share.v2
    :command: share network subnet *

===========
share types
===========

.. autoprogram-cliff:: openstack.share.v2
    :command: share type *

============
share quotas
============

.. autoprogram-cliff:: openstack.share.v2
    :command: share quota *

===============
share snapshots
===============

.. autoprogram-cliff:: openstack.share.v2
    :command: share snapshot [!i]*

========================
share snapshot instances
========================

.. autoprogram-cliff:: openstack.share.v2
    :command: share snapshot instance *

===============
user messages
===============

.. autoprogram-cliff:: openstack.share.v2
    :command: share message *

==============
share replicas
==============

.. autoprogram-cliff:: openstack.share.v2
    :command: share replica *

========================
share availability zones
========================

.. autoprogram-cliff:: openstack.share.v2
    :command: share availability zone list

==============
share services
==============

.. autoprogram-cliff:: openstack.share.v2
    :command: share service *

=======================
share security services
=======================

.. autoprogram-cliff:: openstack.share.v2
    :command: share security service *

===========
share pools
===========

.. autoprogram-cliff:: openstack.share.v2
    :command: share pool list

============
share limits
============

.. autoprogram-cliff:: openstack.share.v2
    :command: share limits *

==============================
share instance export location
==============================

.. autoprogram-cliff:: openstack.share.v2
    :command: share instance export location *

============
share groups
============

.. autoprogram-cliff:: openstack.share.v2
    :command: share group [!ts]*

.. autoprogram-cliff:: openstack.share.v2
    :command: share group set

=================
share group types
=================

.. autoprogram-cliff:: openstack.share.v2
    :command: share group type *

=====================
share group snapshots
=====================

  .. autoprogram-cliff:: openstack.share.v2
      :command: share group snapshot *

==============
share servers
==============

.. autoprogram-cliff:: openstack.share.v2
    :command: share server *

==============
resource locks
==============

.. autoprogram-cliff:: openstack.share.v2
    :command: share lock *
