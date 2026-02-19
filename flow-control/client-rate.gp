set datafile separator ","
set terminal pngcairo size 1280,720 enhanced font 'Arial,16'
set output "client-rate.png"

set logscale y
set xlabel "time (s)"
set ylabel "rate (kB/s)"
# set yrange [0:1400]
unset key
plot "client-stats.csv" using 1:($3/1000) with lines lw 3 title "data"
