#!/bin/bash

giso=$( realpath $1 )
workspace=$( realpath $2 )
#iso_extractor=$( realpath $3 )
is_optimzed=true
giso_name=$( basename $giso )
IFS='-' read -ra ADDR <<< "$giso_name"
platform="${ADDR[0]}"

pd=$(pwd)
#echo "$giso, $workspace, $req_root_fs"

giso_path="$workspace/giso"
mkdir $giso_path

./extract_iso.sh $giso $giso_path

lv1_initrd="$giso_path/boot/initrd.img"
lv1_initrd_path="$workspace/initrd_lv_1"

mkdir -p  $lv1_initrd_path
cd $lv1_initrd_path

echo "Extracting: initrd.img ..."

zcat $lv1_initrd | cpio -imdv

if [ $? -eq 1 ]; 
then
	cpio -imdv < $lv1_initrd
	is_optimized=false
fi
echo "Extracted: initrd.img"

calv_xr_iso=$lv1_initrd_path

#echo $is_optimized

sys_img="$lv1_initrd_path/iso/system_image.iso"

if [ -f "$sys_img" ];
then
	sys_img_path="$workspace/sys_img"
	mkdir $sys_img_path
	cd $pd
	./extract_iso.sh $sys_img $sys_img_path
	lv2_initrd="$sys_img_path/boot/initrd.img"
	lv2_initrd_path="$workspace/initrd_lv_2"
	mkdir $lv2_initrd_path
	cd $lv2_initrd_path
	echo "Extracting: initrd.img ..."
	zcat $lv2_initrd | cpio -imdv
	echo "Extracted: initrd.img"
	cd $pd
	calv_xr_iso=$lv2_initrd_path
	
fi

#echo $calv_xr_iso

sysadmin_iso="$calv_xr_iso/iso/$platform-sysadmin.iso"
xr_iso="$calv_xr_iso/iso/$platform-xr.iso"
initrd_nbi="$calv_xr_iso/nbi-initrd/$platform-sysadmin-nbi-initrd.img"

sysadmin_rpms="$calv_xr_iso/calvados_rpms/*"
xr_rpms="$calv_xr_iso/xr_rpms/*"

if [ "$is_optimized" = false ];
then
	sysadmin_rpms="$giso_path/calvados_rpms/*"
	xr_rpms="$giso_path/xr_rpms/*"
fi

sysadmin_iso_path="$workspace/sysadmin_iso"
xr_iso_path="$workspace/xr_iso"

if [ -f "$initrd_nbi" ];
then
	initrd_nbi_path="$workspace/initrd_nbi"
	mkdir $initrd_nbi_path
	cd $initrd_nbi_path
	echo "Extracting: $platform-sysadmin-nbi-initrd.img ..."
	zcat $initrd_nbi | cpio -imdv
	echo "Extracted: $platform-sysadmin-nbi-initrd.img"
	cd $pd
	nbi_root_fs="$workspace/nbi_root_fs/RPM"
	mkdir -p $nbi_root_fs
	nbi_rpms="$initrd_nbi_path/rpm/*"
	cp $nbi_rpms $nbi_root_fs
	for rpm in $sysadmin_rpms;
	do
		if [[ "$rpm" == *".arm."* ]]; then
			mv $rpm $nbi_root_fs
		fi
	done
fi

mkdir $sysadmin_iso_path
mkdir $xr_iso_path

cd $pd

./extract_iso.sh $sysadmin_iso $sysadmin_iso_path
./extract_iso.sh $xr_iso $xr_iso_path

sysadmin_root_fs="$workspace/sysadmin_root_fs/RPM"
xr_root_fs="$workspace/xr_root_fs/RPM"
sysadmin_base_rpms="$sysadmin_iso_path/rpm/calvados/*"
xr_base_rpms="$xr_iso_path/rpm/xr/*"

mkdir -p $sysadmin_root_fs
mkdir -p $xr_root_fs

cp -r $sysadmin_base_rpms $sysadmin_root_fs
cp -r $sysadmin_rpms $sysadmin_root_fs
cp -r $xr_base_rpms $xr_root_fs
cp -r $xr_rpms $xr_root_fs

: '
echo "Preparing for sysadmin RPM extraction ..."
sysadmin_r="$sysadmin_root_fs/*.rpm"
cd "$workspace/sysadmin_root_fs"
for r in $sysadmin_r
do
	echo "Extracting: $(basename $r) ..."
	rpm2cpio $r | cpio -imdv 2>/dev/null
done
echo "Preparing for xr RPM extraction ..."
xr_r="$xr_root_fs/*.rpm"
cd "$workspace/xr_root_fs"
for r in $xr_r
do
	echo "Extracting: $(basename $r) ..."
	rpm2cpio $r | cpio -imdv 2>/dev/null	
done
'
echo " "
