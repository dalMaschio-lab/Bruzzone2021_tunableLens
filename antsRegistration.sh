#!/bin/bash -l

export OMP_NUM_THREADS=72
export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=72
# For pinning threads correctly:
export OMP_PLACES=cores

input=$1
template=$2

output="exp_aligned2atlas.nrrd"
outtr_prefx="exp2liveatlas_"

# Run the program:
antsRegistration -d 3 \
--float 1 \
--verbose 1 \
-o \[${outtr_prefx},${output}\] \
--interpolation WelchWindowedSinc \
--winsorize-image-intensities \[0.005,0.995\] \
--use-histogram-matching 0 \
-r \[${template},${input},1\] \
-t rigid\[0.1\] \
-m MI\[${template},${input},1,32,Regular,0.25\] \
-c \[200x200x200x0,1e-8,10\] \
--shrink-factors 12x8x4x2 \
--smoothing-sigmas 4x3x2x1vox \
-t Affine\[0.1\] \
-m MI\[${template},${input},1,32,Regular,0.25\] \
-c \[200x200x200x0,1e-8,10\] \
--shrink-factors 12x8x4x2 \
--smoothing-sigmas 4x3x2x1 \
-t SyN\[0.05,6,0.5\] \
-m CC\[${template},${input},1,2\] \
-c \[200x200x200x200x10,1e-7,10\] \
--shrink-factors 12x8x4x2x1 \
--smoothing-sigmas 4x3x2x1x0 | tee "align.log"