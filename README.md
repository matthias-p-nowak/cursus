# cursus
program to coordinate startups of distributed software

## Background

The startup of a complex computer system requires the components to be started in a certain order.
The philosophy not yet implemented everywhere is that components should discover the availability of resources and delay their own startup until the resources are available.
Even in high availability systems there might be an elected leader, which needs to be started first.

Scripting the startup of such a system requires support, which is not available from Element Managers.

## Function
