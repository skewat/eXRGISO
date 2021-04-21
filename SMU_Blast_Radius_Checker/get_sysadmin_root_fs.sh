#!/bin/bash


iso_path=$1
work_dir=$2
pd=$(pwd)
echo "Generating root file system ..."
echo "This will take a minute ..."
giso_mount="$work_dir/mnt_giso"
#echo $giso_mount
mkdir $giso_mount
./extract_iso.sh $iso_path $giso_mount
initrd_lv_1="$work_dir/initrd_lv_1"
mkdir $initrd_lv_1
cd $initrd_lv_1
initrd_lv_1_boot="$giso_mount/boot/initrd.img"
echo "Extracting: $(basename $initrd_lv_1_boot) ..."
cpio -imdv < $initrd_lv_1_boot
echo "Extracted: $(basename $initrd_lv_1_boot)"
cd $pd
#rm -rf $giso_mount
sys_img_iso="$initrd_lv_1/iso/system_image.iso"
sys_img="$work_dir/mnt_sys_img"
mkdir $sys_img
./extract_iso.sh $sys_img_iso $sys_img

initrd_lv_2="$work_dir/initrd_lv_2"
initrd_lv_2_boot="$sys_img/boot/initrd.img"
mkdir $initrd_lv_2
cd $initrd_lv_2
echo "Extracting: $(basename $initrd_lv_2_boot) ..."
zcat $initrd_lv_2_boot | cpio -imdv
echo "Extracted: $(basename $initrd_lv_2_boot)"
cd $pd
rm -rf $sys_img
rm -rf $initrd_lv_1

xr_iso="$initrd_lv_2/iso/ncs5500-sysadmin.iso"
xr_iso_mnt_pt="$work_dir/mnt_sysadmin_iso"
mkdir $xr_iso_mnt_pt
./extract_iso.sh $xr_iso $xr_iso_mnt_pt

rpm="$xr_iso_mnt_pt/rpm"
cp -r $rpm $work_dir
root_fs="$work_dir/sysadmin_root_fs"
root_iso="$xr_iso_mnt_pt/boot/initrd.img"
mkdir $root_fs
cd $root_fs
#zcat $root_iso | cpio -imdv
rm -rf $xr_iso_mnt_pt
rm -rf $initrd_lv_2
cd $pd
rpm="$work_dir/rpm"
rpm2="$giso_mount/calvados_rpms"
mv $rpm $root_fs
mv $rpm2 $root_fs
rm -rf $giso_mount
echo "Preparing RPM extraction"
#chroot $root_fs rpm -iv --nodeps /rpm/xr/*.rpm
rpm="$root_fs/rpm/calvados/*.rpm"
rpm2="$root_fs/calvados_rpms/*.rpm"
RPM="$root_fs/RPM"
mkdir $RPM
cd $root_fs
for r in $rpm
do
	echo "Extracting: $(basename $r) ..."
        rpm2cpio $r | cpio -imdv
	cp $r $RPM
done
for r in $rpm2
do
	echo "Extracting: $(basename $r) ..."
	rpm2cpio $r | cpio -imdv
	cp $r $RPM
done
