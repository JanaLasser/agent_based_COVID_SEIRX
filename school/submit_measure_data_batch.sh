N_runs=300
measure_step=64
school_type=primary

for school_layout_start_index in $(seq 0 14)
   do
   school_layout_end_index=`echo $school_layout_start_index+1 | bc`
   
   for measure_start_index in $(seq 0 $measure_step 127)
      do
      measure_end_index=`echo $measure_start_index+$measure_step | bc`

      python3 run_data_creation.py $school_type $N_runs $school_layout_start_index $school_layout_end_index $measure_start_index $measure_end_index &

   done

done