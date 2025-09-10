#!/bin/bash

export OMP_NUM_THREADS=1

mpirun -np 32 pw.x  -in  test_direct.pwi  >  test_direct.pwo
