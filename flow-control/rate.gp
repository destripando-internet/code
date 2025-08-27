set datafile separator ","
set terminal pngcairo size 1280,720 enhanced font 'Arial,16'
set output "rate.png"

set xlabel "time (s)"
set ylabel "rate (kB/s)"
set yrange [0:1400]
unset key
plot "stats.csv" using 1:3 with lines lw 3 title "data"
