set datafile separator ","
set terminal pngcairo size 1280,720 enhanced font 'Arial,16'
set output "rate.png"

set xlabel "time (s)"
set ylabel "rate (B/s)"
set logscale y
set key top right

plot "stats.csv" using 1:2 with lines lw 3 title "SMA", \
     "stats.csv" using 1:3 with lines lw 3 title "EMA"
