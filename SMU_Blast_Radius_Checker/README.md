# SMU Blast Radius Calculator
## Description:

This product serves as a utility tool for Cisco customers for checking whether an RPM package or shared library of the IOS can be replaced and what will be the impact of such a change on the state of the device. It aims to generate statistical analysis of what programs are going to be affected and how it is going to impact the network as routing tables and protocols may need restarting.
## Usage    
```bash
usage: main_2.py [-h] --iso ISO --smu SMU [SMU ...] [--independent]

Calculate SMU Blast Radius

optional arguments:
  -h, --help            show this help message and exit
  --iso ISO, -i ISO     path/to/iso
  --smu SMU [SMU ...], -s SMU [SMU ...]
                        path/to/smu
  --independent, -I     Consider SMUs independently
```
### Parameters:
```[--iso / -i]:``` This marks the path to the golden ISO.  
```[--smu/ -s]:``` This marks the path(s) to one or multiple SMUs. A minimum of one SMU is mandatory.  
```[-h]:``` Shows help menu.  
```[--independent/ -I]:``` If multiple SMUs are passed as parameter, it is assumed that the operator will try to install all at once. This option is used to instruct the program to consider all the SMUs independently. It has the same effect as installing the SMUs one by one.  

### Examples:
```bash
-bash-4.2$ ./main_2.py --iso ncs5500-goldenk9-x-6.6.3-tej.iso --smu test_SMUs/ncs5500-6.6.3.CSCvu83624.tar

Extracting ncs5500-6.6.3.CSCvu83624.tar...
ncs5500-6.6.3.CSCvu83624.txt
ncs5500-mgbl-3.0.0.1-r663.CSCvu83624.x86_64.rpm

Checking for reload SMU: ncs5500-mgbl-3.0.0.1-r663.CSCvu83624.x86_64.rpm ---- Not a reload SMU.
Analyzing: ncs5500-mgbl-3.0.0.1-r663.CSCvu83624.x86_64.rpm
Extracting: ncs5500-goldenk9-x-6.6.3-tej.iso...
Extracted: ncs5500-goldenk9-x-6.6.3-tej.iso
Extracting: initrd.img ...
Extracted: initrd.img
Extracting: system_image.iso...
Extracted: system_image.iso
Extracting: initrd.img ...
Extracted: initrd.img
Extracting: ncs5500-sysadmin-nbi-initrd.img ...
Extracted: ncs5500-sysadmin-nbi-initrd.img
Extracting: ncs5500-sysadmin.iso...
Extracted: ncs5500-sysadmin.iso
Extracting: ncs5500-xr.iso...
Extracted: ncs5500-xr.iso

Analyzing: ncs5500-common-pd-fib-2.0.0.0-r663.x86_64.rpm
Analyzing: ncs5500-cai-2.0.0.0-r663.x86_64.rpm
Analyzing: ncs5500-ce-2.0.0.0-r663.x86_64.rpm
Analyzing: ncs5500-fwding-3.0.0.0-r663.x86_64.rpm
Analyzing: ncs5500-bgp-2.0.0.0-r663.x86_64.rpm
Analyzing: ncs5500-dpa-fwding-4.1.0.0-r663.x86_64.rpm
Analyzing: ncs5500-dpa-4.0.0.0-r663.x86_64.rpm
Analyzing: ncs5500-package_version_lock-1.0.0.0-r663.x86_64.rpm
Analyzing: ncs5500-infra-6.0.0.0-r663.x86_64.rpm
Analyzing: ncs5500-parser-3.0.0.0-r663.x86_64.rpm
Analyzing: ncs5500-ncs-base-3.0.0.0-r663.x86_64.rpm
Analyzing: ncs5500-routing-4.0.0.0-r663.x86_64.rpm
Analyzing: ncs5500-spirit-boot-2.0.0.0-r663.x86_64.rpm
Analyzing: ncs5500-eigrp-1.0.0.0-r663.x86_64.rpm
Analyzing: ncs5500-isis-2.2.0.0-r663.x86_64.rpm
Analyzing: ncs5500-li-1.0.0.0-r663.x86_64.rpm
Analyzing: ncs5500-os-7.0.0.0-r663.x86_64.rpm
Analyzing: ncs5500-k9sec-3.1.0.0-r663.x86_64.rpm
Analyzing: ncs5500-mpls-2.1.0.0-r663.x86_64.rpm
Analyzing: ncs5500-routing-4.0.0.1-r663.CSCvt31267.x86_64.rpm
Analyzing: ncs5500-mcast-3.1.0.0-r663.x86_64.rpm
Analyzing: ncs5500-ospf-2.0.0.0-r663.x86_64.rpm
Analyzing: ncs5500-mpls-te-rsvp-4.1.0.0-r663.x86_64.rpm
Analyzing: ncs5500-mgbl-3.0.0.0-r663.x86_64.rpm
Analyzing: ncs5500-iosxr-fwding-6.0.0.0-r663.x86_64.rpm
Analyzing: ncs5500-os-support-4.1.0.0-r663.x86_64.rpm




                                                            XR

Number of affected programs in rp: 2
---------------------------------------------------------------------------------------------------------
emsd                               netconf
---------------------------------------------------------------------------------------------------------
Detailed output in: 'output.txt'        log file: 'debug.log'
```

