# SMU Blast Radius Calculator (On the Box)
## Description
This product serves as a utility tool for Cisco customers for checking whether a SMU update can be carried out and what will be the impact of such a change on the state of the device. It aims to generate a list of what programs are going to be affected and how it is going to impact the network as processes and protocols may need restarting.  

This is a utility tool that consists of two parts:  
	1. On the box program to collect process map data from the router. The  folder [onbox](https://github.com/skewat/exrgiso/tree/master/Onbox_SMU_Blast/onbox) contains instructions on how to use it.  
	2. Once the data is collected from the box the user is required to feed the data to a off the box utility that processes the process maps to calculate the SMU Blast radius. The folder [offbox](https://github.com/skewat/exrgiso/tree/master/Onbox_SMU_Blast/offbox) contains instructions on how to use it.  

## Example
### On the Box

### Of the Box
```bash
-bash-4.2$ python3 main_2.py -m ../SMU_blast_radius_17-06-2021-14-05-14.tar.gz --smu ../ncs5500-7.5.1.08I.CSCxr22222.tar
Extracting SMU and Gathering data. It may take several minutes ...


                                                                                                        XR



Number of affected programs in RP: 3
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
sdr_invmgr                         invmgr_proxy                       udp
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


Number of affected programs in LC: 1
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
sdr_invmgr
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

```


