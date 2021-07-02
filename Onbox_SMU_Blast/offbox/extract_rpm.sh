#!/bin/bash


rpm_path=$(realpath $1)
dir=$(dirname $rpm_path)
ex_dir=$2
cd $dir
#ex_dir='extracted_rpm_564332'
rm -rf $ex_dir
mkdir $ex_dir
cp $rpm_path $ex_dir
cd $ex_dir
rpm2cpio $(basename $rpm_path) | cpio -imdv
